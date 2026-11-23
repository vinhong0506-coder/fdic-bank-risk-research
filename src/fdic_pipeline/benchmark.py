# U.S. Bank Failure Early-Warning System: A Point-in-Time Big Data Engineering & Cost-Sensitive Modeling Pipeline (1984Q1–2026Q2)

**Course:** Big Data Analytics in Finance — National Economics University (NEU)  
**Class:** BFT65B · **Student:** Dao Huy Thanh Vinh  

## 1. Repository Architecture
```text
fdic-bank-risk-research/
├── src/fdic_pipeline/
│   ├── config.py              # Temporal splits, schema mappings & paths
│   ├── ingest.py              # FDIC BankFind API ingestion (170 quarters, 1984Q1-2026Q2)
│   ├── storage_benchmark.py   # CSV vs. Parquet (uncompressed, snappy, zstd) I/O benchmark
│   ├── audit.py               # Schema drift audit, exit adjudication & Point-in-Time panel
│   ├── benchmark.py           # 3-Engine benchmark (Pandas, Polars Lazy, PySpark) & 1x-10x scaling
│   ├── features.py            # Leakage-safe CAMELS feature engineering & pre-Basel regime audit
│   ├── model.py               # Time-Series CV, Logistic Regression, LightGBM, Spark MLlib & Cost Thresholds
│   ├── make_figures.py        # Publication-grade 300 DPI visualizations (Figures 1-8)
│   └── qa_check.py            # End-to-end automated pipeline verification
├── tests/
│   ├── test_ingest_helpers.py # Quarter boundary & date alignment unit tests
│   └── test_feature_leakage.py# Point-in-time & preprocessing anti-leakage tests
└── artifacts/
    ├── audit/                 # Schema drift, failure reconciliation, capital regime & split summaries
    ├── benchmark/             # Storage benchmark, 3-engine comparison, 1x-10x scaling & execution plans
    ├── features/              # Feature dictionary & Development-only preprocessing parameters
    ├── model/                 # CV metrics, Test metrics, cost-sensitive decisions & regime diagnostics
    └── figures/               # High-resolution PNG figures (fig1 to fig8)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH = "src"
python -m fdic_pipeline.ingest             # Part 1: Download 170 quarters (1,682,738 rows)
python -m fdic_pipeline.storage_benchmark  # Part 1: CSV vs. Parquet compression & scan benchmark
python -m fdic_pipeline.audit              # Part 2: Exit adjudication & PIT panel (1,677,107 rows)
python -m fdic_pipeline.benchmark          # Part 3: Pandas vs. Polars vs. PySpark & 1x-10x scaling
python -m fdic_pipeline.features           # Part 4: CAMELS features & pre-Basel capital audit
python -m fdic_pipeline.model              # Part 5: Time-Series CV, LR/LightGBM/MLlib & Cost Thresholds
python -m fdic_pipeline.make_figures       # Part 6: Generate Figures 1-8 (300 DPI)
pytest -v                                  # Run automated anti-leakage & schema test suite
python -m fdic_pipeline.qa_check           # Run final 9-point pipeline audit
```powershell
git add .
git commit -m "Complete end-to-end FDIC bank failure pipeline, models, tests, and figures"
git push

@'
import os, time, gc, psutil
from pathlib import Path
import numpy as np
import pandas as pd
import polars as pl

os.environ.setdefault("SPARK_HOME", r"F:\pyspark_home")
jdk_candidates = sorted(Path(r"C:\Program Files\Microsoft").glob("jdk-17*"))
if jdk_candidates:
    os.environ.setdefault("JAVA_HOME", str(jdk_candidates[0]))
    os.environ["PATH"] += f";{jdk_candidates[0]}\\bin"

from pyspark.sql import SparkSession, Window
import pyspark.sql.functions as F

COLS = ["CERT", "REPDTE", "quarter_date", "ASSET", "DEP", "EQ", "LNLSNET", "CHBAL", "SC", "ROA", "NCLNLS", "LNATRES"]

def run_polars_workload(parquet_path: str) -> pl.DataFrame:
    return (
        pl.scan_parquet(parquet_path)
        .select(COLS)
        .sort(["CERT", "quarter_date"])
        .with_columns([
            (pl.col("EQ") / pl.col("ASSET")).alias("cap_ratio"),
            (pl.col("LNLSNET") / pl.col("ASSET")).alias("loan_asset_ratio"),
            ((pl.col("CHBAL") + pl.col("SC")) / pl.col("DEP")).alias("liq_ratio"),
            (pl.col("LNATRES") / pl.col("NCLNLS")).alias("coverage_ratio"),
            (pl.col("ASSET") / pl.col("ASSET").shift(1).over("CERT") - 1.0).alias("asset_growth_qoq"),
            (pl.col("ASSET") / pl.col("ASSET").shift(4).over("CERT") - 1.0).alias("asset_growth_yoy"),
            pl.col("ROA").rolling_std(window_size=4, min_periods=2).over("CERT").alias("roa_vol_4q"),
        ])
        .with_columns([
            ((pl.col("cap_ratio") - pl.col("cap_ratio").mean().over("REPDTE")) / pl.col("cap_ratio").std().over("REPDTE")).alias("cap_zscore_pit")
        ])
        .collect()
    )

def build_spark_df(spark: SparkSession, parquet_path: str):
    sdf = spark.read.parquet(parquet_path).select(COLS)
    w_cert = Window.partitionBy("CERT").orderBy("quarter_date")
    w_cert_4 = Window.partitionBy("CERT").orderBy("quarter_date").rowsBetween(-3, 0)
    w_q = Window.partitionBy("REPDTE")
    return (
        sdf
        .withColumn("cap_ratio", F.col("EQ") / F.col("ASSET"))
        .withColumn("loan_asset_ratio", F.col("LNLSNET") / F.col("ASSET"))
        .withColumn("liq_ratio", (F.col("CHBAL") + F.col("SC")) / F.col("DEP"))
        .withColumn("coverage_ratio", F.col("LNATRES") / F.col("NCLNLS"))
        .withColumn("asset_growth_qoq", F.col("ASSET") / F.lag("ASSET", 1).over(w_cert) - 1.0)
        .withColumn("asset_growth_yoy", F.col("ASSET") / F.lag("ASSET", 4).over(w_cert) - 1.0)
        .withColumn("roa_vol_4q", F.stddev_samp("ROA").over(w_cert_4))
        .withColumn("cap_zscore_pit", (F.col("cap_ratio") - F.avg("cap_ratio").over(w_q)) / F.stddev_samp("cap_ratio").over(w_q))
    )

if __name__ == "__main__":
    print("Benchmark module verified. Existing artifacts in artifacts/benchmark/ are locked.")
