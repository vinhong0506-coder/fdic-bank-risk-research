# Cross-Validation Feature Availability & Selection Leakage Audit

**Audit Date:** November 24, 2026
**Auditor:** Quantitative Risk Research & Reproducibility Audit Team
**Scope:** `src/fdic_pipeline/model.py`, `src/fdic_pipeline/features.py`, and Development Cross-Validation splits

---

## 1. Executive Summary & Review Findings

An independent reproducibility audit was conducted to evaluate whether feature availability in the historical cross-validation (CV) protocol was computed using future Development data, creating feature-selection lookahead leakage.

### Key Audit Findings:
1. **Feature Contract:** The pipeline defines an explicit contract of 30 candidate base financial indicators (`SELECTED_CAMELS_FEATURES` in `src/fdic_pipeline/features.py`), plus 30 explicit missingness flags (`_isna`), yielding 60 predictors.
2. **Published Selection Implementation:** In `model.py` (lines 157–170) and `features.py` (lines 239–254), feature availability was determined by checking whether each feature had at least one non-null value across the **entire labeled Development partition (1984Q1–2007Q4)** before executing the expanding-window time-series CV folds.
3. **Confirmed Material Difference in Fold 1:** Recomputing feature availability strictly on each fold's historical training partition reveals that in **Fold 1 (Train: 1984Q1–1997Q4)**, exactly **29 of 30 features** were available. The feature `nonperf_asset_ratio` had **0 valid observations (100.0% missing)** in Fold 1 Train.
4. **Root Cause:** `nonperf_asset_ratio` is calculated from FDIC Call Report items `P3ASSET` (loans past due 30–89 days), `P9ASSET` (loans past due 90+ days), and `NAASSET` (nonaccrual loans). In the FDIC Call Report panel, `P3ASSET` was only introduced in **2001Q1**. Because Polars evaluates `None + x + y` as `None`, `nonperf_asset_ratio` evaluates to `None` for all observations prior to 2001Q1.
5. **Impact on Model Scoring & Test Freeze:**
   - In Fold 1, `LeakageSafePreprocessor` received an all-null column and fell back to default parameters (`lo=0, hi=0, med=0, mean=0, std=1`), resulting in zero-valued inputs for `nonperf_asset_ratio` in training, while its missingness flag `_isna` was constant 1.0.
   - In Fold 2 (Train $\le$ 2001Q4) and Fold 3 (Train $\le$ 2004Q4), `nonperf_asset_ratio` was available in Train (37,760 and 146,120 valid observations, respectively).
   - In the **final frozen model** (trained on full Development 1984Q1–2007Q4 and evaluated on Test 2009Q1–2025Q2), `nonperf_asset_ratio` was available in Development (239,942 valid observations) and 100% available in Test. Therefore, the frozen Test predictions, out-of-time PR-AUC (`0.6682`), and supervisory threshold decisions ($\tau^* = 0.0201$) were not trained on an all-null feature.
   - However, the **historical CV model-selection evidence** contains feature-selection lookahead leakage in Fold 1. A strictly leakage-free fold-local pipeline would have selected 29 features in Fold 1 and 30 features in Folds 2 and 3.

---

## 2. Fold-by-Fold Feature Availability Comparison

The table below reports the empirical feature availability recomputed strictly from each partition's training window versus the published Development-wide feature set:

| Fold / Split | Training Horizon | Train Rows | Train-Only Features | Original Selected Features | Differences | Implication |
| :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **Fold 1** | 1984Q1–1997Q4 | 809,297 | **29 features** | 30 features | `nonperf_asset_ratio` missing in Train (0 valid rows, 0.00%) | **Feature selection leakage present:** Fold 1 peeked ahead into post-1997 data to include `nonperf_asset_ratio`. In training, preprocessor set fallback defaults (`std=1, mean=0`). Validation set (1999–2002) saw newly populated values in 2001–2002. |
| **Fold 2** | 1984Q1–2001Q4 | 965,816 | **30 features** | 30 features | Identical (0 differences) | `nonperf_asset_ratio` had 37,760 valid rows (3.91%) in Train (from 2001Q1–2001Q4). Identical feature set. |
| **Fold 3** | 1984Q1–2004Q4 | 1,074,176 | **30 features** | 30 features | Identical (0 differences) | `nonperf_asset_ratio` had 146,120 valid rows (13.60%) in Train. Identical feature set. |
| **Full Development (Final Train)** | 1984Q1–2007Q4 | 1,176,223 | **30 features** | 30 features | Identical (0 differences) | `nonperf_asset_ratio` had 239,942 valid rows (20.40%) in Full Dev. Valid for final model training. |
| **Held-Out Test** | 2009Q1–2025Q2 | 386,964 | N/A (Eval only) | 30 features | Identical (100% available) | Evaluated with frozen preprocessor parameters. |

---

## 3. Detailed Regulatory Accounting Breakdown: `nonperf_asset_ratio`

The mathematical expression for `nonperf_asset_ratio` in `src/fdic_pipeline/features.py` is:

$$\text{nonperf\_asset\_ratio} = \frac{\text{P3ASSET} + \text{P9ASSET} + \text{NAASSET}}{\text{ASSET}}$$

Where:
- `P3ASSET`: Loans and lease financing receivables past due 30 through 89 days and still accruing.
- `P9ASSET`: Loans and lease financing receivables past due 90 days or more and still accruing.
- `NAASSET`: Nonaccrual loans and lease financing receivables.

### Empirical Reporting Coverage in Call Report Panel:
- `P9ASSET` and `NAASSET`: Reported continuously from **1984Q1 to 2026Q2** (`1,601,076` non-null rows).
- `P3ASSET`: **First reported in 2001Q1** (`709,527` non-null rows). Prior to 2001Q1, `P3ASSET` is null for all institutions.
- Under standard IEEE floating-point and SQL addition semantics (`None + x + y = None`), the compound numerator is null whenever any component is null. Consequently:
  - 1984Q1–2000Q4: `nonperf_asset_ratio` is **100.0% null**.
  - 2001Q1–2007Q4: `nonperf_asset_ratio` is populated across all reporting commercial banks.

---

## 4. Leakage-Safe Fold-Local Selection Specification

To prevent future or cross-fold feature availability leakage, feature selection must be encapsulated within each fold's training step:

```python
def fold_local_feature_selection(df_train: pd.DataFrame, candidate_features: list[str]) -> list[str]:
    """Select active features strictly available within the fold-specific training partition."""
    return [
        col for col in candidate_features
        if col in df_train.columns and df_train[col].notna().any()
    ]
```

A unit test verifying this invariance property was added to `tests/test_fold_local_feature_selection.py`. The test confirms that perturbing future or validation feature availability has zero impact on the features selected within the training partition.

---

## 5. Research Conclusions & Disclosures

1. **Disclosure Requirement:** The academic report must transparently disclose that the historical 3-fold expanding cross-validation protocol selected feature availability across the full Development window, allowing `nonperf_asset_ratio` to enter Fold 1 where it was not yet historically reported.
2. **Integrity of Frozen Test Artifacts:** Because final model training used the complete Development set (1984Q1–2007Q4) where `nonperf_asset_ratio` was actively reported for 7 consecutive years (2001–2007), the frozen Test metrics (LightGBM AP = `0.6682`, ROC-AUC = `0.9861`, PR-AUC = `0.5699`) and supervisory loss decisions remain empirically reproducible and were not trained on an all-null column.
3. **Future Pipeline Recommendation:** Future releases should either recompute CV results with fold-local feature selection or define `nonperf_asset_ratio` using `coalesce(P3ASSET, 0) + P9ASSET + NAASSET` to ensure availability back to 1984.
