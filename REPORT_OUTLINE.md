# Individual Research Report — 20-page allocation (excluding cover if instructor counts it; confirm page rule)

## Cover / Executive Summary (1 page)
- Student details, GitHub URL, acquisition method/date, exact counts for Financials/Failures/Institutions.
- Scope, Development/Test periods, unique failed banks and positive bank-quarter labels (computed after label adjudication).
- One-line finding for Q1/Q2/Q3; no unsupported claims before running.

## 1. Research objective & context (1 page)
- SBV use-case, early warning vs prediction distinction, research questions, scope and limitations.
- Figure 1: Pipeline overview (source → ingestion/checkpoint → raw Parquet → audit/lifecycle → PIT panel → features → model).

## 2. Data acquisition and storage (2 pages; 15 points)
- FDIC API source, selected fields and rationale, date scope, download date, retries/paging/resume strategy.
- Table 1: Row counts, API totals, quarter coverage, unique CERT, duplicates, completeness, checksums.
- Table 2: CSV vs Parquet codecs; size, ratio, write/read seconds; methodology and repeated-run median.
- Figure 2: Storage footprint comparison.

## 3. Data quality and point-in-time panel (3 pages; 20 points)
- Automated schema drift, nullness, duplicate keys, numeric anomalies, ratio ranges, quarter-level availability.
- Table 3: Quality flags, count/rate, handling rule, retained vs excluded rows.
- Figure 3: Variable availability heatmap over time; Figure 4: distributions/tails (log scale where justified).
- Lifecycle: failures vs mergers/other exits; exit adjudication evidence and unresolved cases.
- Label formula; right censoring; label horizon boundary; sample flow waterfall and label counts.

## 4. Scalable processing and benchmarking (5 pages; 25 points)
- Explain Polars LazyFrame, projection/predicate pushdown, optimizer, parallel execution, streaming caveats, Arrow interchange.
- Table 4: identical transformations in pandas and Polars; median wall-time, spread, peak RSS, row count, hardware/software.
- Table 5: PySpark equivalent; numerical equivalence tolerances; Spark plan excerpt and operator interpretation.
- Figure 5: runtime by engine; Figure 6: RAM by engine (measured externally/process RSS).
- Q1 answer: local laptop thresholds empirically estimated from tested row/column scale, RAM, disk, runtime; operational Spark break-even discussion, not universal rule.

## 5. Feature pipeline (3 pages; 15 points)
- Feature definitions table: CAMELS ratios, growth, rolling volatility, liquidity, asset quality, capital; formula, direction, rationale, availability.
- PIT peer-relative features; point-in-time peer definition and minimum group size.
- Temporal split diagram; fit imputer/winsorizer/scaler only on training folds. Avoid full-panel transforms.
- Table 6: Feature missingness and train-only preprocessing choices.

## 6. Model and validation (3 pages; 15 points)
- Logistic baseline vs LightGBM; optional Spark MLlib demonstration.
- Time-ordered development folds, purging/embargo rules; frozen test.
- Metrics: PR-AUC primary, ROC-AUC, Recall@K, Brier score, calibration, event recall by regime.
- Empirical C_FN/C_FP estimation from failure costs/assets, caveats; threshold chosen on Dev only.
- Table 7: Development CV results; Table 8: single test result; Figure 7: PR/calibration; Figure 8: risk ranking/recall@K.

## 7. Conclusions, Vietnam adaptation & limitations (1 page; 5 points)
- Evidence answers Q1–Q3, model is screening/triage not decision automation.
- SBV adaptation: secure access controls, Vietnamese reporting schema mapping, regulator-specific definitions, data lineage, monitoring, drift, audit logs, human governance, model validation.

## 8. Reproducibility / citations (1 page; 5 points)
- Repo, pinned dependencies, seeds, commands, environment, raw-data exclusion.
- Source, code, papers, library and AI-tool citations/usage disclosure.

## Appendix (up to 10 pages)
- Full selected field dictionary, additional quality tables, all run logs, detailed Spark plan, unit tests, label edge-case examples, threshold derivation and formulas.
