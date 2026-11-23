from pathlib import Path
import re, json, hashlib, traceback
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_curve, average_precision_score

ROOT = Path.cwd()
ART = ROOT / "artifacts"
OUT = ART / "figures_verified"
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.size": 10, "figure.dpi": 150})

status = []
def source(path):
    p = ROOT / path
    if not p.exists():
        raise FileNotFoundError(str(p))
    return p

def csv(path, cols):
    p = source(path)
    d = pd.read_csv(p)
    missing = set(cols) - set(d.columns)
    if missing:
        raise ValueError(f"{path}: missing {sorted(missing)}")
    return d

def save(name):
    for fig_no in plt.get_fignums():
        fig = plt.figure(fig_no)
        for ax in fig.axes:
            for container in ax.containers:
                if not hasattr(container, "patches"):
                    continue
                if not container.patches:
                    continue
                try:
                    labels = []
                    for bar in container.patches:
                        h = bar.get_height()
                        if h is None or h != h:
                            labels.append("")
                        elif abs(h) >= 100:
                            labels.append(f"{h:,.0f}")
                        else:
                            labels.append(f"{h:,.2f}")
                    ax.bar_label(
                        container,
                        labels=labels,
                        padding=3,
                        fontsize=8
                    )
                except (AttributeError, ValueError):
                    pass
    plt.tight_layout()
    plt.savefig(OUT / name, dpi=250, bbox_inches="tight")
    plt.close()

def run(number, name, fn):
    try:
        fn()
        status.append((number, "PASS", name, "New image created"))
        print(f"[PASS] Figure {number}: {name}", flush=True)
    except Exception as exc:
        plt.close("all")
        status.append((number, "FAIL", name, str(exc)))
        print(f"[FAIL] Figure {number}: {exc}", flush=True)

# Gather benchmark runs from CSV files and prior terminal logs.
def benchmark_data():
    frames = []
    for p in [
        ART / "benchmark/final/benchmark_runs_complete.csv",
        ART / "benchmark/final/benchmark_5x10x_backup.csv",
        ART / "benchmark/spark_stage3/benchmark_runs.csv",
        ART / "benchmark/final/benchmark_runs_all.csv",
    ]:
        if p.exists():
            d = pd.read_csv(p)
            if {"engine","scale","run","wall_seconds","rows"}.issubset(d):
                if "peak_process_tree_rss_mb" not in d:
                    d["peak_process_tree_rss_mb"] = np.nan
                frames.append(d)

    pat = re.compile(
        r"^\s*(pandas|polars|spark)\s+(\d+)x\s+run=(\d+):\s+"
        r"([\d.]+)s,\s+([\d.]+)MiB,\s+rows=(\d+)",
        re.M
    )
    rec = []
    for p in sorted((ROOT / "logs").glob("benchmark*.log")):
        text = p.read_text(encoding="utf-8", errors="replace")
        for m in pat.finditer(text):
            a,b,c,d,e,f = m.groups()
            rec.append(dict(
                engine=a, scale=int(b), run=int(c),
                wall_seconds=float(d),
                peak_process_tree_rss_mb=float(e),
                rows=int(f)
            ))
    if rec:
        frames.insert(0, pd.DataFrame(rec))

    if not frames:
        raise RuntimeError("No benchmark CSV or logs found")

    all_runs = pd.concat(frames, ignore_index=True)
    all_runs = all_runs.drop_duplicates(
        ["scale","engine","run"], keep="first"
    )
    all_runs["scale"] = all_runs["scale"].astype(int)
    all_runs["run"] = all_runs["run"].astype(int)

    summary = all_runs.groupby(
        ["scale","engine"], as_index=False
    ).agg(
        repeats=("run","nunique"),
        rows=("rows","first"),
        runtime_s=("wall_seconds","median"),
        rss_mib=("peak_process_tree_rss_mb","median")
    )

    (ART / "benchmark/final").mkdir(
        parents=True, exist_ok=True
    )
    all_runs.to_csv(
        ART / "benchmark/final/benchmark_runs_recovered.csv",
        index=False
    )
    summary.to_csv(
        ART / "benchmark/final/scaling_summary_recovered.csv",
        index=False
    )
    return summary

BENCH = benchmark_data()
print("\n=== RECOVERED BENCHMARK ===")
print(BENCH.to_string(index=False))

def fig1():
    d = csv(
        "artifacts/benchmark/storage_full/storage_benchmark.csv",
        ["format","bytes","write_s","read_s"]
    )
    fig, ax = plt.subplots(1,2,figsize=(11,4))
    ax[0].bar(d["format"],d["bytes"]/1048576)
    ax[0].set_title("Measured Storage Footprint")
    ax[0].set_ylabel("MiB")
    ax[1].plot(d["format"],d["read_s"],marker="o",label="Read")
    ax[1].plot(d["format"],d["write_s"],marker="s",label="Write")
    ax[1].legend()
    ax[1].set_title("Measured I/O Time")
    ax[1].set_ylabel("Seconds")
    for a in ax: a.tick_params(axis="x",rotation=15)
    save("fig1_storage_benchmark.png")

def fig2():
    d = csv(
        "artifacts/audit/capital_availability_by_year.csv",
        ["year","rbcrwa_zero_pct","rbc1_zero_pct"]
    )
    d["year"] = pd.to_numeric(d["year"],errors="raise")
    d = d.sort_values("year")
    plt.figure(figsize=(10,4))
    plt.plot(d["year"],d["rbcrwa_zero_pct"],label="RBCRWAJ zero %")
    plt.plot(d["year"],d["rbc1_zero_pct"],label="RBC1AAJ zero %")
    plt.xlabel("Year")
    plt.ylabel("Zero-value share (%)")
    plt.title("Capital Data Availability by Year")
    plt.legend()
    save("fig2_capital_regime_audit.png")

def fig3():
    d = csv(
        "artifacts/audit/temporal_split_summary.csv",
        ["split","Valid_Rows","Pos_BankQuarters"]
    )
    d = d.set_index("split").reindex(["DEV","EMBARGO","TEST"])
    if d["Valid_Rows"].isna().any():
        raise ValueError("Missing DEV/EMBARGO/TEST")
    rate = 100*d["Pos_BankQuarters"]/d["Valid_Rows"]
    fig,ax = plt.subplots(1,2,figsize=(10,4))
    ax[0].bar(d.index,d["Valid_Rows"])
    ax[0].set_title("Labeled Bank-Quarters")
    ax[0].set_ylabel("Rows")
    ax[1].bar(d.index,rate)
    ax[1].set_title("4-Quarter Failure Incidence")
    ax[1].set_ylabel("%")
    save("fig3_temporal_split_overview.png")

def fig4():
    d = BENCH[BENCH["scale"]==1].copy()
    if set(d["engine"]) != {"pandas","polars","spark"}:
        raise ValueError("1x benchmark incomplete")
    if (d["repeats"] < 3).any():
        raise ValueError("Fewer than 3 measured repeats")
    d = d.set_index("engine").loc[
        ["pandas","polars","spark"]
    ]
    fig,ax = plt.subplots(1,2,figsize=(10,4))
    ax[0].bar(d.index,d["runtime_s"])
    ax[0].set_title("Median Runtime, 1x")
    ax[0].set_ylabel("Seconds")
    ax[1].bar(d.index,d["rss_mib"])
    ax[1].set_title("Median Sampled Process-Tree RSS")
    ax[1].set_ylabel("MiB")
    save("fig4_engine_benchmark_1x.png")

def fig5():
    piv = BENCH.pivot(index="scale",columns="engine",values="runtime_s")
    mem = BENCH.pivot(index="scale",columns="engine",values="rss_mib")
    needed = [1,2,5,10]
    if not set(needed).issubset(piv.index):
        raise ValueError("Missing 1x/2x/5x/10x benchmark")
    if not {"pandas","polars","spark"}.issubset(piv.columns):
        raise ValueError("Missing engine")
    sub = piv.loc[needed]
    fig,ax = plt.subplots(1,2,figsize=(11,4))
    for engine in ["pandas","polars","spark"]:
        ax[0].plot(needed,sub[engine],marker="o",label=engine)
        ax[1].plot(needed,mem.loc[needed,engine],marker="o",label=engine)
    ax[0].set_title("Measured Runtime Scaling")
    ax[0].set_ylabel("Median Wall Time (s)")
    ax[1].set_title("Sampled Process-Tree RSS")
    ax[1].set_ylabel("MiB")
    for a in ax:
        a.set_xlabel("Synthetic Scale Factor")
        a.set_xticks(needed)
        a.legend()
    save("fig5_synthetic_scaling_10x.png")

def fig6():
    p = source("artifacts/model/test_predictions.parquet")
    d = pd.read_parquet(p)
    required = {"target_4q","prob_lr","prob_lgb"}
    if not required.issubset(d):
        raise ValueError("Missing prediction columns")
    if d["target_4q"].isna().any():
        raise ValueError("Test predictions contain censored rows")
    y = d["target_4q"].astype(int)
    if len(d)!=386964 or y.sum()!=1775:
        raise ValueError("Unexpected test population")
    fig,ax = plt.subplots(1,2,figsize=(11,4))
    for col,label in [
        ("prob_lr","Logistic Regression"),
        ("prob_lgb","LightGBM")
    ]:
        precision,recall,_ = precision_recall_curve(y,d[col])
        ap = average_precision_score(y,d[col])
        ax[0].plot(recall,precision,label=f"{label}: AP={ap:.4f}")
    ax[0].axhline(y.mean(),linestyle="--",color="gray")
    ax[0].set_xlabel("Recall")
    ax[0].set_ylabel("Precision")
    ax[0].set_title("Out-of-Sample Precision-Recall")
    ax[0].legend()

    c = csv(
        "artifacts/model/test_calibration_curve.csv",
        ["Model","mean_predicted_prob","fraction_of_positives"]
    )
    ax[1].plot([0,1],[0,1],linestyle="--",color="gray")
    for label,g in c.groupby("Model"):
        ax[1].plot(
            g["mean_predicted_prob"],
            g["fraction_of_positives"],
            marker="o",label=label
        )
    ax[1].set_xlabel("Mean Predicted Probability")
    ax[1].set_ylabel("Observed Failure Frequency")
    ax[1].set_title("Test Probability Calibration")
    ax[1].legend(fontsize=8)
    save("fig6_test_pr_and_calibration.png")

def fig7():
    d = csv(
        "artifacts/model/feature_importance.csv",
        ["feature","lgb_gain_importance"]
    )
    d = d.nlargest(10,"lgb_gain_importance").iloc[::-1]
    plt.figure(figsize=(9,5))
    plt.barh(d["feature"],d["lgb_gain_importance"])
    plt.xlabel("Total Gain")
    plt.title("Top 10 LightGBM Feature Importances")
    save("fig7_top10_camels_importance.png")

def fig8():
    c = csv(
        "artifacts/model/test_cost_sensitive_decisions.csv",
        ["Scenario","Model","Expected_Cost_Units"]
    )
    r = csv(
        "artifacts/model/test_regime_diagnostics.csv",
        ["Regime","Recall_Top5Pct_Q"]
    )
    costs = c.pivot_table(
        index="Scenario",
        columns="Model",
        values="Expected_Cost_Units",
        aggfunc="first"
    )
    fig,ax = plt.subplots(1,2,figsize=(13,5))
    costs.plot(kind="bar",ax=ax[0])
    ax[0].set_title("Illustrative Test Decision Costs")
    ax[0].set_ylabel("Assumed Cost Units")
    ax[0].tick_params(axis="x",rotation=25)
    ax[1].bar(range(len(r)),100*r["Recall_Top5Pct_Q"])
    ax[1].set_xticks(range(len(r)))
    ax[1].set_xticklabels(r["Regime"],rotation=25,ha="right")
    ax[1].set_ylabel("Recall@Top-5% (%)")
    ax[1].set_title("Test Recall by Regime")
    save("fig8_cost_and_regime_analysis.png")

for no,name,fn in [
    (1,"Storage",fig1),
    (2,"Capital",fig2),
    (3,"Temporal Split",fig3),
    (4,"Engine 1x",fig4),
    (5,"Scaling",fig5),
    (6,"Test PR & Calibration",fig6),
    (7,"CAMELS Importance",fig7),
    (8,"Cost & Regime",fig8)
]:
    run(no,name,fn)

audit = pd.DataFrame(
    status,columns=["figure","status","subject","detail"]
)
audit.to_csv(OUT/"figure_audit.csv",index=False)

print("\n=== FIGURE AUDIT ===")
print(audit.to_string(index=False))

old_dir = ART / "figures"
print("\n=== OLD VS NEW FIGURES ===")
for _,row in audit.iterrows():
    no = int(row["figure"])
    new = list(OUT.glob(f"fig{no}_*.png"))
    old = list(old_dir.glob(f"fig{no}_*.png")) if old_dir.exists() else []
    if new:
        n = new[0]
        print(f"FIG {no}: regenerated; new={n.stat().st_size} bytes")
        if old:
            print("  Old modification time:",
                  pd.Timestamp(old[0].stat().st_mtime,unit="s"))
            print("  New modification time:",
                  pd.Timestamp(n.stat().st_mtime,unit="s"))

print("\nPASS:",int((audit.status=="PASS").sum()),"/8")
if (audit.status=="PASS").all():
    print("ALL FIGURES REGENERATED: PASS")
else:
    print("INCOMPLETE: see figure_audit.csv for missing inputs")
