from pathlib import Path
import pandas as pd

print("=== 1. EXIT MAPPING ===")
mapping = Path("data_reference/exit_mapping.csv")

if mapping.exists():
    m = pd.read_csv(mapping)
    print("Mapping rows:", len(m))
    print("Columns:", m.columns.tolist())
    if "event_type" in m.columns:
        print(m["event_type"].value_counts(dropna=False))
    if "CERT" in m.columns:
        print("Duplicate CERT:", int(m["CERT"].duplicated().sum()))
else:
    print("NO EXIT MAPPING FILE")
    print("Verified mergers cannot be identified from this mapping.")

print("\n=== 2. PANEL EXIT TYPES ===")

panel = Path("data_processed/panel_pit.parquet")
cols = pd.read_parquet(panel).columns.tolist()

wanted = [
    "CERT", "REPDTE", "split", "exit_type",
    "label_reason", "target_4q", "quarter_date",
    "failure_date", "inst_end_date",
    "event_date", "confirmed_exit_date",
    "horizon_end_date"
]

d = pd.read_parquet(
    panel,
    columns=[c for c in wanted if c in cols]
)

print(d["exit_type"].value_counts(dropna=False))
print("\nEXIT TYPE X LABEL REASON")
print(pd.crosstab(d["exit_type"], d["label_reason"]))

print("\n=== 3. UNKNOWN EXIT CASES ===")

u = d[d["label_reason"] == "CENSORED_UNKNOWN_EXIT"].copy()
print("Censored observations:", len(u))
print("Distinct CERT:", u["CERT"].nunique())
print("By split:")
print(u.groupby("split").agg(
    observations=("CERT", "size"),
    distinct_CERT=("CERT", "nunique")
))

for c in ("failure_date", "inst_end_date", "event_date"):
    if c in u.columns:
        print(c, "non-null:", int(u[c].notna().sum()))

print("\n=== 4. FAILURE DATE CONSISTENCY ===")

for c in (
    "quarter_date", "failure_date",
    "inst_end_date", "event_date",
    "confirmed_exit_date"
):
    if c in d.columns:
        d[c] = pd.to_datetime(d[c], errors="coerce")

if {"failure_date", "inst_end_date"}.issubset(d.columns):
    conflict = d[
        d["failure_date"].notna()
        & d["inst_end_date"].notna()
        & (d["inst_end_date"] < d["failure_date"])
    ]
    print("Bank-quarter rows with institution end before failure:", len(conflict))
    print("Distinct CERT involved:", conflict["CERT"].nunique())
    if len(conflict):
        print("Examples:")
        print(conflict[
            ["CERT", "REPDTE", "failure_date", "inst_end_date"]
        ].drop_duplicates("CERT").head(10).to_string(index=False))

print("\n=== 5. SCOPE CHECK ===")
print("Panel rows:", len(d))
print("Unique CERT:", d["CERT"].nunique())
print("Unique CERT-REPDTE duplicates:",
      int(d.duplicated(["CERT","REPDTE"]).sum()))

print("\nDIAGNOSTIC COMPLETE - NO FILES MODIFIED")
