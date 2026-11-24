from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_curve, average_precision_score

root = Path.cwd()
model = root / "artifacts/model_30feature_corrected"
bench = root / "artifacts/stageC/final"
out = root / "artifacts/stageD/figures"

paths = {
    "storage": root / "artifacts/benchmark/storage_full/storage_benchmark.csv",
    "capital": root / "artifacts/audit/capital_availability_by_year.csv",
    "split": root / "artifacts/audit/temporal_split_summary.csv",
    "runs": bench / "benchmark_runs.csv",
    "summary": bench / "benchmark_summary.csv",
    "manifest": bench / "benchmark_manifest.json",
    "frozen": model / "frozen_development_decisions.json",
    "pred": model / "test_predictions.parquet",
    "calibration": model / "test_calibration_curve.csv",
    "importance": model / "feature_importance.csv",
    "cost": model / "test_cost_sensitive_decisions.csv",
    "regime": model / "test_regime_diagnostics.csv",
}

missing = [f"{key}: {path}" for key, path in paths.items()
           if not path.is_file()]
if missing:
    raise FileNotFoundError("Missing inputs:\n" + "\n".join(missing))

runs = pd.read_csv(paths["runs"])
scales = sorted(runs["scale"].astype(int).unique().tolist())
expected = {
    (e, s, r)
    for e in ("pandas", "polars", "spark")
    for s in (1, 2, 5)
    for r in (1, 2, 3)
}
observed = set(zip(
    runs.engine,
    runs.scale.astype(int),
    runs.run.astype(int)
))
assert scales == [1, 2, 5] and len(runs) == 27 and observed == expected

manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
assert manifest["completed_scales"] == [1, 2, 5]
assert manifest["completed_runs"] == 27

frozen = json.loads(paths["frozen"].read_text(encoding="utf-8"))
assert len(frozen["feature_cols"]) == 30

if out.exists() and any(out.glob("*.png")):
    raise RuntimeError(
        f"Output images already exist: {out}. Preserve before rerunning."
    )

out.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 160,
    "savefig.dpi": 200,
    "font.size": 9,
    "axes.grid": True,
    "grid.alpha": 0.20,
})

created = []

def save(fig, name):
    fig.tight_layout()
    fig.savefig(out / name, bbox_inches="tight")
    plt.close(fig)
    if (out / name).stat().st_size < 1000:
        raise RuntimeError(f"Invalid image: {name}")
    created.append(name)
    print("FIGURE PASS:", name, flush=True)

# Figure 1 - Storage
s = pd.read_csv(paths["storage"])
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
x = np.arange(len(s))
ax[0].bar(x, s["bytes"] / 2**20)
ax[0].set_xticks(x, s["format"], rotation=20)
ax[0].set_title("Storage size")
ax[0].set_ylabel("MiB")
ax[1].plot(x, s["read_s"], marker="o", label="Read")
ax[1].plot(x, s["write_s"], marker="s", label="Write")
ax[1].set_xticks(x, s["format"], rotation=20)
ax[1].set_title("Measured I/O time")
ax[1].set_ylabel("Seconds")
ax[1].legend()
save(fig, "fig1_storage_benchmark.png")

# Figure 2 - Capital field availability
cap = pd.read_csv(paths["capital"])
fig, ax = plt.subplots(figsize=(10, 4.2))
ax.plot(pd.to_numeric(cap["year"]), cap["rbc1_zero_pct"],
        label="RBC1AAJ: zero (%)")
ax.plot(pd.to_numeric(cap["year"]), cap["rbcrwa_zero_pct"],
        label="RBCRWAJ: zero (%)")
ax.set(
    title="Capital field availability audit",
    xlabel="Reporting year",
    ylabel="Zero share (%)"
)
ax.legend()
save(fig, "fig2_capital_regime_audit.png")

# Figure 3 - DEV / EMBARGO / TEST
sp = pd.read_csv(paths["split"])
sp = sp.set_index("split").reindex(["DEV", "EMBARGO", "TEST"])
assert sp[["Valid_Rows", "Pos_BankQuarters"]].notna().all().all()

rate = 100 * sp["Pos_BankQuarters"] / sp["Valid_Rows"]
fig, ax = plt.subplots(1, 2, figsize=(10, 4.1))
ax[0].bar(sp.index, sp["Valid_Rows"] / 1e6)
ax[0].set(title="Labeled observations",
          ylabel="Million bank-quarters")
ax[1].bar(sp.index, rate)
ax[1].set(title="4-quarter positive incidence",
          ylabel="Percent of labeled observations")
save(fig, "fig3_temporal_split_overview.png")

# Figure 4 - Benchmark at 1x
b = pd.read_csv(paths["summary"])
one = b.loc[b["scale"].eq(1)].set_index("engine").reindex(
    ["pandas", "polars", "spark"]
)
assert one["median_wall_seconds"].notna().all()

fig, ax = plt.subplots(1, 2, figsize=(10, 4.2))
ax[0].bar(one.index, one["median_wall_seconds"])
ax[0].set(title="1x median wall-clock (3 runs)",
          ylabel="Seconds")
ax[1].bar(one.index, one["median_peak_rss_mb"])
ax[1].set(title="1x median sampled process-tree RSS",
          ylabel="MiB")
save(fig, "fig4_engine_benchmark_1x.png")

# Figure 5 - Measured 1x, 2x, 5x only
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
for eng in ("pandas", "polars", "spark"):
    part = b[b["engine"].eq(eng)].sort_values("scale")
    assert part["scale"].tolist() == [1, 2, 5]
    ax[0].plot(part["rows"] / 1e6,
               part["median_wall_seconds"],
               marker="o", label=eng)
    ax[1].plot(part["rows"] / 1e6,
               part["median_peak_rss_mb"],
               marker="o", label=eng)

ax[0].set(
    title="Measured scaling (3-run medians)",
    xlabel="Million replicated bank-quarters",
    ylabel="Wall-clock seconds"
)
ax[1].set(
    title="Sampled process-tree RSS",
    xlabel="Million replicated bank-quarters",
    ylabel="MiB"
)
ax[0].legend()
ax[1].legend()
save(fig, "fig5_synthetic_scaling_5x.png")

# Figure 6 - Corrected Test PR and calibration
p = pd.read_parquet(paths["pred"])
y = p["target_4q"].astype(int).to_numpy()
assert len(y) == 386964 and y.sum() == 1775

cal = pd.read_csv(paths["calibration"])
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))

for name, col in (
    ("Logistic Regression", "prob_lr"),
    ("LightGBM", "prob_lgb"),
):
    z = p[col].to_numpy()
    precision, recall, _ = precision_recall_curve(y, z)
    ap = average_precision_score(y, z)
    ax[0].plot(recall, precision,
               label=f"{name} AP={ap:.4f}")

    sub = cal.loc[cal["Model"].eq(name)]
    assert len(sub) > 0
    ax[1].plot(sub["mean_predicted_prob"],
               sub["fraction_of_positives"],
               marker="o", label=name)

ax[0].axhline(y.mean(), linestyle=":",
              label=f"Prevalence {y.mean():.4f}")
ax[0].set(
    title="30-feature corrected Test PR curves",
    xlabel="Recall",
    ylabel="Precision"
)
ax[0].legend(fontsize=8)

ax[1].plot([0, 1], [0, 1], "k--",
           label="Perfect calibration")
ax[1].set(
    title="Test calibration (quantile bins)",
    xlabel="Mean predicted probability",
    ylabel="Observed failure rate"
)
ax[1].legend(fontsize=8)
save(fig, "fig6_test_pr_and_calibration.png")

# Figure 7 - Feature importance
imp = pd.read_csv(paths["importance"])
assert {"feature", "lgb_gain_importance"}.issubset(imp.columns)
top = imp.nlargest(10, "lgb_gain_importance").iloc[::-1]

fig, ax = plt.subplots(figsize=(10, 4.8))
ax.barh(top["feature"], top["lgb_gain_importance"])
ax.set(
    title="Top 10 LightGBM predictors (corrected model)",
    xlabel="Total gain"
)
save(fig, "fig7_top10_camels_importance.png")

# Figure 8 - Cost scenarios and regime recall
cost = pd.read_csv(paths["cost"])
reg = pd.read_csv(paths["regime"])
pivot = cost.pivot(
    index="Scenario",
    columns="Model",
    values="Expected_Cost_Units"
)
assert {"Logistic Regression", "LightGBM"}.issubset(pivot.columns)

fig, ax = plt.subplots(1, 2, figsize=(12, 4.7))
x = np.arange(len(pivot))
w = 0.36

for j, name in enumerate(("Logistic Regression", "LightGBM")):
    ax[0].bar(
        x + (j - .5) * w,
        pivot[name],
        width=w,
        label=name
    )

ax[0].set_xticks(x, pivot.index, rotation=17, ha="right")
ax[0].set(
    title="Development OOF-tuned cost scenarios (hypothetical)",
    ylabel="Scenario cost units"
)
ax[0].legend(fontsize=8)

ax[1].bar(range(len(reg)), reg["Recall_Top5Pct_Q"] * 100)
ax[1].set_xticks(
    range(len(reg)), reg["Regime"],
    rotation=17, ha="right"
)
ax[1].set(
    title="Test recall@Top5% by regime",
    ylabel="Percent"
)
save(fig, "fig8_cost_and_regime_analysis.png")

assert len(created) == 8

figure_manifest = {
    "status": "PASS",
    "figures": created,
    "source_model": str(model),
    "benchmark_scales": [1, 2, 5],
    "benchmark_runs": 27,
    "limitations": [
        "10x not measured",
        "Unknown exit adjudication remains open",
        "Hypothetical cost units are not observed supervisory savings"
    ]
}

(out.parent / "figures_manifest.json").write_text(
    json.dumps(figure_manifest, indent=2),
    encoding="utf-8"
)

print("\nSTAGE_D_FIGURES: PASS (8/8)")
print("OUTPUT:", out)
