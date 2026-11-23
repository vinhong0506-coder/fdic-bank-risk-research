from pathlib import Path
import sys, os, json, subprocess, ast, zipfile, re
from datetime import datetime
import pandas as pd

ROOT = Path.cwd()
PY = sys.executable
MODE = "--full" if "--full" in sys.argv else "--check"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
OUT = ROOT / "logs" / "final_validation"
OUT.mkdir(parents=True, exist_ok=True)
checks = []

def add(name, ok, detail=""):
    status = "WARN" if ok is None else ("PASS" if ok else "FAIL")
    checks.append((name, status, str(detail)))
    print(f"[{status}] {name}: {detail}", flush=True)

def command(name, args, cwd=ROOT):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    logfile = OUT / (name + ".log")
    with logfile.open("w", encoding="utf-8") as f:
        result = subprocess.run(
            args, cwd=cwd, env=env,
            stdout=f, stderr=subprocess.STDOUT,
            check=False
        )
    tail = logfile.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines()[-10:]
    for line in tail:
        print(line, flush=True)
    add(name, result.returncode == 0,
        f"exit={result.returncode}; {logfile.name}")
    return result.returncode == 0

def safe(name, fn):
    try:
        fn()
    except Exception as e:
        add(name, False, repr(e))

print("=== FDIC FINAL VALIDATION ===")
print("Mode:", MODE)
print("Python:", PY)
print("Root:", ROOT)

def syntax():
    files = list((ROOT/"src").rglob("*.py"))
    files += list((ROOT/"tests").rglob("*.py"))
    files += list((ROOT/"scripts").rglob("*.py"))
    for p in files:
        ast.parse(p.read_text(encoding="utf-8-sig"))
    add("PYTHON_SYNTAX", True, f"{len(files)} files")

safe("PYTHON_SYNTAX", syntax)

command("PYTEST", [PY, "-m", "pytest", "-q"])

def manifest():
    p = ROOT/"data_raw/fdic/manifest_financials.json"
    m = json.loads(p.read_text(encoding="utf-8"))
    complete = sum(
        bool(v.get("complete")) for v in m.values()
    )
    add("170_QUARTERS",
        len(m) == 170 and complete == 170,
        f"manifest={len(m)}, complete={complete}")

safe("170_QUARTERS", manifest)

def data_audit():
    import polars as pl
    p = ROOT/"data_processed/features_pit.parquet"
    lf = pl.scan_parquet(str(p))
    test = lf.filter(pl.col("split") == "TEST")
    row = test.select(
        pl.len().alias("total"),
        pl.col("target_4q").is_not_null().sum().alias("valid"),
        (pl.col("target_4q") == 1).sum().alias("positive"),
        (
            (pl.col("label_reason") == "CENSORED_UNKNOWN_EXIT")
            & pl.col("target_4q").is_null()
        ).sum().alias("censored")
    ).collect().row(0)
    add("TEST_LABELS",
        row == (400698,386964,1775,13734),
        str(row))

    bad = lf.group_by(["CERT","REPDTE"]).agg(
        pl.len().alias("n")
    ).filter(pl.col("n") > 1).select(pl.len()).collect().item()
    add("UNIQUE_BANK_QUARTER", bad == 0, bad)

safe("DATA_AUDIT", data_audit)

def model_check():
    from sklearn.metrics import (
        average_precision_score, roc_auc_score
    )
    pred = pd.read_parquet(
        ROOT/"artifacts/model/test_predictions.parquet"
    )
    required = {"target_4q","prob_lr","prob_lgb"}
    if not required.issubset(pred.columns):
        raise ValueError("Missing test prediction columns")
    y = pred["target_4q"]
    if len(pred) != 386964 or y.isna().any() or y.sum() != 1775:
        raise ValueError("Test population mismatch")
    for name, col in [
        ("Logistic Regression", "prob_lr"),
        ("LightGBM", "prob_lgb")
    ]:
        pr = average_precision_score(y, pred[col])
        roc = roc_auc_score(y, pred[col])
        print(f"{name}: PR-AUC={pr:.6f}, ROC-AUC={roc:.6f}")
        add(name+"_PREDICTIONS",
            0 <= pr <= 1 and 0 <= roc <= 1,
            f"PR={pr:.6f}, ROC={roc:.6f}")

safe("MODEL_PREDICTIONS", model_check)

def benchmark_check():
    paths = [
        ROOT/"artifacts/benchmark/final/benchmark_runs_complete.csv",
        ROOT/"artifacts/benchmark/final/benchmark_runs_recovered.csv",
        ROOT/"logs/pre_github_benchmark_runs.csv"
    ]
    dfs = []
    for p in paths:
        if p.exists():
            d = pd.read_csv(p)
            if {"scale","engine","run"}.issubset(d.columns):
                dfs.append(d)
    if not dfs:
        raise ValueError("No consolidated benchmark runs")
    d = pd.concat(dfs).drop_duplicates(
        ["scale","engine","run"]
    )
    expected = {
        (s,e,r)
        for s in (1,2,5,10)
        for e in ("pandas","polars","spark")
        for r in (1,2,3)
    }
    got = set(zip(d.scale,d.engine,d.run))
    add("BENCHMARK_36_RUNS",
        expected.issubset(got),
        f"observed={len(got & expected)}/36")

    p = ROOT/"artifacts/benchmark/spark_stage3/numeric_equivalence.json"
    eq = json.loads(p.read_text(encoding="utf-8"))
    diff = max(eq["max_abs_diff_by_feature"].values())
    add("NUMERICAL_EQUIVALENCE",
        eq["status"] == "PASS" and diff < 1e-6,
        f"max_abs_diff={diff:.10g}")

safe("BENCHMARK_CHECK", benchmark_check)

def mllib():
    d = pd.read_csv(
        ROOT/"artifacts/model/spark_mllib_demo.csv"
    )
    ok = (
        len(d) == 1 and
        "Status" not in d.columns and
        int(d.iloc[0]["Train_Rows"]) == 1176223 and
        int(d.iloc[0]["Test_Rows"]) == 386964
    )
    add("MLLIB_METADATA",ok,"Counts checked")
    add("MLLIB_METRIC_REPRODUCIBILITY",None,
        "Needs independent prediction-level check; "
        "CSV metadata alone is insufficient")

safe("MLLIB_CHECK", mllib)

def figures():
    folder = ROOT/"artifacts/figures"
    names = [
        "fig1_storage_benchmark.png",
        "fig2_capital_regime_audit.png",
        "fig3_temporal_split_overview.png",
        "fig4_engine_benchmark_1x.png",
        "fig5_synthetic_scaling_10x.png",
        "fig6_test_pr_and_calibration.png",
        "fig7_top10_camels_importance.png",
        "fig8_cost_and_regime_analysis.png"
    ]
    missing = [
        n for n in names
        if not (folder/n).exists()
        or (folder/n).stat().st_size < 1000
    ]
    add("FIGURES_8",not missing,
        "missing=" + repr(missing))

safe("FIGURES_CHECK", figures)

def docx():
    docs = [
        p for p in ROOT.glob("*.docx")
        if not p.name.startswith("~$")
    ]
    if not docs:
        raise ValueError("No DOCX report found")
    for p in docs:
        with zipfile.ZipFile(p) as z:
            content = z.read("word/document.xml").decode(
                "utf-8", errors="replace"
            )
            media = [
                n for n in z.namelist()
                if n.startswith("word/media/")
                and not n.endswith("/")
            ]
            has_url = "github.com/" in content
            add("DOCX_CONTENT",
                has_url and len(media)>=8,
                f"{p.name}, media={len(media)}, URL={has_url}")
    print("NOTE: This does not verify page layout or new image identity")

safe("DOCX_CHECK", docx)

def git_check():
    p = subprocess.run(
        ["git","ls-files","-z"],
        stdout=subprocess.PIPE, check=True
    )
    paths = [
        s for s in p.stdout.decode(
            "utf-8",errors="replace"
        ).split("\0") if s
    ]
    banned = [
        s for s in paths if (
            s.startswith(("data_raw/","data_processed/"))
            or s.lower().endswith(
                (".csv",".parquet",".xlsx",".xls",".db")
            )
        )
    ]
    add("NO_TRACKED_DATA",not banned,
        f"{len(banned)} tracked data files")
    for item in banned[:10]:
        print("TRACKED:",item)

safe("GIT_CHECK", git_check)

def readme():
    p = ROOT/"README.md"
    text = p.read_text(encoding="utf-8-sig").lower()
    add("README_AI_AND_SOURCES",
        "chatgpt" in text and "fdic" in text
        and "data sources" in text,
        "Check actual disclosure before submission")

safe("README_CHECK",readme)

# Read QA CONTENT, not only process exit code.
def qa_existing():
    p = ROOT/"artifacts/qa_master_checklist.csv"
    d = pd.read_csv(p)
    if not {"Status","Check_Item"}.issubset(d.columns):
        raise ValueError("Unknown QA table schema")
    failed = d[
        ~d["Status"].astype(str).str.upper().eq("PASS")
    ]
    add("QA_CHECKLIST",failed.empty,
        f"{len(failed)} non-PASS rows")
    for _,r in failed.iterrows():
        print("QA ISSUE:",r["Check_Item"],r["Status"])

safe("QA_CHECKLIST",qa_existing)

# Optional independent rebuild from local raw source.
if MODE == "--full":
    print("\n=== INDEPENDENT REBUILD ===")
    scratch = ROOT/"repro_validation"/STAMP
    scratch.mkdir(parents=True,exist_ok=True)

    # Windows junction: source data remains in original location.
    raw = scratch/"data_raw"
    ref = scratch/"data_reference"
    if not raw.exists():
        subprocess.run(
            ["cmd","/c","mklink","/J",
             str(raw),str(ROOT/"data_raw")],
            check=True,stdout=subprocess.DEVNULL
        )
    if (ROOT/"data_reference").exists() and not ref.exists():
        subprocess.run(
            ["cmd","/c","mklink","/J",
             str(ref),str(ROOT/"data_reference")],
            check=True,stdout=subprocess.DEVNULL
        )

    (scratch/"artifacts").mkdir(exist_ok=True)

    stages = [
        ("REBUILD_STORAGE",[
            PY,"-m","fdic_pipeline.storage_benchmark"
        ]),
        ("REBUILD_AUDIT",[
            PY,"-m","fdic_pipeline.audit"
        ]),
        ("REBUILD_FEATURES",[
            PY,"-m","fdic_pipeline.features"
        ])
    ]

    stage_ok = True
    for name,cmd in stages:
        if not command(name,cmd,cwd=scratch):
            stage_ok = False
            print("STOP: dependent rebuild stages skipped")
            break

    if stage_ok:
        # Convert scratch PIT parquet to Spark-readable microseconds.
        try:
            import pyarrow as pa
            import pyarrow.compute as pc
            import pyarrow.parquet as pq
            p = scratch/"data_processed/panel_pit.parquet"
            t = pq.read_table(p)
            arrays,fields = [],[]
            for field,col in zip(t.schema,t.columns):
                typ = field.type
                if pa.types.is_timestamp(typ) and typ.unit=="ns":
                    newtyp = pa.timestamp("us",tz=typ.tz)
                    col = pc.cast(col,newtyp,safe=True)
                    field = field.with_type(newtyp)
                arrays.append(col)
                fields.append(field)
            converted=pa.Table.from_arrays(
                arrays,
                schema=pa.schema(
                    fields,metadata=t.schema.metadata
                )
            )
            sp=scratch/"data_processed/panel_pit_spark.parquet"
            pq.write_table(
                converted,sp,
                compression="zstd",
                version="1.0",
                coerce_timestamps="us"
            )
            add("REBUILD_SPARK_PARQUET",True,str(sp))
        except Exception as exc:
            add("REBUILD_SPARK_PARQUET",False,str(exc))
            stage_ok = False

    if stage_ok:
        command("REBUILD_BENCHMARK_1X",[
            PY,"-m","fdic_pipeline.benchmark",
            "--input","data_processed/panel_pit_spark.parquet",
            "--scales","1","--repeats","3",
            "--master","local[2]"
        ],cwd=scratch)

        command("REBUILD_MODEL",[
            PY,"-m","fdic_pipeline.model"
        ],cwd=scratch)

        command("REBUILD_FIGURES",[
            PY,"-m","fdic_pipeline.make_figures"
        ],cwd=scratch)

        command("REBUILD_QA",[
            PY,"-m","fdic_pipeline.qa_check"
        ],cwd=scratch)

        qa=scratch/"artifacts/qa_master_checklist.csv"
        if qa.exists():
            d=pd.read_csv(qa)
            nonpass=d[
                ~d["Status"].astype(str).str.upper().eq("PASS")
            ]
            add("REBUILD_QA_CONTENT",nonpass.empty,
                f"non-PASS rows={len(nonpass)}")

    print("Rebuild directory:",scratch)
    print("No original project artifacts overwritten")

report=pd.DataFrame(
    checks,columns=["Check","Status","Details"]
)
path=OUT/("FULL_REBUILD_REPORT.csv" if MODE=="--full"
          else "FINAL_PROJECT_AUDIT.csv")
report.to_csv(path,index=False)
print("\n=== FINAL STATUS ===")
print(report.to_string(index=False))
print("Report:",path)
print("Failures:",sum(report.Status=="FAIL"))
print("IMPORTANT: Review recorded failures before submission")

# In check mode the MLlib reproducibility warning requires
# review but does not prevent all other checks from running.
critical=report[
    (report.Status=="FAIL") &
    (report.Check!="MLLIB_METRIC_REPRODUCIBILITY")
]
sys.exit(1 if len(critical) else 0)
