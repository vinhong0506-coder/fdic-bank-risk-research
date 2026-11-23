from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_curve, roc_curve, average_precision_score, roc_auc_score

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.titleweight": "bold",
    "axes.grid": True,
    "grid.alpha": 0.25,
    "figure.dpi": 300,
})

fig_dir = Path("artifacts/figures")
fig_dir.mkdir(parents=True, exist_ok=True)

# Figure 1: Storage Benchmark (Size MB & Read/Write Time)
sb = pd.read_csv("artifacts/benchmark/storage_full/storage_benchmark.csv")
sb["Size_MB"] = sb["bytes"] / (1024 ** 2)
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
colors = ["#7f8c8d", "#3498db", "#1f618d", "#2ecc71"]
axes[0].bar(sb["format"], sb["Size_MB"], color=colors)
axes[0].set_title("A. Disk Footprint (1.68M Rows, MB)")
axes[0].set_ylabel("Size (MB)")
for i, v in enumerate(sb["Size_MB"]):
    axes[0].text(i, v + 8, f"{v:.1f} MB", ha="center", fontsize=8.5)

x = np.arange(len(sb))
w = 0.36
axes[1].bar(x - w/2, sb["write_s"], width=w, label="Write (s)", color="#e67e22")
axes[1].bar(x + w/2, sb["read_s"], width=w, label="Read (s)", color="#2980b9")
axes[1].set_xticks(x)
axes[1].set_xticklabels(sb["format"])
axes[1].set_title("B. Full-Scan I/O Latency (Seconds)")
axes[1].set_ylabel("Seconds (Lower is Better)")
axes[1].legend()
plt.tight_layout()
plt.savefig(fig_dir / "fig1_storage_benchmark.png", bbox_inches="tight")
plt.close()

# Figure 2: Structural Regime Shift in Regulatory Capital Ratios (1984-2026)
cap = pd.read_csv("artifacts/audit/capital_availability_by_year.csv")
fig, ax = plt.subplots(figsize=(9.5, 3.8))
ax.plot(cap["year"], cap["rbcrwa_zero_pct"], label="RBCRWAJ == 0 (%)", color="#c0392b", linewidth=2)
ax.plot(cap["year"], cap["rbc1_zero_pct"], label="RBC1AAJ == 0 (%)", color="#2980b9", linewidth=2, linestyle="--")
ax.axvline(1990, color="#2c3e50", linestyle=":", linewidth=1.5, label="Basel I Adoption (1990Q1)")
ax.set_title("Pre-Basel Structural Zero Audit in FDIC Capital Ratios (1984-2026)")
ax.set_xlabel("Reporting Year")
ax.set_ylabel("Zero-Value Share (%)")
ax.legend()
plt.tight_layout()
plt.savefig(fig_dir / "fig2_capital_regime_audit.png", bbox_inches="tight")
plt.close()

# Figure 3: Temporal Split & Embargo Architecture
sp = pd.read_csv("artifacts/audit/temporal_split_summary.csv")
fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
split_labels = ["Dev\n(1984Q1-2007Q4)", "Embargo\n(2008Q1-2008Q4)", "Test\n(2009Q1-2025Q2)"]
axes[0].bar(split_labels, sp["Valid_Rows"] / 1e6, color=["#2980b9", "#95a5a6", "#16a085"])
axes[0].set_title("A. Valid Bank-Quarter Observations (Millions)")
axes[0].set_ylabel("Observations (Millions)")
for i, v in enumerate(sp["Valid_Rows"] / 1e6):
    axes[0].text(i, v + 0.03, f"{v:.2f}M", ha="center", fontsize=8.5)

axes[1].bar(split_labels, sp["Failure_Rate_Pct"], color=["#2980b9", "#95a5a6", "#16a085"])
axes[1].set_title("B. 4-Quarter Failure Incidence Rate (%)")
axes[1].set_ylabel("Failure Rate (%)")
for i, v in enumerate(sp["Failure_Rate_Pct"]):
    axes[1].text(i, v + 0.03, f"{v:.3f}%", ha="center", fontsize=8.5)
plt.tight_layout()
plt.savefig(fig_dir / "fig3_temporal_split_overview.png", bbox_inches="tight")
plt.close()

# Figure 4: 3-Engine Benchmark (Pandas vs Polars vs PySpark at 1x)
eng = pd.read_csv("artifacts/benchmark/engine_benchmark_summary.csv")
fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.8))
e_colors = ["#7f8c8d", "#1f618d", "#d35400"]
axes[0].bar(eng["Engine"], eng["Median_Runtime_s"], color=e_colors)
axes[0].set_title("A. Median Runtime on 1.68M Rows (Seconds)")
axes[0].set_ylabel("Seconds (Lower is Better)")
for i, v in enumerate(eng["Median_Runtime_s"]):
    axes[0].text(i, v + 0.12, f"{v:.3f}s", ha="center", fontsize=8.5)

axes[1].bar(eng["Engine"], eng["Throughput_rows_s"] / 1e6, color=e_colors)
axes[1].set_title("B. Processing Throughput (Million Rows/sec)")
axes[1].set_ylabel("Million Rows / sec")
for i, v in enumerate(eng["Throughput_rows_s"] / 1e6):
    axes[1].text(i, v + 0.12, f"{v:.2f}M/s", ha="center", fontsize=8.5)
plt.tight_layout()
plt.savefig(fig_dir / "fig4_engine_benchmark_1x.png", bbox_inches="tight")
plt.close()

# Figure 5: Synthetic Scaling Curves (1x -> 10x)
sc = pd.read_csv("artifacts/benchmark/synthetic_scaling_benchmark.csv")
rows_m = sc["Rows"] / 1e6
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
axes[0].plot(rows_m, sc["Polars_Runtime_s"], marker="o", label="Polars (Lazy API)", color="#1f618d", linewidth=2)
axes[0].plot(rows_m, sc["Spark_Local_Runtime_s"], marker="s", label="PySpark (Local[*])", color="#d35400", linewidth=2)
axes[0].axvline(3.354, color="#7f8c8d", linestyle="--", label="Warm-JVM Crossover (~3.35M)")
axes[0].set_title("A. Execution Time Scaling (1x to 10x)")
axes[0].set_xlabel("Dataset Scale (Million Rows)")
axes[0].set_ylabel("Runtime (Seconds)")
axes[0].legend(fontsize=8.5)

axes[1].plot(rows_m, sc["Polars_Peak_RSS_MB"], marker="o", color="#8e44ad", linewidth=2)
axes[1].set_title("B. Polars Process Peak RSS Memory (MB)")
axes[1].set_xlabel("Dataset Scale (Million Rows)")
axes[1].set_ylabel("Peak RSS Memory (MB)")
for x_v, y_v in zip(rows_m, sc["Polars_Peak_RSS_MB"]):
    axes[1].text(x_v, y_v + 70, f"{y_v:.0f} MB", ha="center", fontsize=8)
plt.tight_layout()
plt.savefig(fig_dir / "fig5_synthetic_scaling_10x.png", bbox_inches="tight")
plt.close()

# Figure 6: Out-of-Sample Test Precision-Recall & Calibration Curves
preds = pd.read_parquet("artifacts/model/test_predictions.parquet")
yt = preds["target_4q"].astype(int).values
fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
for name, col, c in [("Logistic Regression", "prob_lr", "#2980b9"), ("LightGBM", "prob_lgb", "#c0392b")]:
    prec, rec, _ = precision_recall_curve(yt, preds[col])
    ap = average_precision_score(yt, preds[col])
    axes[0].plot(rec, prec, label=f"{name} (PR-AUC={ap:.4f})", color=c, linewidth=2)
axes[0].axhline(yt.mean(), color="#7f8c8d", linestyle=":", label=f"Baseline Prevalence ({yt.mean():.4f})")
axes[0].set_title("A. Test Set Precision-Recall Curve (2009Q1-2025Q2)")
axes[0].set_xlabel("Recall")
axes[0].set_ylabel("Precision")
axes[0].legend(fontsize=8.5)

cal = pd.read_csv("artifacts/model/test_calibration_curve.csv")
axes[1].plot([0, 0.35], [0, 0.35], "k--", linewidth=1, label="Perfect Calibration")
for name, c in [("Logistic Regression", "#2980b9"), ("LightGBM", "#c0392b")]:
    sub = cal[cal["Model"] == name]
    axes[1].plot(sub["mean_predicted_prob"], sub["fraction_of_positives"], marker="o", label=name, color=c)
axes[1].set_title("B. Test Set Probability Calibration (Deciles)")
axes[1].set_xlabel("Mean Predicted Failure Probability")
axes[1].set_ylabel("Observed Failure Fraction")
axes[1].legend(fontsize=8.5)
plt.tight_layout()
plt.savefig(fig_dir / "fig6_test_pr_and_calibration.png", bbox_inches="tight")
plt.close()

# Figure 7: Top 10 CAMELS Feature Importances (LightGBM Gain)
imp = pd.read_csv("artifacts/model/feature_importance.csv").head(10).iloc[::-1]
fig, ax = plt.subplots(figsize=(8.5, 4.2))
ax.barh(imp["feature"], imp["lgb_gain_importance"] / 1000.0, color="#1f618d")
ax.set_title("Top 10 Point-in-Time CAMELS Predictors (LightGBM Split Gain)")
ax.set_xlabel("Total Split Gain (Thousands)")
plt.tight_layout()
plt.savefig(fig_dir / "fig7_top10_camels_importance.png", bbox_inches="tight")
plt.close()

# Figure 8: Cost-Sensitive Expected Supervisory Cost & Crisis Regime Capture
cost_df = pd.read_csv("artifacts/model/test_cost_sensitive_decisions.csv")
reg_df = pd.read_csv("artifacts/model/test_regime_diagnostics.csv")
fig, axes = plt.subplots(1, 2, figsize=(10.5, 4))
scenarios = cost_df["Scenario"].unique()
x = np.arange(len(scenarios))
w = 0.35
lr_costs = cost_df[cost_df["Model"] == "Logistic Regression"]["Expected_Cost_Units"].values
lgb_costs = cost_df[cost_df["Model"] == "LightGBM"]["Expected_Cost_Units"].values
axes[0].bar(x - w/2, lr_costs / 1000.0, width=w, label="Logistic Regression", color="#2980b9")
axes[0].bar(x + w/2, lgb_costs / 1000.0, width=w, label="LightGBM", color="#c0392b")
axes[0].set_xticks(x)
axes[0].set_xticklabels(scenarios, fontsize=8.5)
axes[0].set_title("A. Expected Supervisory Cost on Test (Thousands)")
axes[0].set_ylabel("Expected Cost Units (Thousands)")
axes[0].legend(fontsize=8.5)

axes[1].bar(["2009-2014\n(GFC)", "2015-2022\n(Expansion)", "2023-2025Q2\n(Regional Stress)"],
            reg_df["Recall_Top5Pct_Q"] * 100, color=["#16a085", "#2980b9", "#e67e22"])
axes[1].set_title("B. LightGBM Quarterly Recall@Top-5% by Regime")
axes[1].set_ylabel("Quarterly Recall@Top-5% (%)")
for i, v in enumerate(reg_df["Recall_Top5Pct_Q"] * 100):
    axes[1].text(i, v + 1.5, f"{v:.1f}%", ha="center", fontsize=8.5)
plt.tight_layout()
plt.savefig(fig_dir / "fig8_cost_and_regime_analysis.png", bbox_inches="tight")
plt.close()

print("Generated all 8 publication-grade figures in artifacts/figures/:")
for f in sorted(fig_dir.glob("*.png")):
    print(" -", f.name)
