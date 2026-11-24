"""Safety-first, small-data preflight for FDIC EWS / Python 3.11 / Spark 3.5.

Run after dot-sourcing env_setup.ps1. Does not run full FDIC ingestion, models,
or scaling benchmarks. Writes diagnostic evidence only.
"""
from __future__ import annotations
import importlib.metadata as md
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "diagnostics" / ("stage1_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
OUT.mkdir(parents=True, exist_ok=False)
results: list[dict] = []


def note(name: str, status: str, detail: str = "") -> None:
    results.append({"check": name, "status": status, "detail": detail})
    print(f"[{status:4}] {name}: {detail}", flush=True)


def run(name: str, cmd: list[str], timeout: int = 120) -> None:
    try:
        cp = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        log_path = OUT / f"{name}.log"
        log_path.write_text(cp.stdout + "\n===== STDERR =====\n" + cp.stderr, encoding="utf-8")
        excerpt = (cp.stdout + "\n" + cp.stderr).strip().splitlines()[-4:]
        note(name, "PASS" if cp.returncode == 0 else "FAIL", f"returncode={cp.returncode}; log={log_path.name}; tail={' | '.join(excerpt)[-400:]}")
    except subprocess.TimeoutExpired:
        note(name, "FAIL", f"timeout after {timeout}s")
    except Exception as exc:
        note(name, "FAIL", f"{type(exc).__name__}: {exc}")


def main() -> int:
    print("REPO:", ROOT)
    print("PYTHON:", sys.executable, sys.version.split()[0])
    print("ENV SPARK_HOME:", os.environ.get("SPARK_HOME", "<unset>"))
    print("ENV JAVA_HOME:", os.environ.get("JAVA_HOME", "<unset>"))
    print("ENV PYSPARK_PYTHON:", os.environ.get("PYSPARK_PYTHON", "<unset>"))

    note("python_311", "PASS" if sys.version_info[:2] == (3, 11) else "FAIL", sys.version.split()[0])
    for pkg in ("pyspark", "numpy", "pandas", "polars", "pyarrow", "scikit-learn", "lightgbm", "pytest"):
        try:
            note("pkg_" + pkg, "PASS", md.version(pkg))
        except md.PackageNotFoundError:
            note("pkg_" + pkg, "FAIL", "package not installed")

    # Conservative compatibility contract for PySpark 3.5's Python APIs.
    def version_first(package: str) -> int | None:
        try:
            return int(md.version(package).split(".")[0])
        except (md.PackageNotFoundError, ValueError):
            return None
    note("numpy_major_lt_2", "PASS" if version_first("numpy") is not None and version_first("numpy") < 2 else "FAIL", "NumPy 1.x required for conservative PySpark 3.5 reproducibility")
    note("pandas_major_lt_3", "PASS" if version_first("pandas") is not None and version_first("pandas") < 3 else "FAIL", "Pandas 2.x baseline")
    note("pyarrow_major_lt_13", "PASS" if version_first("pyarrow") is not None and version_first("pyarrow") < 13 else "FAIL", "PyArrow <13 baseline for Spark 3.5 pandas interfaces")

    spark_home = Path(os.environ.get("SPARK_HOME", "__unset__"))
    note("spark_launcher", "PASS" if (spark_home / "bin" / "spark-submit.cmd").is_file() else "FAIL", str(spark_home))
    note("python_worker_env", "PASS" if Path(os.environ.get("PYSPARK_PYTHON", "__unset__")).resolve() == Path(sys.executable).resolve() else "FAIL", "worker must match current Python executable")

    try:
        import polars as pl
        # Constructor alone detects removed rolling_std argument names.
        pl.col("x").rolling_std(window_size=4, min_samples=4, ddof=1)
        for path in (ROOT / "src/fdic_pipeline/features.py", ROOT / "src/fdic_pipeline/workload.py"):
            if "rolling_std(window_size=4, min_periods=4" in path.read_text(encoding="utf-8-sig"):
                raise ValueError(f"outdated rolling_std keyword in {path.name}")
        note("polars_rolling_api", "PASS", f"Polars {pl.__version__}; min_samples supported")
    except Exception as exc:
        note("polars_rolling_api", "FAIL", str(exc))

    data = ROOT / "data_raw" / "fdic"
    manifest = data / "manifest_financials.json"
    if manifest.exists():
        try:
            obj = json.loads(manifest.read_text(encoding="utf-8-sig"))
            note("manifest_exists", "PASS", f"{len(obj)} entries, not yet SHA-256 revalidated")
        except Exception as exc:
            note("manifest_exists", "FAIL", f"invalid JSON: {exc}")
    else:
        note("manifest_exists", "WARN", "missing locally; do not download again until data location is confirmed")
    for rel in ("data_raw/fdic/failures.parquet", "data_raw/fdic/institutions.parquet", "data_processed/panel_pit.parquet"):
        note("data_" + Path(rel).name, "PASS" if (ROOT / rel).is_file() else "WARN", rel)

    run("pip_check", [sys.executable, "-m", "pip", "check"], timeout=90)
    run("git_status", ["git", "status", "--short", "--branch"], timeout=30)

    spark_code = r'''
from pyspark.sql import SparkSession
import pandas as pd
s = SparkSession.builder.master("local[2]").appName("FDIC_STAGE1_ONLY").config("spark.ui.enabled", "false").config("spark.sql.shuffle.partitions","2").getOrCreate()
try:
    s.sparkContext.setLogLevel("ERROR")
    assert s.range(5).count() == 5
    vals = s.sparkContext.parallelize([1,2,3], 2).map(lambda x: x + 1).collect()
    assert sorted(vals) == [2,3,4], vals
    s.conf.set("spark.sql.execution.arrow.pyspark.enabled", "false")
    back = s.createDataFrame(pd.DataFrame({"x":[1,2],"y":["a","b"]})).toPandas()
    assert list(back["x"]) == [1,2], back
    print("SPARK_WORKER_AND_PANDAS_PASS: count=5 python_worker=3 rows pandas_bridge=2")
finally:
    s.stop()
'''
    run("spark_worker_pandas_smoke", [sys.executable, "-c", spark_code], timeout=150)
    run("pytest_synthetic", [sys.executable, "-m", "pytest", "-q", "tests"], timeout=150)

    report = OUT / "preflight.json"
    report.write_text(json.dumps({"python": sys.executable, "repo": str(ROOT), "checks": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    failed = [x["check"] for x in results if x["status"] == "FAIL"]
    print("\nREPORT:", report)
    print("SUMMARY:", "PASS" if not failed else "FAIL", "failed checks:", failed)
    return 0 if not failed else 2


if __name__ == "__main__":
    sys.exit(main())
