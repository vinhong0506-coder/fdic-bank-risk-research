import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(
        encoding="utf-8",
        errors="replace"
    )

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(
        encoding="utf-8",
        errors="replace"
    )
from pathlib import Path
import json
import subprocess
import sys

import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

ROOT = Path.cwd()
DATA = ROOT / "data_processed"
MODEL = ROOT / "artifacts" / "model"
LOGS = ROOT / "logs"

def convert_parquet(name):
    src = DATA / f"{name}.parquet"
    dst = DATA / f"{name}_spark.parquet"

    if not src.exists():
        raise FileNotFoundError(f"Missing: {src}")

    print(f"\n[CONVERT] {src.name}", flush=True)

    table = pq.read_table(src)
    arrays = []
    fields = []
    changed = []

    for field, col in zip(table.schema, table.columns):
        typ = field.type

        if pa.types.is_timestamp(typ) and typ.unit == "ns":
            new_type = pa.timestamp("us", tz=typ.tz)
            converted = pc.cast(col, new_type, safe=True)

            arrays.append(converted)
            fields.append(field.with_type(new_type))
            changed.append(field.name)
        else:
            arrays.append(col)
            fields.append(field)

    result = pa.Table.from_arrays(
        arrays,
        schema=pa.schema(fields, metadata=table.schema.metadata)
    )

    tmp = DATA / f"{name}_spark.tmp.parquet"

    try:
        pq.write_table(
            result,
            tmp,
            compression="zstd",
            version="1.0",
            coerce_timestamps="us"
        )

        assert pq.read_metadata(tmp).num_rows == table.num_rows

        tmp.replace(dst)
    finally:
        if tmp.exists():
            tmp.unlink()

    print("Converted columns:", changed)
    print("Rows:", table.num_rows)
    print("Output:", dst)
    return dst

def run_command(cmd, log_name):
    print("\nRUN:", " ".join(map(str, cmd)), flush=True)

    with (LOGS / log_name).open("w", encoding="utf-8") as f:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1
        )

        for line in process.stdout:
            print(line, end="", flush=True)
            f.write(line)

        code = process.wait()

    if code != 0:
        raise RuntimeError(
            f"Command failed ({code}). See logs/{log_name}"
        )

def main():
    panel = convert_parquet("panel_pit")
    features = convert_parquet("features_pit")

    print("\n[CHECK] Spark Parquet compatibility")

    from pyspark.sql import SparkSession

    spark = (
        SparkSession.builder
        .master("local[2]")
        .appName("FDIC-Parquet-Compatibility")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")

    try:
        for path in [panel, features]:
            df = spark.read.parquet(str(path))
            n = df.count()

            expected = pq.read_metadata(path).num_rows
            assert n == expected

            print("SPARK READ PASS:", path.name, n)
    finally:
        spark.stop()

    print("\n[STEP 1] Three-engine benchmark 1x")

    run_command(
        [
            sys.executable,
            "-m", "fdic_pipeline.benchmark",
            "--input", str(panel),
            "--scales", "1",
            "--repeats", "3",
            "--master", "local[2]"
        ],
        "benchmark_1x_fixed.log"
    )

    print("\n[STEP 2] Spark MLlib demo")

    from fdic_pipeline.model import run_spark_mllib_demo

    dictionary_path = (
        ROOT / "artifacts" / "features"
        / "feature_dictionary.csv"
    )

    dictionary = pd.read_csv(dictionary_path)

    base_features = dictionary["feature"].tolist()

    feature_cols = [
        col
        for name in base_features
        for col in (f"{name}_isna", name)
    ]

    available = set(pq.read_schema(features).names)
    missing = set(feature_cols) - available

    if missing:
        raise ValueError(
            f"Missing MLlib feature columns: {sorted(missing)}"
        )

    run_spark_mllib_demo(
        features,
        feature_cols,
        MODEL
    )

    result_path = MODEL / "spark_mllib_demo.csv"
    result = pd.read_csv(result_path)

    print("\n=== SPARK MLLIB RESULT ===")
    print(result.to_string(index=False))

    if "Status" in result.columns:
        raise RuntimeError(
            "Spark MLlib was skipped. Check the Status above."
        )

    if not {"Test_PR_AUC", "Test_ROC_AUC"}.issubset(result.columns):
        raise RuntimeError("Missing Spark MLlib metrics.")

    print("\n======================================")
    print("SPARK FIX COMPLETED")
    print("Benchmark and MLlib completed")
    print("Original FDIC Parquet files unchanged")
    print("======================================")

if __name__ == "__main__":
    main()
