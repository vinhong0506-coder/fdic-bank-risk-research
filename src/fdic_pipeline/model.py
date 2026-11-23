from __future__ import annotations
import os
import time
from pathlib import Path
import numpy as np
import pandas as pd
import polars as pl
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
    brier_score_loss,
    confusion_matrix,
)
from sklearn.calibration import calibration_curve
import lightgbm as lgb
from fdic_pipeline.features import build_raw_camels_features, LeakageSafePreprocessor

BASE_FEATURES = [
    "cap_ratio", "rbc_tier1", "rbc_total", "neg_equity_flag", "is_pre_basel",
    "npl_ratio", "reserve_coverage", "nonperf_asset_ratio", "ore_ratio", "re_loan_share", "ci_loan_share",
    "eff_ratio", "nonix_asset_ratio",
    "roa", "roe", "nimy", "roa_lag1", "roa_lag4", "roa_diff_qoq", "roa_std_4q", "nimy_std_4q",
    "liq_asset_ratio", "liq_dep_ratio", "ldr", "brokered_dep_ratio", "core_dep_ratio",
    "log_asset", "asset_growth_qoq", "asset_growth_yoy", "cap_zscore_q", "roa_zscore_q", "npl_zscore_q"
]


def estimate_empirical_cost_ratio(raw_dir: Path, out_dir: Path) -> float:
    fails = pl.read_parquet(raw_dir / "failures.parquet")
    df = (
        fails.select([
            pl.col("CERT").cast(pl.Int64, strict=False),
            pl.col("FAILDATE").cast(pl.String).str.strip_chars().alias("fdate"),
            pl.col("COST").cast(pl.Float64, strict=False),
            pl.col("QBFASSET").cast(pl.Float64, strict=False),
        ])
        .filter(
            pl.col("CERT").is_not_null()
            & (pl.col("fdate") <= "20071231")
            & pl.col("COST").is_not_null()
            & (pl.col("COST") >= 0)
            & pl.col("QBFASSET").is_not_null()
            & (pl.col("QBFASSET") > 0)
        )
        .with_columns((pl.col("COST") / pl.col("QBFASSET")).alias("loss_ratio"))
        .to_pandas()
    )

    if df.empty: raise ValueError('No valid development failure losses; cannot estimate cost ratio')
    q25, med, q75 = np.percentile(df["loss_ratio"], [25, 50, 75])
    mean_val = float(df["loss_ratio"].mean())
    implied_ratio = round(float(med / 0.005), 1)
    summary = pd.DataFrame([{
        "dev_failures_with_valid_cost": len(df),
        "loss_ratio_p25": round(float(q25), 4),
        "loss_ratio_median": round(float(med), 4),
        "loss_ratio_mean": round(mean_val, 4),
        "loss_ratio_p75": round(float(q75), 4),
        "assumed_exam_cost_pct_asset": 0.005,
        "cost_identification_note": "FDIC resolution loss measured; examination cost 0.5% of assets ASSUMED, not identified from FDIC",
        "empirical_cfn_cfp_ratio": implied_ratio,
    }])
    summary.to_csv(out_dir / "empirical_cost_estimation.csv", index=False)
    return implied_ratio


def quarterly_recall_at_top_k(df_eval: pd.DataFrame, prob_col: str, k_pct: float = 0.05) -> float:
    captured, total_pos = 0, 0
    for _, grp in df_eval.groupby("REPDTE"):
        y = grp["target_4q"].values
        p = grp[prob_col].values
        n_pos = int(y.sum())
        total_pos += n_pos
        if n_pos == 0:
            continue
        top_n = max(1, int(np.ceil(len(grp) * k_pct)))
        idx = np.argsort(-p)[:top_n]
        captured += int(y[idx].sum())
    return float(captured / total_pos) if total_pos > 0 else 0.0


def find_optimal_threshold(y_true: np.ndarray, y_prob: np.ndarray, cost_ratio: float) -> tuple[float, float]:
    # Candidate cutoffs span observed Development OOF probabilities, plus never/always alert.
    thresholds = np.unique(np.concatenate(([0.0], np.quantile(y_prob, np.linspace(0,1,501)), [1.0])))
    best_tau, best_cost = 0.05, float("inf")
    for tau in thresholds:
        pred = (y_prob >= tau).astype(int)
        fn = int(((y_true == 1) & (pred == 0)).sum())
        fp = int(((y_true == 0) & (pred == 1)).sum())
        cost = cost_ratio * fn + 1.0 * fp
        if cost < best_cost:
            best_cost = cost
            best_tau = float(tau)
    return best_tau, best_cost


def run_spark_mllib_demo(features_parquet: Path, feature_cols: list[str], out_dir: Path) -> None:
    try:
        from pyspark.sql import SparkSession
        import pyspark.sql.functions as F
        from pyspark.ml.feature import VectorAssembler
        from pyspark.ml.classification import LogisticRegression as SparkLR
        from pyspark.ml.evaluation import BinaryClassificationEvaluator

        t0 = time.perf_counter()
        spark = (
            SparkSession.builder.master("local[*]")
            .appName("FDIC-Spark-MLlib-Demo")
            .config("spark.driver.memory", "4g")
            .getOrCreate()
        )
        spark.sparkContext.setLogLevel("ERROR")

        sdf = spark.read.parquet(str(features_parquet)).filter(F.col("target_4q").isNotNull())
        sdf = sdf.withColumn("label", F.col("target_4q").cast("double"))

        assembler = VectorAssembler(inputCols=feature_cols, outputCol="features", handleInvalid="keep")
        assembled = assembler.transform(sdf).select("split", "label", "features")

        train_sp = assembled.filter(F.col("split") == "DEV")
        test_sp = assembled.filter(F.col("split") == "TEST")

        train_count = train_sp.count()
        test_count = test_sp.count()

        lr_sp = SparkLR(featuresCol="features", labelCol="label", maxIter=25, regParam=0.01)
        model_sp = lr_sp.fit(train_sp)
        preds = model_sp.transform(test_sp)

        pr_eval = BinaryClassificationEvaluator(labelCol="label", rawPredictionCol="rawPrediction", metricName="areaUnderPR")
        roc_eval = BinaryClassificationEvaluator(labelCol="label", rawPredictionCol="rawPrediction", metricName="areaUnderROC")

        pr_auc = float(pr_eval.evaluate(preds))
        roc_auc = float(roc_eval.evaluate(preds))
        elapsed = time.perf_counter() - t0
        spark.stop()

        res = pd.DataFrame([{
            "Engine_Model": "PySpark MLlib LogisticRegression",
            "Train_Rows": train_count,
            "Test_Rows": test_count,
            "Num_Features": len(feature_cols),
            "Test_PR_AUC": round(pr_auc, 4),
            "Test_ROC_AUC": round(roc_auc, 4),
            "EndToEnd_Runtime_s": round(elapsed, 2),
        }])
        res.to_csv(out_dir / "spark_mllib_demo.csv", index=False)
    except Exception as exc:
        pd.DataFrame([{"Status": f"SKIPPED: {exc}"}]).to_csv(out_dir / "spark_mllib_demo.csv", index=False)


def run_modeling_pipeline(pit_path: Path, raw_dir: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    emp_ratio = estimate_empirical_cost_ratio(raw_dir, out_dir)

    raw_df = build_raw_camels_features(pl.scan_parquet(str(pit_path))).collect().to_pandas()
    feat_cols = [c for c in BASE_FEATURES if c in raw_df.columns]

    dev_df = raw_df[(raw_df["split"] == "DEV") & (raw_df["target_4q"].notna())].copy().reset_index(drop=True)
    test_df = raw_df[(raw_df["split"] == "TEST") & (raw_df["target_4q"].notna())].copy().reset_index(drop=True)
    if (out_dir / "final_test_metrics.csv").exists():
        raise RuntimeError("Test results already exist. Archive old artifacts and deliberately remove them before a NEW frozen final test. Do not iterate on test results.")

    # 1. Expanding-Window Time-Series Cross-Validation on Development
    folds = [
        ("Fold 1 (Val: 1999-2002)", "19971231", "19990101", "20021231"),
        ("Fold 2 (Val: 2003-2005)", "20011231", "20030101", "20051231"),
        ("Fold 3 (Val: 2006-2007)", "20041231", "20060101", "20071231"),
    ]

    cv_rows = []
    oof_preds = []

    for fold_name, tr_end, val_start, val_end in folds:
        # Purged CV: four FULL calendar quarters between last train observation and val start.
        assert (pd.Period(val_start[:4]+'Q'+str((int(val_start[4:6])-1)//3+1), freq='Q') - pd.Period(tr_end[:4]+'Q'+str((int(tr_end[4:6])-1)//3+1),freq='Q')).n >= 5
        tr = dev_df[dev_df["REPDTE"] <= tr_end]
        va = dev_df[(dev_df["REPDTE"] >= val_start) & (dev_df["REPDTE"] <= val_end)].copy()

        prep = LeakageSafePreprocessor(feat_cols).fit(tr[feat_cols])
        X_tr = prep.transform(tr[feat_cols])
        y_tr = tr["target_4q"].astype(int).values
        X_va = prep.transform(va[feat_cols])
        y_va = va["target_4q"].astype(int).values

        lr = LogisticRegression(max_iter=500, C=0.5, random_state=42)
        lr.fit(X_tr, y_tr)
        va["prob_lr"] = lr.predict_proba(X_va)[:, 1]

        gbm = lgb.LGBMClassifier(
            n_estimators=300,
            learning_rate=0.03,
            num_leaves=31,
            subsample_for_bin=50000,
            colsample_bytree=0.8,
            subsample=0.8,
            min_child_samples=100,
            random_state=42,
            n_jobs=-1,
            verbose=-1,
        )
        gbm.fit(X_tr, y_tr)
        va["prob_lgb"] = gbm.predict_proba(X_va)[:, 1]
        oof_preds.append(va[["CERT", "REPDTE", "target_4q", "prob_lr", "prob_lgb"]])

        for m_name, p_col in [("Logistic Regression", "prob_lr"), ("LightGBM", "prob_lgb")]:
            cv_rows.append({
                "Fold": fold_name,
                "Model": m_name,
                "Val_Rows": len(va),
                "Val_Positives": int(y_va.sum()),
                "PR_AUC": round(float(average_precision_score(y_va, va[p_col])), 4),
                "ROC_AUC": round(float(roc_auc_score(y_va, va[p_col])), 4),
                "Recall_Top5Pct_Q": round(quarterly_recall_at_top_k(va, p_col, 0.05), 4),
                "Brier_Score": round(float(brier_score_loss(y_va, va[p_col])), 5),
            })

    cv_df = pd.DataFrame(cv_rows)
    cv_df.to_csv(out_dir / "dev_timeseries_cv.csv", index=False)

    # Optimize Cost-Sensitive Thresholds on Out-of-Fold Development Predictions
    oof_all = pd.concat(oof_preds, ignore_index=True)
    scenarios = [
        ("Conservative (10:1)", 10.0),
        (f"Loss-Informed Scenario ({emp_ratio:.0f}:1; assumed CFP)", emp_ratio),
        ("High Penalty (50:1)", 50.0),
    ]
    thresh_map = {}
    for sc_name, c_ratio in scenarios:
        tau_lgb, _ = find_optimal_threshold(oof_all["target_4q"].values, oof_all["prob_lgb"].values, c_ratio)
        tau_lr, _ = find_optimal_threshold(oof_all["target_4q"].values, oof_all["prob_lr"].values, c_ratio)
        thresh_map[sc_name] = {"cost_ratio": c_ratio, "tau_lgb": tau_lgb, "tau_lr": tau_lr}

    # Persist exact OOF threshold choices BEFORE touching test predictions.
    import json
    (out_dir / 'frozen_development_decisions.json').write_text(json.dumps({
        'folds':folds, 'thresholds':thresh_map, 'feature_cols':feat_cols,
        'assumed_exam_cost_asset_ratio':0.005, 'selection_source':'Development OOF only'
    },indent=2),encoding='utf-8')
    # 2. Fit Frozen Final Models on Full Development -> Evaluate ONCE on Test (2009Q1-2025Q2)
    final_prep = LeakageSafePreprocessor(feat_cols).fit(dev_df[feat_cols])
    X_dev = final_prep.transform(dev_df[feat_cols])
    y_dev = dev_df["target_4q"].astype(int).values
    X_test = final_prep.transform(test_df[feat_cols])
    y_test = test_df["target_4q"].astype(int).values

    final_lr = LogisticRegression(max_iter=500, C=0.5, random_state=42).fit(X_dev, y_dev)
    test_df["prob_lr"] = final_lr.predict_proba(X_test)[:, 1]

    final_lgb = lgb.LGBMClassifier(
        n_estimators=300,
        learning_rate=0.03,
        num_leaves=31,
        subsample_for_bin=50000,
        colsample_bytree=0.8,
        subsample=0.8,
        min_child_samples=100,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    ).fit(X_dev, y_dev)
    test_df["prob_lgb"] = final_lgb.predict_proba(X_test)[:, 1]

    # Save Feature Importances
    imp_df = pd.DataFrame({
        "feature": X_dev.columns,
        "lgb_gain_importance": final_lgb.booster_.feature_importance(importance_type="gain"),
        "lr_abs_coef": np.abs(final_lr.coef_[0]),
        "lr_coef": final_lr.coef_[0],
    }).sort_values("lgb_gain_importance", ascending=False)
    imp_df.to_csv(out_dir / "feature_importance.csv", index=False)

    # Save Calibration Curve
    cal_rows = []
    for m_name, p_col in [("Logistic Regression", "prob_lr"), ("LightGBM", "prob_lgb")]:
        prob_true, prob_pred = calibration_curve(y_test, test_df[p_col], n_bins=10, strategy="quantile")
        for pt, pp in zip(prob_true, prob_pred):
            cal_rows.append({"Model": m_name, "mean_predicted_prob": float(pp), "fraction_of_positives": float(pt)})
    pd.DataFrame(cal_rows).to_csv(out_dir / "test_calibration_curve.csv", index=False)

    # Final Test Metrics Table + Competing-Risk Sensitivity
    no_merger_mask = test_df["label_reason"] != "VALID_NON_FAILURE_EXIT"
    test_rows = []
    for subset_name, sub in [
        ("Full Test (2009Q1-2025Q2)", test_df),
        ("Sensitivity: Excl. Non-Failure Exits", test_df[no_merger_mask]),
    ]:
        yt = sub["target_4q"].astype(int).values
        for m_name, p_col in [("Logistic Regression", "prob_lr"), ("LightGBM", "prob_lgb")]:
            yp = sub[p_col].values
            test_rows.append({
                "Dataset": subset_name,
                "Model": m_name,
                "Rows": len(sub),
                "Positives": int(yt.sum()),
                "PR_AUC": round(float(average_precision_score(yt, yp)), 4),
                "ROC_AUC": round(float(roc_auc_score(yt, yp)), 4),
                "Recall_Top5Pct_Q": round(quarterly_recall_at_top_k(sub, p_col, 0.05), 4),
                "Recall_Top10Pct_Q": round(quarterly_recall_at_top_k(sub, p_col, 0.10), 4),
                "Brier_Score": round(float(brier_score_loss(yt, yp)), 5),
            })
    test_summary = pd.DataFrame(test_rows)
    test_summary.to_csv(out_dir / "final_test_metrics.csv", index=False)

    # Cost-Sensitive Decision Table on Test Set
    cost_rows = []
    for sc_name, info in thresh_map.items():
        c_ratio = info["cost_ratio"]
        for m_name, p_col, tau_key in [("Logistic Regression", "prob_lr", "tau_lr"), ("LightGBM", "prob_lgb", "tau_lgb")]:
            tau = info[tau_key]
            pred = (test_df[p_col].values >= tau).astype(int)
            tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
            captured_banks = test_df.loc[(y_test == 1) & (pred == 1), "CERT"].nunique()
            total_failed_banks = test_df.loc[y_test == 1, "CERT"].nunique()
            cost_rows.append({
                "Scenario": sc_name,
                "Model": m_name,
                "Frozen_Tau": round(tau, 4),
                "TP": int(tp),
                "FP": int(fp),
                "FN": int(fn),
                "Precision_Pct": round(tp / max(1, tp + fp) * 100, 2),
                "Recall_BankQ_Pct": round(tp / max(1, tp + fn) * 100, 2),
                "Unique_Banks_Captured": f"{captured_banks}/{total_failed_banks} ({captured_banks/total_failed_banks*100:.1f}%)",
                "Alert_Rate_Pct": round((tp + fp) / len(test_df) * 100, 2),
                "Expected_Cost_Units": round(c_ratio * fn + 1.0 * fp, 1),
            })
    cost_df = pd.DataFrame(cost_rows)
    cost_df.to_csv(out_dir / "test_cost_sensitive_decisions.csv", index=False)

    # Crisis Regime Diagnostic Breakdown on Test Set (LightGBM)
    regimes = [
        ("2009Q1-2014Q4 (GFC & Aftermath)", "20090101", "20141231"),
        ("2015Q1-2022Q4 (Low-Failure Expansion)", "20150101", "20221231"),
        ("2023Q1-2025Q2 (Regional Bank Stress)", "20230101", "20250630"),
    ]
    base_tau = thresh_map[f"Loss-Informed Scenario ({emp_ratio:.0f}:1; assumed CFP)"]["tau_lgb"]
    reg_rows = []
    for r_name, r_start, r_end in regimes:
        sub = test_df[(test_df["REPDTE"] >= r_start) & (test_df["REPDTE"] <= r_end)]
        yt = sub["target_4q"].astype(int).values
        yp = sub["prob_lgb"].values
        pred = (yp >= base_tau).astype(int)
        cap_b = sub.loc[(yt == 1) & (pred == 1), "CERT"].nunique()
        tot_b = sub.loc[yt == 1, "CERT"].nunique()
        reg_rows.append({
            "Regime": r_name,
            "Rows": len(sub),
            "Pos_BankQ": int(yt.sum()),
            "Unique_Failed_Banks": int(tot_b),
            "PR_AUC": round(float(average_precision_score(yt, yp)), 4),
            "ROC_AUC": round(float(roc_auc_score(yt, yp)), 4),
            "Recall_Top5Pct_Q": round(quarterly_recall_at_top_k(sub, "prob_lgb", 0.05), 4),
            "Banks_Captured_BaseTau": f"{cap_b}/{tot_b}",
        })
    reg_df = pd.DataFrame(reg_rows)
    reg_df.to_csv(out_dir / "test_regime_diagnostics.csv", index=False)
    # Distinct failed CERTs summed across regimes may exceed global total if bank-quarter
    # labels for the same failed CERT straddle two diagnostic regimes.
    regime_note = {
        'sum_regime_unique_failed_banks':int(reg_df['Unique_Failed_Banks'].sum()),
        'global_test_unique_failed_banks':int(test_df.loc[test_df.target_4q==1,'CERT'].nunique()),
        'counting_note':'Regime-level CERT counts are not additive across calendar boundaries.'}
    (out_dir/'regime_nonadditivity.json').write_text(__import__('json').dumps(regime_note,indent=2))

    # Sensitivity to avoidable share of the measured resolution loss.
    med_loss = float(pd.read_csv(out_dir/'empirical_cost_estimation.csv').iloc[0]['loss_ratio_median'])
    sensitivity=[]
    for avoidable in (0.10,0.25,0.50,1.00):
        for assumed_fp in (0.0025,0.005,0.01):
            sensitivity.append({'avoidable_loss_fraction_assumed':avoidable,
                                'exam_cost_as_fraction_assets_assumed':assumed_fp,
                                'implied_CFN_to_CFP':med_loss*avoidable/assumed_fp})
    pd.DataFrame(sensitivity).to_csv(out_dir/'cost_assumption_sensitivity.csv',index=False)

    test_df[["CERT", "REPDTE", "target_4q", "label_reason", "prob_lr", "prob_lgb"]].to_parquet(
        out_dir / "test_predictions.parquet", compression="zstd"
    )

    # 3. Run PySpark MLlib Distributed Workflow Demo
    run_spark_mllib_demo(Path("data_processed/features_pit.parquet"), list(X_dev.columns), out_dir)

    print("=== 1. EMPIRICAL COST ESTIMATION (DEV) ===")
    print(pd.read_csv(out_dir / "empirical_cost_estimation.csv").to_markdown(index=False))
    print("\n=== 2. DEVELOPMENT TIME-SERIES CV ===")
    print(cv_df.to_markdown(index=False))
    print("\n=== 3. FINAL TEST SET EVALUATION (2009Q1-2025Q2) ===")
    print(test_summary.to_markdown(index=False))
    print("\n=== 4. COST-SENSITIVE THRESHOLD DECISIONS (TEST) ===")
    print(cost_df.to_markdown(index=False))
    print("\n=== 5. TEST REGIME DIAGNOSTICS (LIGHTGBM) ===")
    print(reg_df.to_markdown(index=False))
    print("\n=== 6. TOP 10 FEATURES (LIGHTGBM GAIN) ===")
    print(imp_df.head(10).to_markdown(index=False))
    print("\n=== 7. PYSPARK MLLIB WORKFLOW DEMO ===")
    print(pd.read_csv(out_dir / "spark_mllib_demo.csv").to_markdown(index=False))


if __name__ == "__main__":
    run_modeling_pipeline(Path("data_processed/panel_pit.parquet"), Path("data_raw/fdic"), Path("artifacts/model"))
