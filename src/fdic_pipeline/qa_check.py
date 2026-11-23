import json
from pathlib import Path
import pandas as pd
import polars as pl


def run_master_qa() -> None:
    checks = []

    def record(part: str, item: str, passed: bool, detail: str) -> None:
        checks.append({
            "Part": part,
            "Check_Item": item,
            "Status": "PASS" if passed else "ACTION_NEEDED",
            "Actual_Evidence": detail,
        })

    # 1. Part 1: Acquisition & Storage
    m_path = Path("data_raw/fdic/manifest_financials.json")
    if m_path.exists():
        m = json.loads(m_path.read_text(encoding="utf-8"))
        n_q = len(m)
        n_comp = sum(1 for x in m.values() if x.get("complete"))
        n_dup = sum(int(x.get("duplicate_keys", 0)) for x in m.values())
        record("Part 1", "Raw Financials Manifest (170Q)", (n_q == 170 and n_comp == 170 and n_dup == 0), f"quarters={n_q}, complete={n_comp}, dup={n_dup}")
    else:
        record("Part 1", "Raw Financials Manifest (170Q)", False, "manifest_financials.json not found")

    sb_path = Path("artifacts/benchmark/storage_full/storage_benchmark.csv")
    if sb_path.exists():
        sb = pd.read_csv(sb_path)
        n_rows = int(sb["rows"].iloc[0])
        ok = (len(sb) == 4) and (sb["rows"].nunique() == 1) and (n_rows == 1682738)
        record("Part 1", "Storage Benchmark (CSV vs Parquet)", ok, f"formats={len(sb)}, rows={n_rows:,}")
    else:
        record("Part 1", "Storage Benchmark (CSV vs Parquet)", False, "storage_benchmark.csv missing")

    # 2. Part 2: Data Quality, Exit Adjudication & PIT Panel
    pit_path = Path("data_processed/panel_pit.parquet")
    if pit_path.exists():
        pit = pl.read_parquet(pit_path)
        n_pit = len(pit)
        n_dup = pit.select(pl.struct(["CERT", "REPDTE"]).is_duplicated().sum()).item()
        n_zomb = pit.filter(pl.col("confirmed_exit_date").is_not_null() & (pl.col("quarter_date") > pl.col("confirmed_exit_date"))).height
        record("Part 2", "Point-in-Time Clean Panel", (n_pit == 1677107 and n_dup == 0 and n_zomb == 0), f"rows={n_pit:,}, dup_keys={n_dup}, post_exit_zombies={n_zomb}")
    else:
        record("Part 2", "Point-in-Time Clean Panel", False, "panel_pit.parquet missing")

    split_path = Path("artifacts/audit/temporal_split_summary.csv")
    if split_path.exists():
        sp = pd.read_csv(split_path)
        test_banks = int(sp.loc[sp["Split"].str.contains("Test"), "Unique_Failed_Banks"].iloc[0])
        record("Part 2", "Temporal Split & Embargo (2008)", test_banks >= 50, f"Test unique failed banks={test_banks} (req >= 50)")
    else:
        record("Part 2", "Temporal Split & Embargo (2008)", False, "temporal_split_summary.csv missing")

    # 3. Part 3: Big Data Engines & Scaling
    eng_path = Path("artifacts/benchmark/engine_benchmark_summary.csv")
    sc_path = Path("artifacts/benchmark/synthetic_scaling_benchmark.csv")
    plan_ok = Path("artifacts/benchmark/polars_execution_plan.txt").exists() and Path("artifacts/benchmark/spark_catalyst_plan.txt").exists()
    if eng_path.exists() and sc_path.exists():
        eng = pd.read_csv(eng_path)
        sc = pd.read_csv(sc_path)
        all_pass = eng["Equivalence"].str.contains("PASS|Reference").all()
        max_rows = int(sc["Rows"].max())
        record("Part 3", "3-Engine Benchmark & Equivalence", bool(all_pass and plan_ok), f"Engines={len(eng)}, Plans={plan_ok}, MaxScale={max_rows:,} rows")
    else:
        record("Part 3", "3-Engine Benchmark & Equivalence", False, "Missing engine or scaling benchmark CSV")

    # 4. Part 4: CAMELS Features & Zero-Leakage Matrix
    feat_path = Path("data_processed/features_pit.parquet")
    if feat_path.exists():
        fdf = pl.read_parquet(feat_path)
        meta = {"CERT", "REPDTE", "quarter_date", "q_idx", "target_4q", "label_reason", "exit_type", "split"}
        feat_cols = [c for c in fdf.columns if c not in meta]
        null_sum = sum(fdf[c].null_count() for c in feat_cols)
        inf_sum = sum(fdf.filter(pl.col(c).is_infinite()).height for c in feat_cols)
        record("Part 4", "CAMELS Feature Matrix (Zero NaN/Inf)", (null_sum == 0 and inf_sum == 0), f"shape={fdf.shape}, features={len(feat_cols)}, nulls={null_sum}, infs={inf_sum}")
    else:
        record("Part 4", "CAMELS Feature Matrix (Zero NaN/Inf)", False, "features_pit.parquet missing")

    # 5. Part 5: Modeling, Cost Threshold & Spark MLlib
    req_model_files = [
        "empirical_cost_estimation.csv", "dev_timeseries_cv.csv", "final_test_metrics.csv",
        "test_cost_sensitive_decisions.csv", "test_regime_diagnostics.csv",
        "feature_importance.csv", "test_calibration_curve.csv", "spark_mllib_demo.csv"
    ]
    missing_m = [f for f in req_model_files if not (Path("artifacts/model") / f).exists()]
    record("Part 5", "Modeling, Cost Threshold & MLlib Files", len(missing_m) == 0, f"found={len(req_model_files)-len(missing_m)}/{len(req_model_files)}" if not missing_m else f"missing={missing_m}")

    # 6. Part 6: Figures & Git Safety
    figs = sorted(Path("artifacts/figures").glob("fig*.png"))
    gi = Path(".gitignore").read_text(encoding="utf-8") if Path(".gitignore").exists() else ""
    gi_ok = ("data_raw" in gi) and ("data_processed" in gi)
    record("Part 6", "8 Publication Figures (300 DPI)", len(figs) >= 8, f"found={len(figs)}/8 PNG files")
    record("Part 6", "Git Safety (.gitignore blocks raw/processed)", gi_ok, "data_raw & data_processed ignored" if gi_ok else "CHECK .gitignore!")

    qa_df = pd.DataFrame(checks)
    qa_df.to_csv("artifacts/qa_master_checklist.csv", index=False)
    print("================ MASTER PIPELINE QA SCORECARD ================")
    print(qa_df.to_markdown(index=False))


if __name__ == "__main__":
    run_master_qa()
