from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import polars as pl

KEYS = ["CERT", "REPDTE"]
NUMERIC_CHECKS = ["ASSET", "DEP", "EQ", "NETINC", "ROA", "ROE", "RBC1AAJ", "RBCRWAJ", "COST", "QBFASSET", "QBFDEP"]


def load_panel(raw_dir: Path) -> pl.LazyFrame:
    return pl.scan_parquet(str(raw_dir / "financials" / "**/*.parquet"), hive_partitioning=False)



def audit(raw_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    files = sorted((raw_dir / "financials").glob("**/*.parquet"))
    schema_rows, quarterly_rows = [], []
    for f in files:
        df = pl.read_parquet(f)
        repdte = str(df["REPDTE"][0]) if len(df) else f.stem.split("=")[-1]
        schema_rows.append({"quarter_file": f.name, "row_count": len(df), "columns": len(df.columns),
                          "schema_signature": str([(c, str(t)) for c,t in df.schema.items()])})
        quarterly_rows.append({"REPDTE": repdte, "rows": len(df),
                              "duplicate_CERT_REPDTE": int(df.select(pl.struct(KEYS).is_duplicated().sum()).item()) if len(df) else 0})
    pd.DataFrame(schema_rows).to_csv(output_dir / "schema_by_quarter.csv", index=False)
    pd.DataFrame(quarterly_rows).to_csv(output_dir / "quarterly_counts.csv", index=False)
    lf = load_panel(raw_dir)
    summary = lf.select([pl.len().alias("rows"), pl.col("CERT").n_unique().alias("unique_CERT")]).collect()
    print("=== Panel summary ===\n", summary)
    print("=== Duplicate key count ===", lf.select(pl.struct(KEYS).is_duplicated().sum()).collect().item())
    print("=== Missingness (%) ===")
    null_exprs = [((pl.col(c).null_count() / pl.len()) * 100).alias(c) for c in lf.collect_schema().names()]
    nulls = lf.select(null_exprs).collect()
    print(nulls)
    # Numeric audit: report counts and tails; do not delete or cap raw values here.
    existing = [c for c in NUMERIC_CHECKS if c in lf.collect_schema().names()]
    exprs = []
    for c in existing:
        x = pl.col(c).cast(pl.Float64, strict=False)
        exprs.extend([x.min().alias(f"{c}_min"), x.max().alias(f"{c}_max"),
                     x.quantile(0.01).alias(f"{c}_p01"), x.quantile(0.50).alias(f"{c}_p50"),
                     x.quantile(0.99).alias(f"{c}_p99")])
    numeric = lf.select(exprs).collect()
    numeric.write_csv(output_dir / "numeric_extremes.csv")
    print("=== Numeric audit saved ===", output_dir / "numeric_extremes.csv")
    print("=== Schema audit saved ===", output_dir / "schema_by_quarter.csv")


def create_panel(raw_dir: Path, output_path: Path, mapping_path: Path | None = None) -> None:
    """Build conservative PIT panel. Exit mapping CSV must have CERT,event_date,event_type.
    Accepted event_type values: FAILURE, MERGER, VOLUNTARY_LIQUIDATION, OTHER_EXIT, UNKNOWN.
    Unknown/other exits are censored for labels after event_date; they are never silently treated as negatives.
    """
    fin = pl.read_parquet(str(raw_dir / "financials" / "**/*.parquet"), hive_partitioning=False)
    fin = fin.with_columns(pl.col("CERT").cast(pl.Int64, strict=False))
    dup_keys = fin.select(pl.struct(["CERT", "REPDTE"]).is_duplicated().sum()).item()
    if dup_keys:
        raise ValueError(f"Duplicate CERT-REPDTE keys ({dup_keys}); adjudicate before panel build")
    fails = pl.read_parquet(raw_dir / "failures.parquet")
    inst = pl.read_parquet(raw_dir / "institutions.parquet")
    fin = fin.with_columns(pl.col("REPDTE").cast(pl.String).str.strptime(pl.Date, "%Y%m%d", strict=False).alias("quarter_date"))
    fails = fails.with_columns(pl.col("FAILDATE").cast(pl.String).str.strptime(pl.Date, "%Y%m%d", strict=False).alias("fail_date"))
    # failure events only sourced from the official failure list
    event = fails.select([pl.col("CERT").cast(pl.Int64, strict=False), pl.col("fail_date").alias("event_date"), pl.lit("FAILURE").alias("event_type")])
    if mapping_path and mapping_path.exists():
        mapping = pl.read_csv(mapping_path, try_parse_dates=True).with_columns(pl.col("event_date").cast(pl.Date))
        event = pl.concat([event, mapping.select([pl.col("CERT").cast(pl.Int64, strict=False), "event_date", "event_type"])])
    event = event.unique(subset=["CERT", "event_date", "event_type"])
    # Rows after any known institution end date are dropped; unknown exit classification is not inferred.
    inst_end = inst.select([pl.col("CERT").cast(pl.Int64, strict=False),
                           pl.col("ENDEFYMD").cast(pl.String).str.strptime(pl.Date, "%Y%m%d", strict=False).alias("end_date")])
    panel = fin.join(inst_end, on="CERT", how="left").filter(pl.col("end_date").is_null() | (pl.col("quarter_date") <= pl.col("end_date")))
    # Label: positive if a failure in (q,q+4Q]; negative only if follow-up horizon is covered and no known exit censored in horizon.
    event_fail = event.filter(pl.col("event_type") == "FAILURE").select(["CERT", pl.col("event_date").alias("fail_date")])
    exits = event.filter(pl.col("event_type").is_in(["MERGER", "VOLUNTARY_LIQUIDATION", "OTHER_EXIT", "UNKNOWN"]))
    exits = exits.group_by("CERT").agg(pl.col("event_date").min().alias("exit_date"))
    max_date = panel.select(pl.col("quarter_date").max()).item()
    panel = panel.join(event_fail, on="CERT", how="left").join(exits.select(["CERT", "exit_date"]), on="CERT", how="left")
    panel = panel.with_columns((pl.col("quarter_date").dt.offset_by("12mo")).alias("horizon_end"))
    panel = panel.with_columns(pl.when((pl.col("fail_date") > pl.col("quarter_date")) & (pl.col("fail_date") <= pl.col("horizon_end"))).then(1)
                             .when((pl.col("horizon_end") <= max_date) & (pl.col("exit_date").is_null() | (pl.col("exit_date") > pl.col("horizon_end")))).then(0)
                             .otherwise(None).cast(pl.Int8).alias("target_4q"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.write_parquet(output_path, compression="zstd")
    print(f"PIT panel rows={panel.height():,}; labels={panel.select(pl.col('target_4q').value_counts()).to_dicts()}")

if __name__ == "__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--raw",default="data_raw/fdic"); ap.add_argument("--out",default="artifacts/audit"); ap.add_argument("--panel",default="data_processed/panel_pit.parquet"); ap.add_argument("--exit-map",default="data_reference/exit_mapping.csv")
    a=ap.parse_args(); audit(Path(a.raw),Path(a.out)); create_panel(Path(a.raw),Path(a.panel),Path(a.exit_map))
