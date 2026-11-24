
"""Validate the current FDIC evidence, not historical runs."""
from pathlib import Path
import argparse
import csv
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()

    if args.full:
        print(
            "Full raw-data rebuild is not certified by this "
            "current-version validator."
        )
        return 2

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    tasks = [
        ("PYTEST", [sys.executable, "-m", "pytest", "-q"]),
        ("STAGE_E", [
            sys.executable,
            "scripts/audit_fdic_stageE_after_mllib.py"
        ]),
        ("FIGURE_SHA", [
            sys.executable,
            "-m", "fdic_pipeline.make_figures",
            "--check"
        ])
    ]

    failures = 0

    for name, command in tasks:
        p = subprocess.run(
            command, cwd=ROOT, env=env,
            capture_output=True, text=True,
            encoding="utf-8", errors="replace"
        )

        status = "PASS" if p.returncode == 0 else "FAIL"
        print(name, status, "exit=", p.returncode)

        if p.returncode:
            print(p.stdout[-1500:])
            print(p.stderr[-1500:])
            failures += 1

    report = ROOT / "logs/stageE/stageE_final_verified.csv"

    if report.is_file():
        with report.open(
            encoding="utf-8-sig", newline=""
        ) as f:
            rows = list(csv.DictReader(f))

        passed = sum(
            x.get("Status") == "PASS" for x in rows
        )
        failed = sum(
            x.get("Status") == "FAIL" for x in rows
        )

        print("STAGE_E_COUNTS:", passed, "PASS,", failed, "FAIL")

        if passed < 11 or failed:
            failures += 1
    else:
        print("STAGE_E_COUNTS: FAIL - missing report")
        failures += 1

    git = subprocess.run(
        ["git", "ls-files", "-z", "artifacts/"],
        cwd=ROOT, capture_output=True
    )

    if git.returncode != 0 or git.stdout:
        print("TRACKED_ARTIFACTS: FAIL")
        failures += 1
    else:
        print("TRACKED_ARTIFACTS: PASS")

    for path in [
        ROOT / "README.md",
        ROOT / "docs/evidence/final_verified_results_20261124.md"
    ]:
        if not path.is_file():
            print("MISSING:", path)
            failures += 1

    status = "PASS" if failures == 0 else "FAIL"
    print("CURRENT_VALIDATION:", status)
    print("FAILURES:", failures)
    print(
        "OPEN WARNINGS: lifecycle adjudication, 10x, "
        "visual report review"
    )

    return int(failures > 0)

if __name__ == "__main__":
    sys.exit(main())
