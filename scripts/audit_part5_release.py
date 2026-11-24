from pathlib import Path
from datetime import datetime
from collections import Counter
from importlib import metadata
import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument(
    "--run-10x",
    action="store_true",
    help="Run 10x only on a machine with enough free RAM"
)
args = parser.parse_args()

ROOT = Path.cwd()
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
OUT = ROOT / "logs" / "part5_final" / STAMP
OUT.mkdir(parents=True, exist_ok=False)

EVIDENCE = (
    ROOT / "docs/evidence/part5_integrity_status.json"
)

RESULTS = []

def audit(name, status, detail=""):
    RESULTS.append({
        "check": name,
        "status": status,
        "details": str(detail)
    })
    print(f"[{status}] {name}: {detail}", flush=True)

def read_csv(path):
    with path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as f:
        return list(csv.DictReader(f))

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(
            lambda: f.read(1024 * 1024), b""
        ):
            h.update(block)
    return h.hexdigest()

def command(args, env=None):
    return subprocess.run(
        args,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

def quarter(value):
    text = str(value).upper()
    text = text.replace(" ", "")
    text = text.replace("-", "")
    text = text.replace("_", "")
    m = re.search(
        r"(19\d{2}|20\d{2})Q([1-4])",
        text
    )
    return (
        f"{m.group(1)}Q{m.group(2)}"
        if m else None
    )

print("=== PART 5: FDIC FINAL INTEGRITY AUDIT ===")

print("\n=== 1. STAGE 1 ENVIRONMENT ===")

python = Path(sys.executable).resolve()

if ".venv311" not in str(python).lower():
    raise RuntimeError(
        "Use the verified .venv311 Python"
    )

env = os.environ.copy()
env["PYSPARK_PYTHON"] = str(python)
env["PYSPARK_DRIVER_PYTHON"] = str(python)
env["PYTHONPATH"] = (
    str(ROOT / "src")
    + os.pathsep
    + str(ROOT)
)
env["PYTHONUTF8"] = "1"
env["PYTHONIOENCODING"] = "utf-8"
env["SPARK_LOCAL_IP"] = "127.0.0.1"
env["SPARK_LOCAL_HOSTNAME"] = "localhost"

preflight = ROOT / "scripts/stage1_preflight.py"

if preflight.is_file():
    p = command(
        [str(python), str(preflight)], env=env
    )
    output = p.stdout + "\n" + p.stderr
    (OUT / "stage1_preflight.log").write_text(
        output, encoding="utf-8"
    )

    passed = (
        p.returncode == 0
        and "SUMMARY: PASS" in p.stdout
    )

    audit(
        "Stage1 preflight",
        "PASS" if passed else "FAIL",
        f"exit={p.returncode}"
    )
else:
    audit(
        "Stage1 preflight",
        "FAIL", "Script missing"
    )

print("\n=== 2. CHECK 170 QUARTERS ===")

manifest = (
    ROOT /
    "artifacts/stageB/audit/manifest_verification.csv"
)

if not manifest.is_file():
    raise FileNotFoundError(manifest)

rows = read_csv(manifest)

expected_quarters = [
    f"{year}Q{q}"
    for year in range(1984, 2027)
    for q in range(1, 5)
    if year < 2026 or q <= 2
]

observed = [
    quarter(r.get("quarter", ""))
    for r in rows
]

continuous = (
    len(rows) == 170
    and len(set(observed)) == 170
    and set(observed) == set(expected_quarters)
)

audit(
    "170 continuous quarters",
    "PASS" if continuous else "FAIL",
    f"rows={len(rows)}, unique={len(set(observed))}"
)

truth = {"1", "true", "yes", "pass", "ok"}
flags_pass = True

for field in (
    "file_exists", "complete", "sha_match"
):
    failed = [
        r.get("quarter")
        for r in rows
        if str(r.get(field, "")).strip().lower()
        not in truth
    ]

    if failed:
        flags_pass = False

    audit(
        "Saved manifest flag: " + field,
        "PASS" if not failed else "FAIL",
        f"not_true={len(failed)}, examples={failed[:5]}"
    )

counts = []

for r in rows:
    value = str(
        r.get("rows_manifest", "")
    ).replace(",", "")

    try:
        counts.append(int(float(value)))
    except (ValueError, TypeError):
        pass

raw_total = (
    sum(counts) if len(counts) == 170
    else None
)

audit(
    "Raw financial rows in manifest",
    "PASS" if raw_total == 1682738 else "WARN",
    f"count={raw_total}; expected=1682738"
)

print("\n=== 3. RECOMPUTE ORIGINAL SHA-256 ===")

raw_root = ROOT / "data_raw/fdic"

pattern = re.compile(
    r"(19\d{2}|20\d{2})[ _-]?[Qq]([1-4])"
)

quarter_files = {
    q: [] for q in expected_quarters
}

if raw_root.is_dir():
    for f in raw_root.rglob("*"):
        if not f.is_file():
            continue

        if not f.name.lower().endswith(
            (".csv", ".parquet", ".zip", ".gz")
        ):
            continue

        if any(
            x in f.name.lower()
            for x in ("manifest", "checksum")
        ):
            continue

        m = pattern.search(f.name)

        if m:
            q = f"{m.group(1)}Q{m.group(2)}"

            if q in quarter_files:
                quarter_files[q].append(f)

# Search for a stored reference SHA-256 manifest.
# The saved sha_match flag alone is not an
# independent checksum reference.
reference = {}
reference_sources = []

for base in (
    raw_root,
    ROOT / "artifacts/stageB/audit"
):
    if not base.is_dir():
        continue

    for f in base.rglob("*"):
        if not f.is_file():
            continue

        if f.suffix.lower() != ".csv":
            continue

        if not any(
            x in f.name.lower()
            for x in ("manifest", "checksum", "sha")
        ):
            continue

        if f.stat().st_size > 20 * 1024 * 1024:
            continue

        try:
            data = read_csv(f)
        except Exception:
            continue

        if not data:
            continue

        names = {
            x.lower(): x for x in data[0]
        }

        hash_col = next(
            (
                names[x]
                for x in (
                    "expected_sha256",
                    "sha256",
                    "checksum_sha256",
                    "sha256_expected"
                )
                if x in names
            ),
            None
        )

        quarter_col = next(
            (
                names[x]
                for x in (
                    "quarter",
                    "report_quarter",
                    "period"
                )
                if x in names
            ),
            None
        )

        if not hash_col or not quarter_col:
            continue

        valid = 0

        for r in data:
            q = quarter(r.get(quarter_col, ""))
            h = str(
                r.get(hash_col, "")
            ).strip().lower()

            if not q:
                continue

            if not re.fullmatch(
                r"[0-9a-f]{64}", h
            ):
                continue

            if q in reference and reference[q] != h:
                reference[q] = None
            else:
                reference[q] = h

            valid += 1

        if valid:
            reference_sources.append(
                str(f.relative_to(ROOT))
            )

audit(
    "Reference SHA-256 manifests",
    (
        "PASS"
        if len(reference) == 170
        and all(reference.values())
        else "WARN"
    ),
    f"reference quarters={sum(bool(x) for x in reference.values())}; "
    f"sources={reference_sources}"
)

hash_rows = []
computed = 0

for q in expected_quarters:
    candidates = quarter_files[q]

    # Never guess when several source files
    # could represent the same quarter.
    source = (
        candidates[0]
        if len(candidates) == 1 else None
    )

    calculated = (
        sha256(source) if source else None
    )

    expected = reference.get(q)

    matched = (
        calculated == expected
        if calculated and expected
        else None
    )

    if calculated:
        computed += 1

    hash_rows.append({
        "quarter": q,
        "candidate_count": len(candidates),
        "file": (
            str(source.relative_to(ROOT))
            if source else ""
        ),
        "recomputed_sha256": calculated or "",
        "reference_sha256": expected or "",
        "match": (
            matched
            if matched is not None
            else "NOT_VERIFIABLE"
        )
    })

hash_csv = OUT / "quarter_file_sha256_audit.csv"

with hash_csv.open(
    "w", newline="", encoding="utf-8-sig"
) as f:
    writer = csv.DictWriter(
        f, fieldnames=list(hash_rows[0])
    )
    writer.writeheader()
    writer.writerows(hash_rows)

matches = sum(
    x["match"] is True
    for x in hash_rows
)

sha_verified = matches == 170

sha_status = (
    "VERIFIED_170_OF_170"
    if sha_verified
    else "NOT_INDEPENDENTLY_VERIFIED"
)

audit(
    "Independent 170-file SHA-256 audit",
    "PASS" if sha_verified else "WARN",
    f"{sha_status}; recomputed={computed}/170; "
    f"reference matches={matches}/170"
)

if computed < 170:
    examples = [
        (q, len(quarter_files[q]))
        for q in expected_quarters
        if len(quarter_files[q]) != 1
    ]
    print(
        "Missing/ambiguous source examples:",
        examples[:12]
    )

print("\n=== 4. NUMERIC EQUIVALENCE ===")

stage_c = ROOT / "artifacts/stageC"

equivalence_files = (
    sorted(stage_c.rglob("numeric_equivalence.json"))
    if stage_c.is_dir() else []
)

equivalence = []

for f in equivalence_files:
    try:
        obj = json.loads(
            f.read_text(encoding="utf-8-sig")
        )
        status = str(
            obj.get("status", "UNKNOWN")
        )
    except Exception as exc:
        status = "ERROR: " + repr(exc)

    equivalence.append({
        "file": str(f.relative_to(ROOT)),
        "status": status
    })

audit(
    "Saved numeric equivalence evidence",
    (
        "PASS"
        if equivalence
        and all(
            x["status"].upper() == "PASS"
            for x in equivalence
        )
        else "WARN"
    ),
    equivalence
)

print("\n=== 5. BENCHMARK COVERAGE ===")

benchmark = (
    ROOT / "artifacts/stageC/final/benchmark_runs.csv"
)

runs = (
    read_csv(benchmark)
    if benchmark.is_file() else []
)

columns = set(runs[0]) if runs else set()

scale_col = next(
    (
        x for x in (
            "scale", "scale_factor", "scale_x"
        ) if x in columns
    ),
    None
)

engine_col = next(
    (
        x for x in (
            "engine", "engine_name", "framework"
        ) if x in columns
    ),
    None
)

cells = Counter()

if scale_col and engine_col:
    for r in runs:
        scale = str(
            r[scale_col]
        ).replace("x", "").replace("X", "").strip()

        try:
            scale = str(int(float(scale)))
        except ValueError:
            pass

        engine = str(
            r[engine_col]
        ).strip().lower()

        cells[(engine, scale)] += 1

engines = {
    engine for engine, scale in cells
}

coverage = (
    len(runs) == 27
    and len(engines) == 3
    and {scale for engine, scale in cells}
        == {"1", "2", "5"}
    and len(cells) == 9
    and all(n == 3 for n in cells.values())
)

audit(
    "Benchmark 3 engines x 3 scales x 3 repeats",
    "PASS" if coverage else "WARN",
    f"rows={len(runs)}, cells={dict(cells)}"
)

print("\n=== 6. SAFE 10X RESOURCE CHECK ===")

try:
    import psutil
    import shutil

    memory = psutil.virtual_memory()

    total_ram = memory.total / 1024**3
    available_ram = memory.available / 1024**3

    free_disk = (
        shutil.disk_usage(str(ROOT.anchor)).free
        / 1024**3
    )

except Exception as exc:
    total_ram = 0
    available_ram = 0
    free_disk = 0

    audit(
        "Resource detection",
        "WARN", repr(exc)
    )

safe_10x = (
    total_ram >= 24
    and available_ram >= 12
    and free_disk >= 30
)

audit(
    "10x resource guard",
    "PASS" if safe_10x else "WARN",
    f"RAM total={total_ram:.1f} GiB; "
    f"available={available_ram:.1f} GiB; "
    f"free disk={free_disk:.1f} GiB"
)

ten_x_rows = None

if args.run_10x:
    if not safe_10x:
        audit(
            "10x execution",
            "BLOCK",
            "Insufficient resources. Execution refused."
        )

    else:
        target = (
            ROOT / "artifacts/stageC"
            / ("benchmark_10x_" + STAMP)
        )

        p = command([
            str(python),
            "-m", "fdic_pipeline.benchmark",
            "--input", "data_processed/panel_pit.parquet",
            "--out", str(target),
            "--scales", "10",
            "--repeats", "3",
            "--master", "local[2]",
            "--partitions", "4"
        ], env=env)

        (OUT / "benchmark_10x.log").write_text(
            p.stdout + "\n" + p.stderr,
            encoding="utf-8"
        )

        result_file = target / "benchmark_runs.csv"

        ten_x_rows = (
            read_csv(result_file)
            if p.returncode == 0
            and result_file.is_file()
            else []
        )

        audit(
            "Independent 10x benchmark",
            (
                "PASS" if len(ten_x_rows) == 9
                else "BLOCK"
            ),
            f"exit={p.returncode}, rows={len(ten_x_rows)}"
        )

else:
    audit(
        "10x benchmark",
        "UNMEASURED",
        "Not executed. Figure 5 remains 5x."
    )

print("\n=== 7. MODEL AND STAGE E EVIDENCE ===")

model = (
    ROOT / "artifacts/model_30feature_corrected"
)

required = [
    "final_test_metrics.csv",
    "frozen_development_decisions.json",
    "dev_timeseries_cv.csv",
    "test_cost_sensitive_decisions.csv",
    "test_regime_diagnostics.csv",
    "cost_assumption_sensitivity.csv",
    "spark_mllib_demo.csv"
]

missing = [
    f for f in required
    if not (model / f).is_file()
]

audit(
    "Saved corrected model evidence",
    "PASS" if not missing else "WARN",
    f"missing={missing}"
)

stage_e_file = (
    ROOT / "logs/stageE/stageE_final_verified.csv"
)

if stage_e_file.is_file():
    stage_e = Counter(
        r.get("Status", "")
        for r in read_csv(stage_e_file)
    )

    audit(
        "Stage E",
        (
            "PASS"
            if stage_e["PASS"] >= 11
            and stage_e["FAIL"] == 0
            else "WARN"
        ),
        dict(stage_e)
    )

print("\n=== 8. REQUIREMENTS CLEANUP AUDIT ===")

requirements = ROOT / "requirements.txt"

uninstalled = []

if requirements.is_file():
    for line in requirements.read_text(
        encoding="utf-8-sig"
    ).splitlines():

        m = re.match(
            r"^\s*([\w.-]+)\s*==\s*([^\s;#]+)",
            line
        )

        if not m:
            continue

        try:
            metadata.version(m.group(1))
        except metadata.PackageNotFoundError:
            uninstalled.append(m.group(1))

(OUT / "uninstalled_requirements.txt").write_text(
    "\n".join(uninstalled),
    encoding="utf-8"
)

audit(
    "Uninstalled requirements entries",
    "WARN" if uninstalled else "PASS",
    f"{len(uninstalled)} entries to review in Part 7"
)

print("\n=== 9. EXPORT PART 5 REPORT ===")

summary = {
    "audit_date": "2026-11-24",
    "manifest_170_quarters": continuous,
    "saved_manifest_flags_all_pass": flags_pass,
    "raw_rows_manifest_sum": raw_total,
    "sha256_validation_status": sha_status,
    "sha256_recomputed_quarters": computed,
    "sha256_compared_quarters": matches,
    "benchmark_runs_1x_2x_5x": len(runs),
    "benchmark_complete_3x3x3": coverage,
    "benchmark_10x_status": (
        "MEASURED_SEPARATELY_NEEDS_REVIEW"
        if ten_x_rows is not None
        and len(ten_x_rows) == 9
        else "NOT_VERIFIED"
    ),
    "ten_x_hardware": {
        "ram_total_gib": round(total_ram, 2),
        "ram_available_gib": round(available_ram, 2),
        "disk_free_gib": round(free_disk, 2)
    },
    "uninstalled_requirements_entries": len(uninstalled),
    "limitations": [
        "10x not independently verified unless measured",
        "Stored sha_match flags are not independent source hashes",
        "Lifecycle adjudication remains incomplete"
    ]
}

EVIDENCE.parent.mkdir(
    parents=True, exist_ok=True
)

EVIDENCE.write_text(
    json.dumps(
        summary, indent=2, ensure_ascii=False
    ) + "\n",
    encoding="utf-8"
)

with (OUT / "checks.csv").open(
    "w", newline="", encoding="utf-8-sig"
) as f:
    writer = csv.DictWriter(
        f, fieldnames=[
            "check", "status", "details"
        ]
    )
    writer.writeheader()
    writer.writerows(RESULTS)

print("\n=== PART 5 SUMMARY ===")
print("MANIFEST_QUARTERS:", len(rows))
print(
    "MANIFEST_FLAGS:",
    "PASS" if flags_pass else "FAIL"
)
print("SHA256_REVALIDATION:", sha_status)
print(
    "BENCHMARK_27:",
    "PASS" if coverage else "REVIEW"
)
print(
    "BENCHMARK_10X:",
    summary["benchmark_10x_status"]
)
print("UNINSTALLED_REQUIREMENTS:", len(uninstalled))
print("AUDIT_REPORT:", OUT)
print("GITHUB_EVIDENCE:", EVIDENCE)
print("NO MODEL RETRAINING")
print("NO COMMIT OR PUSH")
