from pathlib import Path
import pandas as pd
import polars as pl

raw = Path("data_raw/fdic")
out = Path("logs/exit_review")
out.mkdir(parents=True, exist_ok=True)

def parse_dates(series):
    s = series.astype("string").str.strip().str.replace(
        r"\.0$", "", regex=True
    )
    a = pd.to_datetime(s, format="%Y%m%d", errors="coerce")
    b = pd.to_datetime(s, format="mixed", errors="coerce")
    return a.fillna(b)

print("=== 1. READ FINANCIAL REPORTING HISTORY ===", flush=True)

files = sorted((raw / "financials").rglob("*.parquet"))
if len(files) != 170:
    raise ValueError(f"Expected 170 files, found {len(files)}")

history = (
    pl.scan_parquet(
        [str(f) for f in files],
        hive_partitioning=False
    )
    .select([
        pl.col("CERT").cast(pl.Int64, strict=False),
        pl.col("REPDTE").cast(pl.String)
    ])
    .group_by("CERT")
    .agg([
        pl.col("REPDTE").max().alias("last_REPDTE"),
        pl.len().alias("report_count")
    ])
    .collect()
    .to_pandas()
)

print("Unique financial CERT:", len(history))

print("\n=== 2. COMPARE INSTITUTION END DATES ===", flush=True)

inst = pd.read_parquet(
    raw / "institutions.parquet"
)

if not {"CERT", "ENDEFYMD"}.issubset(inst.columns):
    raise ValueError("Missing CERT or ENDEFYMD")

inst["CERT"] = pd.to_numeric(
    inst["CERT"], errors="coerce"
).astype("Int64")

inst["inst_end_date"] = parse_dates(inst["ENDEFYMD"])

institution = (
    inst.dropna(subset=["CERT"])
    .groupby("CERT", as_index=False)["inst_end_date"]
    .min()
)

history["last_report_date"] = parse_dates(history["last_REPDTE"])
joined = history.merge(
    institution, on="CERT", how="left",
    validate="one_to_one"
)

joined["reported_after_end"] = (
    joined["inst_end_date"].notna()
    & (joined["last_report_date"] > joined["inst_end_date"])
)

problem = joined[joined["reported_after_end"]].copy()

print("CERT with financial reports after ENDEFYMD:",len(problem))
print("Total financial observations belonging to these CERT:",
      int(problem["report_count"].sum()))

problem.to_csv(
    out / "reporting_after_end_date.csv", index=False
)

print("\n=== 3. FAILURE DATE CONFLICTS ===", flush=True)

fails = pd.read_parquet(raw / "failures.parquet")
fails["CERT"] = pd.to_numeric(
    fails["CERT"], errors="coerce"
).astype("Int64")
fails["failure_date"] = parse_dates(fails["FAILDATE"])

failure_dates = (
    fails.dropna(subset=["CERT","failure_date"])
    .groupby("CERT", as_index=False)["failure_date"]
    .min()
)

conflicts = (
    institution.merge(
        failure_dates, on="CERT", how="inner"
    )
)

conflicts = conflicts[
    conflicts["inst_end_date"].notna()
    & (conflicts["inst_end_date"] < conflicts["failure_date"])
].copy()

conflicts["days_difference"] = (
    conflicts["failure_date"]
    - conflicts["inst_end_date"]
).dt.days

conflicts.to_csv(
    out / "failure_end_date_conflicts.csv",index=False
)

print("Distinct CERT with end date before failure:",
      len(conflicts))

if len(conflicts):
    print("Days difference distribution:")
    print(conflicts["days_difference"].describe())
    print("Ten largest differences:")
    print(conflicts.sort_values(
        "days_difference",ascending=False
    ).head(10).to_string(index=False))

print("\n=== 4. OUTPUT ===", flush=True)
print(out / "reporting_after_end_date.csv")
print(out / "failure_end_date_conflicts.csv")
print("DIAGNOSTIC COMPLETE: ORIGINAL DATA UNCHANGED")
