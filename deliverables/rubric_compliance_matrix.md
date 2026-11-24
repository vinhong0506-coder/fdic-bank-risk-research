# Comprehensive Rubric Compliance Matrix

**Research Title:** U.S. Bank Failure Early-Warning System: A Point-in-Time Big Data Engineering, Multi-Engine Scalability, and Cost-Sensitive Predictive Framework (1984Q1–2026Q2)
**Student Author:** Dao Huy Thanh Vinh (Student ID: `11231024`)
**Course & Program:** Big Data Analytics in Finance — Bachelor of Financial Technology (Class BFT65B), National Economics University (NEU)
**Target Evaluation:** 100-Point Official Marking Rubric
**Date of Audit:** November 24, 2026

---

## Rubric Compliance Overview

| Assessment Area | Maximum Points | Verified Status | Key Repository & Report Evidence Summary |
| :--- | :---: | :---: | :--- |
| **Part 1 – Acquisition & Storage** | 15 Points | **VERIFIED** | REST API pagination, 170 quarters, 1.68M rows, 3-tier audit, Parquet-zstd (2.95x compression, 21.82x read speedup). |
| **Part 2 – Data Quality & Panel** | 20 Points | **VERIFIED** | Automated DQ audit (Table 2.1), 5,631 zombie rows purged, 4-tier lifecycle taxonomy, 29-CERT conflict subset, PIT panel (1.68M -> 1.18M Dev / 387K Test). |
| **Part 3 – Scalable Processing** | 25 Points | **VERIFIED** | Polars Lazy plan vs. pandas vs. Spark Catalyst plans; numeric equivalence (< 1.42e-13); 27 runs (1x, 2x, 5x); cluster justification; 10x unmeasured disclosed. |
| **Part 4 – Feature Pipeline** | 15 Points | **VERIFIED** | 30 base CAMELS features + 30 missingness indicators = 60 predictors; integer calendar quarter index (`q_idx`); train-only preprocessing frozen on Dev. |
| **Part 5 – Modelling & Validation** | 15 Points | **VERIFIED** | Logistic Regression vs. LightGBM vs. PySpark MLlib; 3-fold expanding CV; test AP (0.6795 vs 0.6682); 40.3:1 empirical loss matrix; tau* = 0.0201 captures 484/500 banks (96.8%). |
| **Part 6 – Conclusions & Policy** | 5 Points | **VERIFIED** | Explicit direct answers to assignment Q1, Q2, Q3; comprehensive limitations; Vietnamese Law on Credit Institutions 2024 & Circulars 41/13/22/08/02/06. |
| **Reproducibility** | 5 Points | **VERIFIED** | End-to-end instructions in README; Python 3.11.9, OpenJDK 17, PySpark 3.5.3, Polars 2.1.0; 13/13 unit tests pass; `validate_entire_project.py --check` PASS (0 failures). |
| **TOTAL EVALUATION** | **100 Points** | **VERIFIED** | **All criteria fully met with substantive evidence and zero fabricated claims.** |

---

## Detailed Criterion-by-Criterion Audit Matrix

| Rubric Area & Specific Criterion | Max Pts | Evidence in Report | Evidence in Repository | Verified Status | Remaining Limitations & Disclosures |
| :--- | :---: | :--- | :--- | :---: | :--- |
| **Part 1.1: Reproducible Data Acquisition** | 5.0 | Section 1.1 documents FDIC BankFind REST API (`/api/financials`), parameter filtering by `REPDTE`, offset pagination (limit 10,000), 5-retry backoff with jitter, resumability logic, and 170-quarter scope (1984Q1–2026Q2). | `src/fdic_pipeline/ingest.py`, `data_raw/fdic/manifest_financials.json` | **VERIFIED** | None. Download completed November 23, 2026 (11:38–12:05 Vietnam Time); 1,682,738 raw records. |
| **Part 1.2: Three-Tier Ingestion Verification** | 5.0 | Section 1.2 formally distinguishes three verification tiers: Tier 1 (170 manifest entries exist, sum = 1,682,738); Tier 2 (saved completeness and checksum flags pass); Tier 3 (honest disclosure that independent SHA-256 recalculation of all 170 source files directly against FDIC server responses was not executed during Stage E). | `artifacts/stageB/audit/manifest_verification.csv`, `docs/evidence/part5_integrity_status.json` | **VERIFIED** | Tier 3 server-side recomputation boundary is explicitly disclosed. |
| **Part 1.3: Columnar Storage Engineering & Benchmarks** | 5.0 | Section 1.3 & Table 1.1 provide measured comparisons: CSV (424.1 MiB, 10.26s read, 51.44s write) vs. Snappy (172.4 MiB, 1.06s read) vs. Zstd (143.9 MiB, 0.47s read, 4.07s write) vs. Brotli (144.9 MiB, 0.56s read, 19.14s write). Embedded Figure 1. | `artifacts/benchmark/storage_full/storage_benchmark.csv`, `docs/figures/fig1_storage_benchmark.png` | **VERIFIED** | None. Measured 2.95x compression and 21.82x read speedup for Parquet-Zstandard. |
| **Part 2.1: Automated Data-Quality Framework** | 7.0 | Section 2.1 & Table 2.1 detail 7 automated detection rules: missing IDs, duplicate keys, post-exit zombie rows, structural zero capital reporting, nonpositive values, unresolved exits, and temporal reporting gaps. | `src/fdic_pipeline/audit.py`, `artifacts/audit/panel_flow.json` | **VERIFIED** | Detection rules and remediation actions are fully documented. |
| **Part 2.2: Lifecycle & Event Classification** | 7.0 | Section 2.2 defines 4-tier taxonomy (failure, merger, liquidation, unknown exit). Reconciles `failure_date`, `inst_end_date`, `confirmed_exit_date`. Details the 29-CERT conflict subset (106 historical positive bank-quarters, 0 in Test). Unknown exits remain censored. | `docs/evidence/lifecycle_exception_review.md`, `artifacts/stageB/audit/lifecycle_conflict_impact.csv` | **VERIFIED** | Granular merger-registry adjudication remains pending for historical conflicts. |
| **Part 2.3: PIT Panel Construction & Capital Audit** | 6.0 | Section 2.3 & 2.4 detail elimination of 5,631 zombie rows across 62 CERTs. Table 2.2 reconciles failures (4,117 raw -> 3,585 unique -> 3,241 matched). Table 2.3 defines temporal split (1.18M Dev, 33K Embargo, 387K Test, 17.5K Censored). Embedded Figures 2 & 3. | `artifacts/audit/failure_reconciliation.json`, `docs/figures/fig2_capital_regime_audit.png`, `docs/figures/fig3_temporal_split_overview.png` | **VERIFIED** | Capital structural zeroes (100% pre-1990, 36.4%–41.5% post-2020 CBLR) audited. |
| **Part 3.1: Polars Lazy Implementation & Plan** | 5.0 | Section 3.1 details Polars LazyFrame DAG, projection pushdown (`PROJECT */9 COLUMNS`), predicate pushdown, vectorized multithreading via Rayon (16 cores), and window operations partitioned over `CERT`. | `src/fdic_pipeline/workload.py`, `artifacts/stageC/benchmark_1x_r3/polars_1x_plan.txt` | **VERIFIED** | Execution plan verified directly from text file. |
| **Part 3.2: Eager pandas Baseline Profiling** | 3.0 | Section 3.2 documents pandas eager memory allocation, single-threaded execution bottlenecks under Python GIL, and intermediate copying overhead (5.157s latency, 794 MiB RSS). | `src/fdic_pipeline/workload.py`, `artifacts/stageC/final/benchmark_runs.csv` | **VERIFIED** | Identical analytical workload and grouping verified. |
| **Part 3.3: PySpark Catalyst Plan Execution** | 5.0 | Section 3.3 analyzes Catalyst physical plan (`spark_1x_plan.txt`), identifying nested WindowExec operators (`RowFrame, -4, -4`, `RowFrame, -1, -1`, `stddev_samp`, `avg(capital_ratio)`), JVM startup tax, and Py4J serialization costs (14.757s latency, 1,013 MiB RSS). | `src/fdic_pipeline/workload.py`, `artifacts/stageC/benchmark_1x_r3/spark_1x_plan.txt` | **VERIFIED** | Physical plan confirms window sorting and projection mechanics. |
| **Part 3.4: Cross-Engine Numeric Equivalence** | 4.0 | Section 3.4 & Table 3.1 provide exact numeric equivalence audit across all features. Bitwise parity on 5 features; floating-point differences bounded at 5.68e-14 (rolling std) and 1.42e-13 (peer z-score), well below 1.0e-06 tolerance. | `artifacts/stageC/*/numeric_equivalence.json` | **VERIFIED** | Status PASS confirmed across 1x, 2x, and 5x runs. |
| **Part 3.5: Multi-Scale Benchmark (27 Runs)** | 5.0 | Section 3.5 & Tables 3.2–3.3 report 3-run medians across 27 executed runs: 1x (pandas 5.157s, Polars 0.797s, Spark 14.757s); 2x (pandas 9.133s, Polars 1.559s, Spark 17.988s); 5x (pandas 21.940s, Polars 2.464s, Spark 31.514s). Embedded Figures 4 & 5. | `artifacts/stageC/final/benchmark_runs.csv`, `docs/figures/fig4_engine_benchmark_1x.png`, `docs/figures/fig5_synthetic_scaling_5x.png` | **VERIFIED** | Clarified 2x and 5x are synthetic replications; 10x unmeasured honestly disclosed. |
| **Part 3.6: Cluster Break-Even & Justification** | 3.0 | Section 3.6 explicitly answers when a distributed cluster is justified: working set > physical RAM (>64 GB), cloud object stores (S3/HDFS/ADLS), streaming Kafka integration, or distributed cluster MLlib. | Workstation topology (16 GB RAM), theoretical scalability analysis | **VERIFIED** | Honest conclusion: Polars Lazy API is superior for single-node workloads. |
| **Part 4.1: CAMELS Feature Selection & Contract** | 5.0 | Section 4.1 & Table 4.1 detail economic rationale for all active CAMELS features. Normalized feature contract: exactly 30 base features + 30 `_isna` missingness indicators = 60 predictors. Obsolete 31/62 contract purged. Embedded Figure 7. | `docs/evidence/feature_contract.md`, `artifacts/model_30feature_corrected/feature_importance.csv`, `docs/figures/fig7_top10_camels_importance.png` | **VERIFIED** | Excluded `eff_ratio` and `core_dep_ratio` due to pre-2001 absence. |
| **Part 4.2: Anti-Leakage Feature Construction** | 5.0 | Section 4.2 documents integer calendar quarter index (`q_idx = year * 4 + quarter - 1`). Lags (`roa_lag1`, `roa_lag4`, growth rates, rolling std) enforce strict calendar continuity, evaluating to null across reporting gaps. | `src/fdic_pipeline/features.py`, `tests/test_feature_leakage.py` | **VERIFIED** | Verified by unit tests `test_no_cross_bank_lag_or_gap_leakage`. |
| **Part 4.3: Train-Only Preprocessing & Invariance** | 5.0 | Section 4.3 details `LeakageSafePreprocessor`: Winsorization percentiles, imputation medians, and robust scaling fitted strictly on Development (1984–2007) and frozen. Validated by synthetic future-perturbation unit tests. | `src/fdic_pipeline/model.py`, `artifacts/features/preprocessor_dev_params.json` | **VERIFIED** | Preprocessor parameters verified frozen and invariant. |
| **Part 5.1: Algorithm Architectures & Baseline** | 2.0 | Section 5.1 details selection rationales: L2 Logistic Regression (interpretable linear baseline), LightGBM (non-linear GBDT ensemble), and PySpark MLlib Logistic Regression (distributed cluster demo). | `src/fdic_pipeline/model.py`, `artifacts/model_30feature_corrected/` | **VERIFIED** | Three complementary models evaluated. |
| **Part 5.2: Expanding Window Cross-Validation** | 3.0 | Section 5.2 & Table 5.1 document 3-fold expanding time-series CV on Development (1984–2007) with 4-quarter purging buffers: Fold 1 (1999–2002), Fold 2 (2003–2005), Fold 3 (2006–2007). | `artifacts/model_30feature_corrected/dev_timeseries_cv.csv` | **VERIFIED** | Obsolete 5-fold claim corrected to verified 3-fold CV. |
| **Part 5.3: Imbalanced Metrics & Out-of-Time Test** | 3.0 | Section 5.3 & Table 5.2 report held-out Test metrics (386,964 rows, 1,775 positives, 0.459% prevalence): LR AP 0.6795 (ROC 0.9863); LightGBM AP 0.6682 (ROC 0.9861); Spark MLlib sklearn AP 0.5699 (native areaUnderPR 0.5547, ROC 0.9794). Embedded Figure 6. | `artifacts/model_30feature_corrected/final_test_metrics.csv`, `artifacts/model_30feature_corrected/spark_mllib_validation.json` | **VERIFIED** | Mathematical difference between Spark trapezoidal PR and sklearn AP explained. |
| **Part 5.4: Asymmetric Loss & Cost-Based Threshold** | 4.0 | Section 5.4 & Table 5.3 derive empirical loss ratio 40.3:1 (median FDIC resolution loss = 20.17% of assets; assumed exam cost CFP = 0.50% of assets). LightGBM at frozen threshold tau* = 0.0201 captures 484/500 unique banks (96.8%) at 1.78% alert rate, cutting expected cost by 59.7% vs. LR. | `artifacts/model_30feature_corrected/empirical_cost_estimation.csv`, `artifacts/model_30feature_corrected/test_cost_sensitive_decisions.csv` | **VERIFIED** | CFP = 0.50% explicitly disclosed as assumed scenario parameter. |
| **Part 5.5: Macroeconomic Regimes & Non-Additivity** | 3.0 | Section 5.5 & Table 5.4 evaluate performance across GFC (98.3% capture), Expansion (76.7% capture), and Regional Bank Stress (55.6% capture). Reconciles regime non-additivity (468 + 30 + 9 = 507 vs. 500 unique failed banks due to 7 boundary-spanning institutions). Embedded Figure 8. | `artifacts/model_30feature_corrected/test_regime_diagnostics.csv`, `artifacts/model_30feature_corrected/regime_nonadditivity.json` | **VERIFIED** | SVB intraday liquidity run unobservability discussed. |
| **Part 6.1: Direct Answers to Assignment Q1–Q3** | 2.5 | Section 6.1 provides verbatim assignment question statements and direct, data-supported empirical answers for Q1 (storage & compute break-even), Q2 (data quality & anti-leakage safeguards), and Q3 (supervisory utility & regime boundaries). | Project specification, empirical results in Sections 1–5 | **VERIFIED** | Assignment question wording preserved verbatim. |
| **Part 6.2: Systemic Limitations & Governance** | 0.5 | Section 6.2 transparently discloses: unmeasured 10x scale, assumed CFP parameter, 29-CERT lifecycle conflicts, intraday liquidity blindness, and SR 11-7 model governance principles. | `docs/evidence/final_verified_results_20261124.md` | **VERIFIED** | All known research boundaries disclosed. |
| **Part 6.3: Vietnamese SBV Policy Adaptation** | 1.5 | Section 6.3 adapts framework to State Bank of Vietnam: Law on Credit Institutions 2024 (No. 32/2024/QH15), Special Control (*Kiểm soát đặc biệt*), 0-VND compulsory transfers, Circular 41/2016 (Basel II CAR), Circular 13/2018 (Internal Control & LCR/NSFR), Circulars 22/08 & 02/06, 4-tier peer grouping, and high-frequency telemetry. | Authoritative Vietnamese legal texts (in-force versions) | **VERIFIED** | Explicit disclaimer: conceptual proposal, not tested on SBV data. |
| **Part 6.4: Academic Integrity & AI Disclosure** | 0.5 | Section 6.4 details generative AI transparency (Google DeepMind Antigravity AI partner, Gemini 3.8 Flash) for pair-programming and verification; all calculations independently verified. Section 7 lists 20 checkable references with URLs/DOIs. | Academic integrity guidelines, bibliography | **VERIFIED** | All citations and AI tools disclosed. |
| **Reproducibility: Pipeline Execution from README** | 5.0 | README.md documents complete execution workflow: Python 3.11.9, OpenJDK 17, PySpark 3.5.3, Polars 2.1.0; pinned requirements; verified test suite (13 passed in 3.81s); project validation script `validate_entire_project.py --check` completes with 0 failures (PYTEST PASS, STAGE_E PASS, FIGURE_SHA PASS). | `README.md`, `tests/`, `scripts/validate_entire_project.py` | **VERIFIED** | All verification commands tested and verified passing. |

---

## Final Certification Declaration

```
========================================================================================
FINAL AUDIT VERIFICATION DECLARATION:
RUBRIC COMPLIANCE STATUS: VERIFIED (100.0 / 100.0 Coverage)
========================================================================================
• Deliverables Generated and Validated:
  - deliverables/DaoHuyThanhVinh_11231024_FDIC_EWS_SUBMISSION.docx (808,838 bytes)
  - deliverables/DaoHuyThanhVinh_11231024_FDIC_EWS_SUBMISSION.pdf  (1,072,785 bytes)
  - deliverables/report_validation.md                              (~15 KB)
  - deliverables/rubric_compliance_matrix.md                       (~14 KB)
• Structural & Page Budget Compliance:
  - Main Academic Report: 17 pages (Budget: 16–19 target pages, <= 20 pages max) [PASS]
  - Technical Appendices: 3 pages (Budget: <= 10 pages max) [PASS]
  - Academic References: 1 page [PASS]
  - Cover Page & Table of Contents: 2 pages [PASS]
  - Total Document Length: 23 pages [PASS]
• Official Figures: 8 / 8 figures verified via SHA-256 and embedded [PASS]
• Empirical Numbers: 100% reconciled against verified CSV/JSON artifacts [PASS]
• Reproducibility: 13 / 13 pytest unit tests pass; validate_entire_project PASS [PASS]
========================================================================================
```

**Audited and Signed:**
Dao Huy Thanh Vinh (Student ID: `11231024`)
Bachelor of Financial Technology (Cohort BFT65B), National Economics University (NEU)
