# Comprehensive Rubric Compliance Matrix

**Research Title:** U.S. Bank Failure Early-Warning System: A Point-in-Time Big Data Engineering, Multi-Engine Scalability, and Cost-Sensitive Predictive Framework (1984Q1–2026Q2)
**Student Author:** Dao Huy Thanh Vinh (Student ID: `11231024`)
**Course & Program:** Big Data Analytics in Finance — Bachelor of Financial Technology (Class BFT65B), National Economics University (NEU)
**Public GitHub Repository:** [https://github.com/vinhong0506-coder/fdic-bank-risk-research](https://github.com/vinhong0506-coder/fdic-bank-risk-research) (branch `main`)
**Audit Date:** November 24, 2026 (Post-Review Targeted Correction Update)

---

## 1. Rubric Compliance Overview

| Assessment Area | Point Weight | Compliance Status | Key Repository & Report Evidence Summary |
| :--- | :---: | :---: | :--- |
| **Part 1 – Acquisition & Storage** | 15 Points | **COMPLIANT** | Automated REST API ingestion across 170 consecutive quarters (`1984Q1–2026Q2`), 1,682,738 raw observations, multi-codec storage benchmark, Parquet-zstd (2.95x compression, 21.82x read speedup). Verified in Figure 1 & Section 1.3. |
| **Part 2 – Data Quality & Panel** | 20 Points | **COMPLIANT** | Automated DQ audit (Table 2.1), 5,631 post-closure zombie rows eliminated across 62 CERTs, 4-tier lifecycle taxonomy, 29-CERT conflict subset review, report-date PIT panel (1.18M Dev, 33K Embargo, 387K Test). Verified in Figures 2, 3 & Section 2. |
| **Part 3 – Scalable Processing** | 25 Points | **COMPLIANT** | Polars Lazy physical plan vs. eager pandas vs. PySpark Catalyst plan; representative seven-feature risk workload (`workload.py`); cross-engine numeric equivalence ($< 1.42\times 10^{-13}$); 27 executed runs (1x, 2x, 5x); host memory cluster boundary; unmeasured 10x disclosed. Verified in Figures 4, 5 & Section 3. |
| **Part 4 – Feature Pipeline** | 15 Points | **COMPLIANT** | Contract of 30 active base CAMELS-inspired features + 30 missingness indicators = 60 predictors; integer calendar quarter index (`q_idx`); train-only Winsorization (1st/99th percentiles), median imputation, and Z-score standardization; CV feature availability audit disclosed. Verified in Figure 7 & Section 4. |
| **Part 5 – Predictive Modeling & MLlib** | 15 Points | **COMPLIANT** | Predefined baseline configurations for Logistic Regression, LightGBM, and PySpark MLlib; Precision-Recall AUC, ROC-AUC, Brier scores; asymmetric supervisory loss matrix ($40.3:1$ ratio); optimal threshold $\tau^* = 0.0201$ over 501-point quantile grid; 1.78% test alert rate; 59.7% modeled expected cost reduction. Verified in Figure 6 & Section 5. |
| **Part 6 – Supervisory Policy & SBV** | 10 Points | **COMPLIANT** | Three supervisory pillars (Continuous Screening, Dynamic Reserves, Targeted Auditing); 3 historical crisis regimes analyzed; non-additivity explained ($468+30+9=507$ vs. 500); SBV adaptation roadmap under Law on Credit Institutions 2024 (No. 32/2024/QH15) and circulars. Verified in Figure 8 & Section 6. |
| **TOTAL ASSESSMENT** | **100 Points** | **FULLY COMPLIANT** | **Strict adherence to all assignment criteria, page budgets, and academic disclosures.** |

---

## 2. Detailed Criterion-by-Criterion Evidence Breakdown

### Criterion 1: Data Acquisition & Storage Benchmarking [15 Points]

- **Lecturer / Rubric Requirements:**
  - Automated download of quarterly Call Reports covering at least 10 years (our study covers 42.5 years, 170 quarters).
  - Storage benchmark across multiple physical formats and compression codecs (CSV, Parquet uncompressed, snappy, gzip, zstd).
  - Measurement of storage size (bytes), compression ratio, and read latency (full-table scan, column subset projection, row filtering).
  - Code modularity and automated retry logic for resilient downloading.
- **Repository Code Evidence:**
  - `src/fdic_pipeline/ingest.py`: Automated ingestion from FDIC BankFind Suite API with offset pagination, exponential backoff (up to 5 retries with jitter), and deterministic 429/5xx error recovery.
  - `src/fdic_pipeline/storage_benchmark.py`: Systematic benchmark script evaluating 6 formats across 1.68 million rows.
  - `artifacts/benchmark/storage_full/storage_benchmark.csv`: Measured disk metrics.
- **Academic Report References:**
  - Section 1.1: API ingestion mechanics, offset pagination, and network resiliency (Pages 5–6).
  - Section 1.2: 3-tier integrity verification (quarter counts, primary key integrity, missingness patterns) (Page 6).
  - Section 1.3: Table 1.1 (Storage benchmark results) and Figure 1 (`fig1_storage_benchmark.png`) (Page 6).

---

### Criterion 2: Data Audit, Point-in-Time Panel & Temporal Splitting [20 Points]

- **Lecturer / Rubric Requirements:**
  - Detection and remediation of historical data-quality anomalies (missing identifiers, duplicates, structural zeroes, post-exit zombie rows).
  - Lifecycle taxonomy distinguishing supervisory receivership closures from commercial unassisted mergers and voluntary dissolutions.
  - Constructing a Point-in-Time (PIT) longitudinal panel without lookahead bias or survivorship distortion.
  - Temporal partitioning into Development, Embargo quarantine, and held-out Test evaluation horizons.
- **Repository Code Evidence:**
  - `src/fdic_pipeline/audit.py`: Automated scanning for 7 defect classes; eliminates 5,631 post-exit zombie filings across 62 unique failure CERTs.
  - `docs/evidence/lifecycle_exception_review.md`: Granular review of the 29-CERT conflict subset (`inst_end_date < failure_date`), proving 0 positive bank-quarters in Test.
  - `artifacts/audit/panel_flow.json` and `failure_reconciliation.csv`: Complete row accounting from 1,682,738 raw rows to 1,677,107 clean PIT rows.
- **Academic Report References:**
  - Section 2.1: Table 2.1 (Automated Data-Quality Audit Framework, detection rules, remediation) (Page 7).
  - Section 2.2: Event taxonomy, competing exit risks, and 29-CERT lifecycle review (Pages 7–8).
  - Section 2.3: Failure registry reconciliation (Table 2.2), 344 unmatched failures qualified explanation, and report-date PIT vs. vintage PIT distinction (Page 8).
  - Section 2.4: Basel I capital accounting structural break, CBLR impact, and Figure 2 (`fig2_capital_regime_audit.png`) (Page 8).
  - Section 2.5: Temporal split architecture, Table 2.3 (Split segments, censoring controls), and Figure 3 (`fig3_temporal_split_overview.png`) (Page 9).

---

### Criterion 3: Scalable Big Data Engine Benchmarking [25 Points]

- **Lecturer / Rubric Requirements:**
  - Implementation of an identical, calendar-aware analytical feature workload across multiple computing engines: eager pandas, Polars Lazy API, and Apache Spark (PySpark).
  - Execution plan disassembly: Polars DAG optimization (projection/predicate pushdown) vs. Spark Catalyst execution tree (WindowExec, Exchange).
  - Cross-engine numerical equivalence audit with strict floating-point parity tolerances ($< 10^{-6}$).
  - Multi-scale empirical performance benchmarking (wall time, compute latency, peak RSS memory) across synthetic data scales with speedup ratios.
  - Analytical justification of when a distributed Spark cluster is economically and computationally warranted.
- **Repository Code Evidence:**
  - `src/fdic_pipeline/workload.py`: Implements identical representative seven-feature risk calculations (`capital_ratio`, `loan_asset_ratio`, `liquidity_ratio`, `asset_growth_qoq`, `asset_growth_yoy`, `roa_std_4q`, `cap_zscore_pit`) in Polars, pandas, and PySpark.
  - `src/fdic_pipeline/benchmark.py`: Multi-scale driver with memory tracking (`psutil` process-tree RSS), Spark master `local[*]`, and 8 shuffle partitions.
  - `artifacts/stageC/final/benchmark_runs.csv`: 27 executed experimental benchmark runs across 1x (1.68M), 2x (3.35M), and 5x (8.39M) synthetic scales.
  - `artifacts/stageC/*/numeric_equivalence.json`: Automated parity test confirming maximum absolute difference $\le 1.42 \times 10^{-13} < 10^{-6}$.
- **Academic Report References:**
  - Section 3.1: Polars Lazy API implementation, query graph, Rayon multithreading, and projection pushdown (Page 10).
  - Section 3.2: Eager pandas baseline overhead, single-threaded GIL bottlenecks (Page 10).
  - Section 3.3: Distributed PySpark Local[*] architecture, 8 shuffle partitions, Catalyst WindowExec plan analysis, Py4J serialization costs (Pages 10–11).
  - Section 3.4: Table 3.1 (Cross-Engine Numeric Equivalence Audit across all 7 engineered attributes) (Page 11).
  - Section 3.5: Table 3.2 (1x Baseline summary), Table 3.3 (Multi-scale scaling across 27 runs), Figure 4 (`fig4_engine_benchmark_1x.png`), and Figure 5 (`fig5_synthetic_scaling_5x.png`) (Pages 11–12).
  - Section 3.6: Cluster break-even boundary, memory bounds, and explicit disclosure that 10x was not measured (Page 12).

---

### Criterion 4: Point-in-Time Feature Engineering & Anti-Leakage [15 Points]

- **Lecturer / Rubric Requirements:**
  - Construction of bank risk indicators grounded in the CAMELS supervisory framework (Capital, Asset Quality, Management, Earnings, Liquidity, Sensitivity).
  - Rigorous anti-leakage engineering: calendar-strict lag offsets, gap invalidation, rolling windows, and train-only fitted transformations.
  - Explicit missingness tracking indicators (`_isna`) for regime-sensitive accounting items.
  - Automated unit tests validating feature contract and temporal invariance under future data perturbation.
- **Repository Code Evidence:**
  - `src/fdic_pipeline/features.py`: Defines 30 active base features (`SELECTED_CAMELS_FEATURES`) + 30 missingness indicators = 60 predictors.
  - `LeakageSafePreprocessor`: Two-sided Winsorization (1st and 99th percentiles), median imputation, and mean/standard-deviation Z-score standardization fitted strictly on training data.
  - `docs/evidence/cv_feature_availability_audit.md` & `tests/test_fold_local_feature_selection.py`: Independent audit and unit test verifying fold-local feature availability invariance.
  - `tests/test_feature_contract.py` & `tests/test_stageB_competing_risk.py`: Automated regression tests.
- **Academic Report References:**
  - Section 4.1: CAMELS-inspired taxonomy augmented by size, growth, and peer indicators; Table 4.1 (Master feature importance and coefficients); Figure 7 (`fig7_top10_camels_importance.png`) (Pages 13–14).
  - Section 4.2: Anti-leakage calendar indexing mathematics (`q_idx = year * 4 + quarter - 1`) and gap-aware invalidation (Page 14).
  - Section 4.3: Train-only preprocessing pipeline, Winsorization, median imputation, Z-score standardization, unit testing, and historical CV feature availability audit disclosure (Page 14).
  - Appendix C: Table C.1 (Master Feature Store Dictionary, mathematical definitions, Development baseline parameters) (Pages 22–23).

---

### Criterion 5: Cost-Sensitive Predictive Modeling & Spark MLlib [15 Points]

- **Lecturer / Rubric Requirements:**
  - Predictive modeling comparing linear baselines (L2 Logistic Regression), modern non-linear gradient boosting (LightGBM), and distributed machine learning (PySpark MLlib).
  - Expanding-window time-series cross-validation protocol on historical Development data with purging buffers.
  - Evaluation under severe class imbalance using Precision-Recall Area Under the Curve (PR-AUC / AP), Brier probability calibration, and Top-Decile Alert Recall.
  - Operational supervisory cost matrix optimization incorporating asymmetric False Positive and False Negative costs.
- **Repository Code Evidence:**
  - `src/fdic_pipeline/model.py`: 3-fold expanding-window cross-validation with 4-quarter purging buffers; out-of-fold probability collection; constructor-aligned hyperparameters.
  - Empirical Cost Estimation: Derived from 1,275 historical FDIC failure resolutions ($L_{FN} = 20.17\%$, assumed $C_{FP} = 0.50\%$, cost ratio $40.3:1$).
  - `run_spark_mllib_demo`: Distributed Spark MLlib LogisticRegression with dual PR metric reporting (Spark trapezoidal `areaUnderPR` = 0.5547; scikit-learn rectangular `AP` = 0.5699).
  - Frozen Decisions: `artifacts/model_30feature_corrected/frozen_development_decisions.json`.
- **Academic Report References:**
  - Section 5.1: Model architectures, rationale for linear vs. non-linear vs. distributed models (Page 15).
  - Section 5.2: Expanding-window cross-validation protocol; Table 5.1 (3-Fold CV performance metrics) (Page 15).
  - Section 5.3: Imbalanced metrics, dual PR metric explanation; Table 5.2 (Out-of-time Test performance on 386,964 quarters); Figure 6 (`fig6_test_pr_and_calibration.png`) (Pages 15–16).
  - Section 5.4: Asymmetric supervisory loss derivation, 501-point empirical quantile threshold grid, frozen $\tau^* = 0.0201$; Table 5.3 (Cost matrix sensitivity across 3 scenarios); alert rate defined as 1.78% of eligible test quarters; 59.7% modeled expected cost reduction (Pages 16–17).
  - Section 5.5: Macroeconomic sub-regime sensitivity, Table 5.4 (Crisis, Normalization, Rate Shock), non-additivity reconciliation ($468+30+9=507$ vs. 500) (Page 17).
  - Appendix E: Exact constructor hyperparameters aligned with codebase (Page 23).

---

### Criterion 6: Supervisory Policy Recommendations & Adaptation [10 Points]

- **Lecturer / Rubric Requirements:**
  - Actionable, realistic early-warning supervisory policy recommendations (e.g., examination scheduling, capital reserve triggers, CAMELS composite downgrades).
  - Historical crisis robustness analysis (GFC, Pandemic, 2023 Regional Banking Crisis).
  - Concrete adaptation framework for the Vietnamese banking system under the State Bank of Vietnam (SBV), addressing local regulations, circulars, and institutional realities.
  - Transparent disclosure of research limitations, model governance (SR 11-7), and academic integrity.
- **Repository Code Evidence:**
  - Figure 8 (`fig8_cost_and_regime_analysis.png`): Empirically verified visual showing crisis breakdown and supervisory decision trade-offs.
  - `docs/evidence/final_verified_results_20261124.md`: Audited regulatory and policy parameters.
- **Academic Report References:**
  - Section 6.1: Three actionable supervisory policy pillars (Continuous Off-Site Screening, Dynamic Countercyclical Capital Conservation, Risk-Weighted On-Site Examination Prioritization); Figure 8 (`fig8_cost_and_regime_analysis.png`) (Pages 18–19).
  - Section 6.2: Systemic limitations and model governance (single-node 10x hardware boundary, $C_{FP}$ scenario assumption, 29-CERT lifecycle review, high-frequency run blindness, SR 11-7 decision support) (Page 19).
  - Section 6.3: State Bank of Vietnam (SBV) adaptation roadmap: VAS vs. Call Reports, Circular 41/2016, Circular 11/2021, Circular 13/2018, Circular 22/2019 & 08/2020, Circular 02/2023 & 06/2024; Special Control (*Kiểm soát đặc biệt*) and 0-VND compulsory transfers under Law on Credit Institutions 2024 (No. 32/2024/QH15); 4-tier bank peer grouping; high-frequency NAPAS/OMO telemetry (Page 19).
  - Section 6.4: Academic integrity, code citation, and Generative AI pair-programming co-auditor disclosure (Page 19).

---

## 3. Formatting, Typography, and Presentation Verification

| Presentation Standard | Target Requirement | Implemented Standard | Audit Verification |
| :--- | :--- | :--- | :---: |
| **Document Format** | Word (.docx) and PDF (.pdf) | Native DOCX + Native Word COM PDF | **PASS** |
| **Typographic Hierarchy** | Clear serif/sans hierarchy | Georgia (prose), Calibri (headings), Consolas (code/math) | **PASS** |
| **Body Font Size & Spacing** | 10.5–11 pt, 1.15 line spacing | 10.5 pt Georgia, 1.15 line spacing, 3 pt paragraph spacing | **PASS** |
| **Table Design** | Professional academic tables | Deep Navy header (#1A365D), white text, alternating slate rows | **PASS (11 Tables)** |
| **Figure Captions & Labels** | Numbered captions + data labels | Bold caption + data labels + 3-bullet structured interpretations | **PASS (8 Figures)** |
| **Page Budget – Main Body** | 16–19 target, max 20 pages | Exactly **18 substantive pages** (Pages 3–20) | **STRICT PASS** |
| **Page Budget – Appendices** | Max 10 additional pages | Exactly **3 technical appendix pages** (Pages 22–24) | **STRICT PASS** |
| **Total Document Length** | Under 30 pages total | Exactly **24 total pages** | **STRICT PASS** |
| **Academic References** | Formal academic citations | 20 formal APA 7th academic and regulatory references (Page 21) | **PASS** |
| **Reproducibility** | Full environment & scripts | Clear README instructions, conda/venv specifications, automated test suite | **PASS** |

---

## 4. Final Audit Verdict

The revised deliverable package satisfies all structural, technical, and academic requirements specified by the course rubric. All empirical results are reproducible, fully audited against repository source code and frozen data artifacts, and defended by transparent academic disclosures.
