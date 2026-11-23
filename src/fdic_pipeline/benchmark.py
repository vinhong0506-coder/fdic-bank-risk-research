from __future__ import annotations
import argparse, time, os, gc
from pathlib import Path
import pandas as pd
import polars as pl


def pandas_transform(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["CERT", "REPDTE"]).copy()
    df["quarter"] = pd.to_datetime(df["REPDTE"].astype(str), format="%Y%m%d")
    df["equity_assets"] = df["EQ"] / df["ASSET"].where(df["ASSET"] > 0)
    df["loan_assets"] = df["LNLSNET"] / df["ASSET"].where(df["ASSET"] > 0)
    df["asset_qoq"] = df.groupby("CERT")["ASSET"].pct_change()
    df["asset_yoy"] = df.groupby("CERT")["ASSET"].pct_change(4)
    df["equity_vol_4q"] = df.groupby("CERT")["equity_assets"].rolling(4, min_periods=2).std().reset_index(level=0, drop=True)
    return df


def polars_transform(lf: pl.LazyFrame) -> pl.LazyFrame:
    lf = lf.sort(["CERT", "REPDTE"]).with_columns(pl.col("REPDTE").cast(pl.String).str.strptime(pl.Date, "%Y%m%d", strict=False).alias("quarter"))
    lf = lf.with_columns([
        (pl.col("EQ") / pl.when(pl.col("ASSET") > 0).then(pl.col("ASSET")).otherwise(None)).alias("equity_assets"),
        (pl.col("LNLSNET") / pl.when(pl.col("ASSET") > 0).then(pl.col("ASSET")).otherwise(None)).alias("loan_assets")])
    lf = lf.with_columns([
        pl.col("ASSET").pct_change().over("CERT").alias("asset_qoq"),
        pl.col("ASSET").pct_change(4).over("CERT").alias("asset_yoy"),
        pl.col("equity_assets").rolling_std(window_size=4, min_samples=2).over("CERT").alias("equity_vol_4q")])
    return lf


def timed(label, fn):
    gc.collect(); t0=time.perf_counter(); out=fn(); elapsed=time.perf_counter()-t0
    print(f"{label}: {elapsed:.4f} seconds")
    return out, elapsed



def run(raw_dir: Path, output_dir: Path):
    files=sorted((raw_dir/"financials").glob("**/*.parquet")); output_dir.mkdir(parents=True,exist_ok=True)
    # Use a bounded sample for laptop-friendly repeatable benchmark; override via --all in your final run.
    print(f"Input files: {len(files)}")
    df=pd.concat([pd.read_parquet(f) for f in files],ignore_index=True)
    print(f"Loaded pandas baseline: rows={len(df):,}, RAM={df.memory_usage(deep=True).sum()/1024**2:.2f} MiB")
    p_out,p_time=timed("Pandas transformation",lambda:pandas_transform(df))
    lf=pl.scan_parquet([str(f) for f in files], hive_partitioning=False)
    l_out,l_time=timed("Polars lazy collect",lambda:polars_transform(lf).collect(engine="streaming"))
    # Numerical equivalence on selected columns, allowing engine-specific ordering/dtypes.
    cols=["CERT","REPDTE","equity_assets","loan_assets","asset_qoq","asset_yoy","equity_vol_4q"]
    p_cmp=p_out[cols].sort_values(["CERT","REPDTE"]).reset_index(drop=True)
    l_cmp=l_out.select(cols).sort(["CERT","REPDTE"]).to_pandas()
    pd.testing.assert_frame_equal(p_cmp,l_cmp,check_dtype=False,check_exact=False,rtol=1e-6,atol=1e-8)
    print("Pandas vs Polars: selected numerical outputs PASS")
    results=pd.DataFrame([{"engine":"Pandas", "wall_seconds":p_time,"rows":len(p_out)},
                         {"engine":"Polars Lazy", "wall_seconds":l_time,"rows":l_out.height}])
    results["speedup_vs_pandas"]=p_time/results.wall_seconds
    results.to_csv(output_dir/"benchmark_results.csv",index=False)
    print(results.to_markdown(index=False))
    print("Polars optimized plan:\n",polars_transform(pl.scan_parquet([str(f) for f in files],hive_partitioning=False)).explain(optimized=True))


def spark_demo(raw_dir: Path):
    try:
        from pyspark.sql import SparkSession, functions as F
    except ImportError:
        print("PySpark not installed. Install optional extra and rerun."); return
    spark=SparkSession.builder.master("local[*]").appName("BFT65B-FDIC").config("spark.sql.shuffle.partitions","8").getOrCreate()
    files=[str(f) for f in sorted((raw_dir/"financials").glob("**/*.parquet"))]
    sdf=spark.read.parquet(*files)
    out=sdf.withColumn("equity_assets",F.col("EQ")/F.when(F.col("ASSET")>0,F.col("ASSET")))
    out.explain(mode="formatted")
    spark_count=out.count()
    print("Spark rows:",spark_count)
    # Equivalence check on core ratio using bounded, deterministic first-quarter sample.
    sample_file=sorted((raw_dir/"financials").glob("**/*.parquet"))[0]
    pandas_sample=pd.read_parquet(sample_file)
    pl_sample=polars_transform(pl.from_pandas(pandas_sample).lazy()).collect()
    spark_sample=spark.read.parquet(str(sample_file)).withColumn("equity_assets",F.col("EQ")/F.when(F.col("ASSET")>0,F.col("ASSET")))
    spark_compare=spark_sample.select("CERT","REPDTE","equity_assets").toPandas().sort_values(["CERT","REPDTE"]).reset_index(drop=True)
    pl_compare=pl_sample.select("CERT","REPDTE","equity_assets").to_pandas().sort_values(["CERT","REPDTE"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(spark_compare,pl_compare,check_dtype=False,check_exact=False,rtol=1e-6,atol=1e-8)
    print("Spark vs Polars ratio sample equivalence: PASS")
    spark.stop()

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--raw",default="data_raw/fdic"); ap.add_argument("--out",default="artifacts/benchmark"); ap.add_argument("--spark",action="store_true"); a=ap.parse_args()
    run(Path(a.raw),Path(a.out));
    if a.spark: spark_demo(Path(a.raw))
