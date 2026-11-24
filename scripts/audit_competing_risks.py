import polars as pl

p = "data_processed/panel_pit.parquet"
df = pl.scan_parquet(p)

print("=== LABEL REASON BY SPLIT ===")
out = (
    df.group_by(["split", "label_reason"])
    .agg([
        pl.len().alias("rows"),
        pl.col("target_4q").is_not_null().sum().alias("labeled"),
        (pl.col("target_4q") == 1).sum().alias("positive")
    ])
    .sort(["split", "label_reason"])
    .collect()
)
print(out)

print("\n=== NON-FAILURE EXIT OBSERVATIONS ===")
n = (
    df.filter(pl.col("label_reason") == "VALID_NON_FAILURE_EXIT")
    .group_by("split")
    .agg([
        pl.len().alias("rows"),
        pl.col("CERT").n_unique().alias("unique_banks")
    ])
    .collect()
)
print(n)

print("\n=== UNKNOWN EXIT CENSORING ===")
unknown = df.filter(
    pl.col("label_reason") == "CENSORED_UNKNOWN_EXIT"
).select([
    pl.len().alias("rows"),
    pl.col("CERT").n_unique().alias("unique_banks")
]).collect()
print(unknown)
