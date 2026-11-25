#!/usr/bin/env python3
"""FDIC EWS: fold-local feature-availability audit + guarded model.py patch.

Run from repository root with its pinned Python environment, for example:
    .\\.venv311\\Scripts\\python.exe scripts\\audit_fix_fdic_cv.py --mode all

This program deliberately NEVER calls run_modeling_pipeline, never fits a final
Development model, never reads Test predictions, and never writes frozen artifacts.
Results are a separate development-only sensitivity analysis, not replacement
for the previously frozen one-time Test evaluation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "fdic_pipeline" / "model.py"
PIT = ROOT / "data_processed" / "panel_pit.parquet"
FOLDS = [
    ("Fold 1 (Val: 1999-2002)", "19971231", "19990101", "20021231"),
    ("Fold 2 (Val: 2003-2005)", "20011231", "20030101", "20051231"),
    ("Fold 3 (Val: 2006-2007)", "20041231", "20060101", "20071231"),
]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for piece in iter(lambda: f.read(1024 * 1024), b""):
            h.update(piece)
    return h.hexdigest()


def json_dump(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def frozen_snapshot() -> dict[str, str]:
    """Record hashes of immutable model/Test decisions and official report files."""
    paths = []
    for folder in (
        ROOT / "artifacts/model_30feature_corrected",
        ROOT / "artifacts/model",
    ):
        paths.extend(folder / name for name in (
            "frozen_development_decisions.json",
            "final_test_metrics.csv",
            "test_cost_sensitive_decisions.csv",
            "test_predictions.parquet",
        ))
    paths.extend((ROOT / "deliverables").glob("*FDIC_EWS_SUBMISSION.*"))
    return {str(p.relative_to(ROOT)): digest(p) for p in paths if p.is_file()}


def columns_available(train: pd.DataFrame, candidates: list[str]) -> list[str]:
    """Select only observed features from the current Train partition."""
    cols = [col for col in candidates if col in train.columns and train[col].notna().any()]
    if not cols:
        raise RuntimeError("No usable features in this training fold")
    return cols


def threshold_fast(y_true: np.ndarray, proba: np.ndarray, ratio: float) -> tuple[float, float]:
    """Exact candidate grid and >= convention used by model.find_optimal_threshold.

    Searchsorted + prefix counts avoids 501 full array scans per scenario.
    Tie-breaking is the original ascending-threshold, first-minimum rule.
    """
    y = np.asarray(y_true, dtype=np.int8)
    p = np.asarray(proba, dtype=np.float64)
    if len(y) != len(p) or len(y) == 0 or not np.isfinite(p).all():
        raise ValueError("Invalid OOF arrays")
    if not (0 < ratio < float("inf")):
        raise ValueError("Expected positive finite cost ratio")
    candidates = np.unique(np.concatenate(([0.0], np.quantile(p, np.linspace(0, 1, 501)), [1.0])))
    order = np.argsort(p, kind="stable")
    p_sorted = p[order]
    cumul_pos = np.concatenate(([0], np.cumsum(y[order], dtype=np.int64)))
    total_pos = int(cumul_pos[-1])
    idx = np.searchsorted(p_sorted, candidates, side="left")
    fn = cumul_pos[idx]
    tp = total_pos - fn
    fp = len(y) - idx - tp
    costs = ratio * fn + fp
    best = int(np.argmin(costs))
    return float(candidates[best]), float(costs[best])


def load_cost_ratio(provided: float | None) -> tuple[float, str, dict | None]:
    """Derive cost ratio from saved Development policy evidence, not TEST."""
    frozen_candidates = [
        ROOT / "artifacts/model_30feature_corrected/frozen_development_decisions.json",
        ROOT / "artifacts/model/frozen_development_decisions.json",
    ]
    for path in frozen_candidates:
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for label, item in data.get("thresholds", {}).items():
            if "Loss-Informed" in label and "cost_ratio" in item:
                derived = float(item["cost_ratio"])
                if provided is not None and not np.isclose(derived, provided, rtol=0, atol=1e-6):
                    raise ValueError(f"Cost ratio conflict: CLI={provided}, {path}={derived}")
                return derived, str(path.relative_to(ROOT)), data
    csv_candidates = [
        ROOT / "artifacts/model_30feature_corrected/empirical_cost_estimation.csv",
        ROOT / "artifacts/model/empirical_cost_estimation.csv",
    ]
    for path in csv_candidates:
        if not path.is_file():
            continue
        with path.open(encoding="utf-8-sig", newline="") as handle:
            row = next(csv.DictReader(handle), None)
        if row and row.get("empirical_cfn_cfp_ratio"):
            derived = float(row["empirical_cfn_cfp_ratio"])
            if provided is not None and not np.isclose(derived, provided, rtol=0, atol=1e-6):
                raise ValueError(f"Cost ratio conflict: CLI={provided}, {path}={derived}")
            return derived, str(path.relative_to(ROOT)), None
    if provided is None:
        raise FileNotFoundError(
            "Missing Development cost evidence. Provide --cost-ratio only after "
            "checking the actual empirical_cost_estimation.csv or frozen policy JSON."
        )
    return float(provided), "user-supplied Development cost ratio", None



def _fit_lgbm_isolated(gbm, xtrain, ytrain, xval):
    import gc
    import os
    import pickle
    import subprocess
    import sys
    import uuid
    from pathlib import Path
    import numpy as np

    gc.collect()
    tmp_dir = Path("artifacts/cv_feature_selection_audit/_lgbm_npy_tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    uid = uuid.uuid4().hex
    xtr_p = tmp_dir / f"xtr_{uid}.npy"
    ytr_p = tmp_dir / f"ytr_{uid}.npy"
    xva_p = tmp_dir / f"xva_{uid}.npy"
    prm_p = tmp_dir / f"prm_{uid}.pkl"
    out_p = tmp_dir / f"out_{uid}.npy"
    try:
        np.save(xtr_p, np.ascontiguousarray(xtrain, dtype=np.float32))
        np.save(ytr_p, np.ascontiguousarray(ytrain, dtype=np.float64))
        np.save(xva_p, np.ascontiguousarray(xval, dtype=np.float32))
        with open(prm_p, "wb") as f:
            pickle.dump(gbm.get_params(), f, protocol=4)
        gc.collect()

        env = os.environ.copy()
        parts = [p for p in env.get("PATH", "").split(";") if p.strip()]
        env["PATH"] = ";".join(
            p for p in parts
            if not any(k in p.lower() for k in ("jdk", "java", "spark", "hadoop", "pyspark"))
        )
        env["OMP_NUM_THREADS"] = "1"
        env["OPENBLAS_NUM_THREADS"] = "1"
        env["MKL_NUM_THREADS"] = "1"
        env["NUMEXPR_NUM_THREADS"] = "1"

        worker = Path(__file__).resolve().parent / "_solo_lgbm_worker.py"
        proc = subprocess.run(
            [sys.executable, "-u", str(worker), str(xtr_p), str(ytr_p), str(xva_p), str(prm_p), str(out_p)],
            env=env,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Solo LightGBM worker failed with code {proc.returncode}")
        pred = np.load(out_p)
        gbm.predict_proba = lambda _X, _p=pred: np.column_stack([1.0 - _p, _p])
    finally:
        for p in (xtr_p, ytr_p, xva_p, prm_p, out_p):
            p.unlink(missing_ok=True)


def train_predict(train, valid, features):
    """Run LR locally; train LightGBM in a separate Python process."""
    import gc
    import os
    import subprocess
    import sys
    import tempfile
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from fdic_pipeline.features import LeakageSafePreprocessor

    prep = LeakageSafePreprocessor(features).fit(
        train[features]
    )

    X_train = prep.transform(train[features])
    X_valid = prep.transform(valid[features])

    y_train = train["target_4q"].astype(int).to_numpy()

    if len(np.unique(y_train)) != 2:
        raise ValueError("Training fold must contain both classes")

    # Original Logistic Regression configuration
    lr = LogisticRegression(
        max_iter=500,
        C=0.5,
        random_state=42
    )

    lr.fit(X_train, y_train)

    pred_lr = lr.predict_proba(X_valid)[:, 1].astype(
        np.float64
    )

    del lr
    gc.collect()

    scratch_root = (
        ROOT / "artifacts"
        / "cv_feature_selection_audit"
        / "worker_tmp"
    )

    scratch_root.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix="lgb_",
        dir=str(scratch_root)
    ) as td:

        td = Path(td)

        xt = td / "x_train.npy"
        yt = td / "y_train.npy"
        xv = td / "x_valid.npy"
        predpath = td / "pred.npy"

        # Save arrays to disk without keeping extra copies
        np.save(
            xt,
            X_train.to_numpy(
                dtype=np.float32,
                copy=False
            ),
            allow_pickle=False
        )

        np.save(
            xv,
            X_valid.to_numpy(
                dtype=np.float32,
                copy=False
            ),
            allow_pickle=False
        )

        np.save(
            yt,
            np.asarray(y_train, dtype=np.float64),
            allow_pickle=False
        )

        del X_train, X_valid, prep, y_train
        gc.collect()

        env = os.environ.copy()

        for k in (
            "OMP_NUM_THREADS",
            "OPENBLAS_NUM_THREADS",
            "MKL_NUM_THREADS",
            "NUMEXPR_NUM_THREADS",
        ):
            env[k] = "1"

        print(
            "  [ISOLATED] Launching LightGBM...",
            flush=True
        )

        proc = subprocess.run(
            [
                sys.executable,
                "-u",
                str(ROOT / "scripts/_fdic_lgb_worker.py"),
                str(xt),
                str(yt),
                str(xv),
                str(predpath),
            ],
            cwd=str(ROOT),
            env=env,
        )

        if proc.returncode != 0:
            raise RuntimeError(
                "LightGBM worker failed with exit code "
                + str(proc.returncode)
            )

        pred_lgb = np.load(
            predpath,
            allow_pickle=False
        ).astype(np.float64)

        if len(pred_lgb) != len(valid):
            raise RuntimeError(
                "LightGBM prediction count mismatch"
            )

    return {
        "lr": pred_lr,
        "lgb": pred_lgb
    }


def metric(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    from sklearn.metrics import average_precision_score, roc_auc_score
    return {"AP": float(average_precision_score(y, p)),
            "ROC_AUC": float(roc_auc_score(y, p))}


def compare_frame(fold: str, valid: pd.DataFrame, old: dict, new: dict, out: Path) -> list[dict]:
    y = valid["target_4q"].astype(int).to_numpy()
    rows = []
    for model in ("lr", "lgb"):
        a, b = old[model], new[model]
        delta = np.abs(a - b)
        old_metrics, new_metrics = metric(y, a), metric(y, b)
        rows.append({
            "fold": fold, "model": model,
            "val_rows": len(y), "positives": int(y.sum()),
            "AP_old": old_metrics["AP"], "AP_fixed": new_metrics["AP"],
            "AP_delta": new_metrics["AP"] - old_metrics["AP"],
            "ROC_old": old_metrics["ROC_AUC"], "ROC_fixed": new_metrics["ROC_AUC"],
            "ROC_delta": new_metrics["ROC_AUC"] - old_metrics["ROC_AUC"],
            "prob_mean_abs_diff": float(delta.mean()),
            "prob_max_abs_diff": float(delta.max()),
            "changed_probs_gt_1e_8": int((delta > 1e-8).sum()),
        })
    pred = valid[["CERT", "REPDTE", "target_4q"]].copy()
    pred.insert(0, "fold", fold)
    for model in ("lr", "lgb"):
        pred[f"{model}_old"] = old[model]
        pred[f"{model}_fixed"] = new[model]
    filename = fold.split(" ")[1]
    pred.to_csv(out / f"{filename}_validation_old_vs_fixed.csv", index=False)
    return rows


def build_report(out: Path, facts: dict, summaries: list[dict], thresholds: list[dict]) -> str:
    lines = [
        "# Fold-local feature selection: independent Development-only audit",
        "",
        f"Executed: {facts['created_at']}",
        f"Source model.py SHA-256 before patch: `{facts['source_model_sha256']}`",
        f"Input panel SHA-256: `{facts['pit_sha256']}`",
        f"Cost ratio: {facts['cost_ratio']} (source: `{facts['cost_ratio_source']}`)",
        "",
        "## Scope and safeguards",
        "",
        "- Old CV: feature availability selected across labeled Development.",
        "- Corrected CV: feature availability selected separately inside each fold's Train.",
        "- Both variants reuse the same CV periods, imputation logic, model constructors and seeds.",
        "- The final full-Development model was NOT fitted or changed.",
        "- No held-out Test predictions, metrics, thresholds or official deliverables were overwritten.",
        "- Old here means a **reproduction of current-source CV logic**; it is not automatically identical to archived published model artifacts.",
        "",
        "## Feature availability by fold",
        "",
        "| Fold | Train rows | Validation rows | Old feature count | Train-only feature count | Dropped features |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for x in facts["folds"]:
        lines.append(f"| {x['fold']} | {x['train_rows']:,} | {x['val_rows']:,} | {x['old_features']} | {x['train_only_features']} | {', '.join(x['dropped']) or 'None'} |")
    lines += ["", "## Model performance and prediction impact", "",
              "| Fold | Model | AP old | AP corrected | ΔAP | ROC old | ROC corrected | ΔROC | Mean |Δp| | Max |Δp| |",
              "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for x in summaries:
        lines.append(f"| {x['fold']} | {x['model']} | {x['AP_old']:.6f} | {x['AP_fixed']:.6f} | {x['AP_delta']:+.6f} | {x['ROC_old']:.6f} | {x['ROC_fixed']:.6f} | {x['ROC_delta']:+.6f} | {x['prob_mean_abs_diff']:.3g} | {x['prob_max_abs_diff']:.3g} |")
    lines += ["", "## OOF-based cost-sensitive thresholds (Development only)", "",
              "| Scenario | Model | Cost ratio | Old τ | Corrected τ | Δτ | Old OOF cost | Corrected OOF cost |",
              "|---|---|---:|---:|---:|---:|---:|---:|"]
    for x in thresholds:
        lines.append(f"| {x['scenario']} | {x['model']} | {x['cost_ratio']:.1f} | {x['tau_old']:.8f} | {x['tau_fixed']:.8f} | {x['tau_delta']:+.8f} | {x['oof_cost_old']:.1f} | {x['oof_cost_fixed']:.1f} |")
    lines += ["", "## Scientific interpretation", "",
              "Inspect the fold-specific deltas and OOF threshold differences before changing the report. ",
              "Any new threshold is a **post-audit Development-only sensitivity result**. It must not be described as the originally frozen pre-Test policy.",
              "The published Test metrics cannot be assumed to remain identical if the final model or its alert threshold is subsequently changed.",
              "The existing historical Test is already observed, so any post-audit policy re-evaluation must be disclosed transparently.",
              ""]
    return "\n".join(lines)


def audit(pit: Path, ratio_input: float | None, output_root: Path) -> tuple[Path, dict]:
    import gc
    import polars as pl
    from fdic_pipeline.features import build_raw_camels_features
    from fdic_pipeline.model import BASE_FEATURES

    if not pit.is_file():
        raise FileNotFoundError(f"PIT panel not found: {pit}")
    if not SRC.is_file():
        raise FileNotFoundError(f"model.py not found: {SRC}")
    if len(BASE_FEATURES) != 30:
        raise ValueError(f"Expected 30-feature contract, got {len(BASE_FEATURES)}. Inspect local branch before running.")
    source_txt = SRC.read_text(encoding="utf-8")
    if "fold_feat_cols = select_fold_available_features(tr, BASE_FEATURES)" in source_txt:
        raise RuntimeError("model.py already patched; audit must run against original current-source CV first. Use saved original backup for historical comparator.")

    cost_ratio, cost_source, frozen = load_cost_ratio(ratio_input)
    frozen_before = frozen_snapshot()
    print(f"[SAFEGUARD] Protecting {len(frozen_before)} frozen/official files by SHA-256", flush=True)
    np.random.seed(42)
    output_root.mkdir(parents=True, exist_ok=True)
    run_stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    out = output_root / f"run_{run_stamp}"
    out.mkdir(parents=False, exist_ok=False)
    print("[INFO] Output:", out, flush=True)
    print("[INFO] Historical benchmark source:", SRC, flush=True)
    print("[INFO] Development-only panel: <=20071231; no Test labels used", flush=True)

    # Reproduce the feature builder on observations through end-2007 only.
    # All feature operations for DEV are calendar-causal, including same-quarter peers.
    # Restricting the source to DEV reduces memory without using future Test features.
    lf = pl.scan_parquet(str(pit)).filter(pl.col("REPDTE") <= "20071231")
    feat = build_raw_camels_features(lf)
    needed = ["CERT", "REPDTE", "split", "target_4q"] + list(BASE_FEATURES)
    absent = [c for c in needed if c not in feat.collect_schema().names()]
    if absent:
        raise RuntimeError(f"Missing needed panel feature columns: {absent}")
    print("[INFO] Building Development feature frame (can use substantial RAM)...", flush=True)
    dev = feat.select(needed).collect().to_pandas()
    dev = dev.loc[(dev["split"] == "DEV") & dev["target_4q"].notna()].copy().reset_index(drop=True)
    del feat, lf
    gc.collect()
    if dev.empty:
        raise RuntimeError("No labeled Development observations")
    dev["target_4q"] = dev["target_4q"].astype(np.int8)
    if dev.duplicated(["CERT", "REPDTE"]).any():
        raise RuntimeError("Duplicate CERT/REPDTE keys in DEV")
    all_dev_feats = columns_available(dev, list(BASE_FEATURES))
    print(f"[INFO] Labeled Development: {len(dev):,} rows; old features: {len(all_dev_feats)}", flush=True)
    if len(all_dev_feats) != 30:
        raise RuntimeError(f"The local feature contract is not the expected 30 available features (got {len(all_dev_feats)}). Stop and review.")

    start = datetime.now().astimezone().isoformat(timespec="seconds")
    facts = {
        "created_at": start,
        "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
        "source_model_sha256": digest(SRC),
        "pit_sha256": digest(pit),
        "cost_ratio": cost_ratio,
        "cost_ratio_source": cost_source,
        "old_feature_cols": all_dev_feats,
        "folds": [],
        "does_not_use_test": True,
    }
    metrics = []
    old_oof = []
    new_oof = []

    for fold_name, train_end, val_start, val_end in FOLDS:
        tr = dev.loc[dev["REPDTE"] <= train_end]
        va = dev.loc[(dev["REPDTE"] >= val_start) & (dev["REPDTE"] <= val_end)]
        if tr.empty or va.empty:
            raise RuntimeError(f"Empty Train or Validation for {fold_name}")
        fold_cols = columns_available(tr, list(BASE_FEATURES))
        dropped = sorted(set(all_dev_feats) - set(fold_cols))
        facts["folds"].append({
            "fold":fold_name, "train_end":train_end, "val_start":val_start, "val_end":val_end,
            "train_rows":len(tr), "val_rows":len(va),
            "old_features":len(all_dev_feats), "train_only_features":len(fold_cols),
            "train_only_feature_names":fold_cols, "dropped":dropped,
        })
        print(f"\n[FOLD] {fold_name}: train={len(tr):,}, val={len(va):,}, old={len(all_dev_feats)}, fixed={len(fold_cols)}, dropped={dropped}", flush=True)
        print("  Original/old model...", flush=True)
        old_pred = train_predict(tr, va, all_dev_feats)
        if fold_cols == all_dev_feats:
            print("  Identical feature list: reuse the same fitted predictions for corrected comparison.", flush=True)
            new_pred = old_pred
        else:
            print("  Fold-local/corrected model...", flush=True)
            new_pred = train_predict(tr, va, fold_cols)
        metrics.extend(compare_frame(fold_name, va, old_pred, new_pred, out))
        part = va[["CERT", "REPDTE", "target_4q"]].copy()
        part.insert(0, "fold", fold_name)
        for name, container, sink in [("old", old_pred, old_oof), ("corrected", new_pred, new_oof)]:
            frame = part.copy()
            frame["prob_lr"] = container["lr"]
            frame["prob_lgb"] = container["lgb"]
            sink.append(frame)
        print("  Finished fold metrics:", [(m['model'],round(m['AP_old'],6),round(m['AP_fixed'],6)) for m in metrics[-2:]], flush=True)
        del old_pred, new_pred
        gc.collect()

    old = pd.concat(old_oof, ignore_index=True)
    fixed = pd.concat(new_oof, ignore_index=True)
    old.to_csv(out / "oof_original_current_code.csv", index=False)
    fixed.to_csv(out / "oof_corrected_fold_local.csv", index=False)
    pd.DataFrame(metrics).to_csv(out / "fold_model_comparison.csv", index=False)
    # Assert row-label identity, independent of using same row ordering.
    key_cols = ["fold", "CERT", "REPDTE", "target_4q"]
    if not old[key_cols].equals(fixed[key_cols]):
        raise RuntimeError("OOF row mismatch between old and corrected variants")
    scenarios = [("Conservative (10:1)", 10.0),
                 (f"Loss-Informed ({cost_ratio:g}:1)", cost_ratio),
                 ("High Penalty (50:1)", 50.0)]
    thresh = []
    for scenario, ratio in scenarios:
        for model in ("lr", "lgb"):
            tau_old, cost_old = threshold_fast(old["target_4q"].to_numpy(), old[f"prob_{model}"].to_numpy(), ratio)
            tau_fixed, cost_fixed = threshold_fast(fixed["target_4q"].to_numpy(), fixed[f"prob_{model}"].to_numpy(), ratio)
            thresh.append({
                "scenario":scenario, "model":model, "cost_ratio":ratio,
                "tau_old":tau_old, "tau_fixed":tau_fixed, "tau_delta":tau_fixed-tau_old,
                "oof_cost_old":cost_old, "oof_cost_fixed":cost_fixed,
                "oof_cost_delta":cost_fixed-cost_old,
            })
    pd.DataFrame(thresh).to_csv(out / "oof_threshold_comparison.csv", index=False)

    published = {}
    if frozen is not None:
        for sc_name, item in frozen.get("thresholds", {}).items():
            if "Loss-Informed" in sc_name:
                published = {"historical_saved_policy_label":sc_name,
                             "historical_tau_lr":item.get("tau_lr"),
                             "historical_tau_lgb":item.get("tau_lgb"),
                             "historical_feature_cols":frozen.get("feature_cols"),
                             "historical_note":"Saved policy may come from a different version of feature contract; compare before claiming reproduction."}
                break
    frozen_after = frozen_snapshot()
    if frozen_after != frozen_before:
        raise RuntimeError("Protected Test/report files changed during the audit. Stop and inspect.")
    facts["protected_files_sha256_unchanged"] = True
    facts["protected_file_hashes"] = frozen_before
    facts["historical_frozen_reference"] = published
    facts["comparison_metrics"] = metrics
    facts["threshold_comparison"] = thresh
    json_dump(out / "comparison_summary.json", facts)
    report_text = build_report(out, facts, metrics, thresh)
    (out / "audit_report.md").write_text(report_text, encoding="utf-8")
    # Public-safe aggregate evidence; no institution-level OOF rows are committed.
    evidence_dir = ROOT / "docs/evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    public_report = evidence_dir / f"cv_fold_local_impact_{run_stamp}.md"
    public_report.write_text(report_text, encoding="utf-8")
    print("[EVIDENCE] Public aggregate report:", public_report, flush=True)
    print("\n=== RESULT: FEATURE SELECTION / OOF THRESHOLDS ===")
    for row in thresh:
        if "Loss-Informed" in row["scenario"]:
            print(f"{row['model']:3s} original={row['tau_old']:.8f} fixed={row['tau_fixed']:.8f} delta={row['tau_delta']:+.8f}")
    if published:
        print("[REFERENCE] Saved historical frozen policy:", published)
    print("[PASS] Audit complete, no TEST was read/written; results:", out, flush=True)
    return out, facts


def patch_source(out: Path | None = None) -> tuple[Path, Path]:
    """Patch only fold-specific feature selection, never final training logic."""
    if not SRC.is_file():
        raise FileNotFoundError(SRC)
    original = SRC.read_text(encoding="utf-8")
    if "fold_feat_cols = select_fold_available_features(tr, BASE_FEATURES)" in original:
        print("[INFO] model.py already has fold-local selection; no second patch applied.")
        return SRC, Path("(already patched)")
    if "def select_fold_available_features(" in original:
        raise RuntimeError("Partial/alternative helper found; refusing automatic patch")
    if out is None or not (out / "comparison_summary.json").is_file():
        raise RuntimeError("Refusing patch without completed audit output")
    original_sha = json.loads((out / "comparison_summary.json").read_text(encoding="utf-8"))["source_model_sha256"]
    if digest(SRC) != original_sha:
        raise RuntimeError("model.py changed after audit. Rerun on matching source or resolve manually.")
    if "BASE_FEATURES = list(SELECTED_CAMELS_FEATURES)" not in original:
        raise RuntimeError("Current model source shape has changed; patch not applied")

    helper = '''\n\ndef select_fold_available_features(train_df: pd.DataFrame, candidates: list[str]) -> list[str]:
    """Choose feature availability strictly from this fold's training rows."""
    chosen = [c for c in candidates if c in train_df.columns and train_df[c].notna().any()]
    if not chosen:
        raise ValueError("No feature with observed values in the fold's Train")
    return chosen
'''
    updated = original.replace(
        "BASE_FEATURES = list(SELECTED_CAMELS_FEATURES)",
        "BASE_FEATURES = list(SELECTED_CAMELS_FEATURES)" + helper,
        1,
    )
    old_block = '''        prep = LeakageSafePreprocessor(feat_cols).fit(tr[feat_cols])
        X_tr = prep.transform(tr[feat_cols])
        y_tr = tr["target_4q"].astype(int).values
        X_va = prep.transform(va[feat_cols])'''
    new_block = '''        # Fold-local: no future Development/Validation availability may select a feature.
        fold_feat_cols = select_fold_available_features(tr, BASE_FEATURES)
        cv_fold_features[fold_name] = fold_feat_cols
        prep = LeakageSafePreprocessor(fold_feat_cols).fit(tr[fold_feat_cols])
        X_tr = prep.transform(tr[fold_feat_cols])
        y_tr = tr["target_4q"].astype(int).values
        X_va = prep.transform(va[fold_feat_cols])'''
    if updated.count(old_block) != 1:
        raise RuntimeError("Cannot find exact CV preprocessing block; no changes made")
    updated = updated.replace(old_block, new_block, 1)
    first = "    cv_rows = []\n    oof_preds = []"
    if updated.count(first) != 1:
        raise RuntimeError("Cannot locate CV init block; no changes made")
    updated = updated.replace(first, first + "\n    cv_fold_features = {}", 1)
    old_meta = "'assumed_exam_cost_asset_ratio':0.005, 'selection_source':'Development OOF only'"
    new_meta = "'assumed_exam_cost_asset_ratio':0.005,\n        'selection_source':'Fold-Train feature selection for CV; full Development for final model',\n        'cv_fold_feature_cols':cv_fold_features"
    if updated.count(old_meta) != 1:
        raise RuntimeError("Cannot locate frozen metadata block; no changes made")
    updated = updated.replace(old_meta, new_meta, 1)
    # Compile candidate before touching the user's research source.
    compile(updated, str(SRC), "exec")
    # Check all target paths before editing source: avoid half-completed changes.
    test = ROOT / "tests/test_cv_feature_local_guard.py"
    if test.exists():
        raise RuntimeError("Test file already exists; inspect it before patching model.py")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup_dir = out / "source_backup"
    backup_dir.mkdir(parents=True, exist_ok=False)
    backup = backup_dir / f"model_before_fold_fix_{timestamp}.py"
    shutil.copy2(SRC, backup)
    SRC.write_text(updated, encoding="utf-8", newline="\n")

    # Add a small integrated test tied to the actual model function.
    test.write_text('''"""Fold-local feature-selection guard: Validation data cannot select features."""
import pandas as pd
from fdic_pipeline.model import select_fold_available_features


def test_fold_local_ignores_validation_future_availability():
    train = pd.DataFrame({
        "cap_ratio": [0.08, 0.09, 0.12],
        "nonperf_asset_ratio": [float("nan")] * 3,
    })
    valid = pd.DataFrame({
        "cap_ratio": [0.1, 0.08],
        "nonperf_asset_ratio": [0.23, 0.04],
    })
    candidates = ["cap_ratio", "nonperf_asset_ratio"]
    first = select_fold_available_features(train, candidates)
    valid.loc[:, "nonperf_asset_ratio"] = [0.9, 0.9]
    second = select_fold_available_features(train, candidates)
    assert first == second == ["cap_ratio"]
''', encoding="utf-8", newline="\n")
    print("[PASS] model.py patch applied. Original saved:", backup)
    print("[PASS] Integrated pytest created:", test)
    return SRC, backup


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["audit", "all", "patch"], default="audit",
                        help="audit=old/new CV comparison, all=audit then guarded patch, patch=apply completed report")
    parser.add_argument("--pit", type=Path, default=PIT,
                        help="Input point-in-time panel (default data_processed/panel_pit.parquet)")
    parser.add_argument("--cost-ratio", type=float, default=None,
                        help="Optional Development-derived ratio; verified saved evidence takes precedence")
    parser.add_argument("--audit-dir", type=Path, default=ROOT / "artifacts/cv_feature_selection_audit")
    parser.add_argument("--completed-audit", type=Path, default=None,
                        help="Required for --mode patch; specific completed run_... directory")
    args = parser.parse_args()
    if Path.cwd().resolve() != ROOT.resolve():
        raise RuntimeError(f"Run from repository root: {ROOT}")
    if args.mode == "patch":
        if args.completed_audit is None:
            parser.error("--mode patch needs --completed-audit artifacts/cv_feature_selection_audit/run_...")
        patch_source(args.completed_audit.resolve())
        return 0

    # Fail fast if local model.py has been substantially changed by Antigravity.
    import fdic_pipeline.model as model
    if len(model.BASE_FEATURES) != 30:
        raise RuntimeError("Local model.py differs from verified 30-feature contract")
    result_dir, facts = audit(args.pit.resolve(), args.cost_ratio, args.audit_dir.resolve())
    if args.mode == "all":
        patch_source(result_dir)
    print("\n== NEXT ACTIONS ==")
    print("1) Read:", result_dir / "audit_report.md")
    print("2) Read:", result_dir / "oof_threshold_comparison.csv")
    if args.mode == "audit":
        print("3) After review, patch: --mode patch --completed-audit", result_dir)
    else:
        print("3) Run: .\\.venv311\\Scripts\\python.exe -m pytest -q")
        print("4) Inspect: git diff -- src/fdic_pipeline/model.py")
    print("DO NOT run full model.py or replace frozen TEST artifacts.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"\n[ERROR] {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        raise
