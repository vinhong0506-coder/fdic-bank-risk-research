# FDIC Bank Failure Early-Warning System

**Point-in-time financial data engineering · Scalable analytics · Four-quarter bank-failure prediction · Cost-sensitive decision support**

**Academic research project** · Big Data Analytics in Finance (BFT65B), National Economics University (NEU)
**Author:** Dao Huy Thanh Vinh · **Student ID:** 11231024
**Study period:** 1984Q1–2026Q2 · **Submission update:** 25 November 2026

> **Research status.** The project includes a completed 24-page submission report, saved held-out Test results, 27 recorded processing benchmarks, and a documented post-audit correction to the time-series cross-validation procedure. Reported limitations and historical-versus-corrected results are distinguished below; this repository does not claim a clean-machine reproduction of every original experiment.

## Start here: submission and verification

| Resource | Purpose |
| --- | --- |
| **[Final research report — PDF](deliverables/DaoHuyThanhVinh_11231024_FDIC_EWS_SUBMISSION.pdf)** | Main submission: 24 pages (2 cover/contents, 18 main analysis, 1 references, 3 appendices), according to the latest report-export verification |
| [Editable report — DOCX](deliverables/DaoHuyThanhVinh_11231024_FDIC_EWS_SUBMISSION.docx) | Corresponding Word submission |
| [Rubric-to-evidence matrix](deliverables/rubric_compliance_matrix.md) | Maps course requirements to code, tables, figures, and supporting evidence |
| [Report verification dossier](deliverables/report_validation.md) | Page, figure, and content checks; use the PDF itself as the authority for final pagination |
| [Targeted correction log](deliverables/targeted_corrections_log.md) | Documents the changes made after academic review |
| [Fold-local CV impact audit](docs/evidence/cv_fold_local_impact_20261125_145302_363270.md) | Before/after model metrics and Development OOF decision thresholds |
| [170-quarter checksum recheck](docs/evidence/quarter_sha256_independent_20261125.md) | SHA-256 comparison against the saved acquisition manifest |

**Scope of the submission:** eight labeled figures, Python source and tests, technical appendices, and an explicit record of outstanding reproducibility limitations. Raw bank-level files and large model artifacts are not committed to GitHub.

### At a glance

| Recorded outcome | Evidence-backed value |
| --- | --- |
| Financial data | **1,682,738** raw bank-quarters; **1,677,107** clean panel observations |
| Source integrity | **170/170** local quarterly Parquet SHA-256 hashes match the saved manifest |
| Model comparison | Held-out Test **AP 0.679477** (Logistic Regression) and **0.668168** (LightGBM) |
| Processing experiment | **27** recorded pandas/Polars/PySpark runs at 1×, 2× and 5× |
| Code verification | **15 passing tests**, with 9 non-fatal deprecation warnings in the recorded run |
| CV repair | Fold 1 feature selection corrected from **30** to **29** available base features; before/after OOF evidence retained |


## 1. Research objective and design

This study develops a **four-quarter-ahead early-warning system for U.S. bank failure** using FDIC Call Report and institutional event information. It integrates three connected tasks:

1. **Data engineering:** quarterly API acquisition, Parquet storage, completeness and checksum controls, lifecycle-aware panel construction, and report-quarter-indexed financial features.
2. **Big-data analytics:** a measured comparison of pandas, Polars Lazy, and locally executed PySpark on the same **representative seven-feature, calendar-aware workload**.
3. **Risk prediction and decisions:** time-ordered validation of Logistic Regression and LightGBM, a Spark MLlib baseline, and supervisory alert thresholds selected under an explicitly assumed asymmetric cost function.

The panel is **point-in-time by reporting quarter** (`REPDTE`), with calendar-aware lags and temporally separated model fitting. It is **not** an archived historical-vintage dataset that proves when each filing first became publicly available. Therefore, results should not be interpreted as a fully reconstructed real-time supervisory backtest.

### Course components and evidence

| Component | Weight | Main evidence |
| --- | ---: | --- |
| Part 1 — Acquisition and storage | 15 | Resumable FDIC ingestion, 170-quarter manifest, CSV/Parquet measurements, [Figure 1](docs/figures/fig1_storage_benchmark.png) |
| Part 2 — Data quality and panel | 20 | Event/exit handling, temporal split and sample flow, [Figures 2–3](docs/figures/) |
| Part 3 — Scalable processing | 25 | Three processing engines, 27 measured runs, numeric-equivalence checks, [Figures 4–5](docs/figures/) |
| Part 4 — Feature pipeline | 15 | Thirty-feature contract, train-only preprocessing, [feature audit](docs/evidence/cv_feature_availability_audit.md), [Figure 7](docs/figures/fig7_top10_camels_importance.png) |
| Part 5 — Modelling and validation | 15 | Expanding-window CV, Test AP/ROC-AUC, frozen thresholds, [post-audit comparison](docs/evidence/cv_fold_local_impact_20261125_145302_363270.md), [Figure 6](docs/figures/fig6_test_pr_and_calibration.png) |
| Part 6 — Conclusions | 5 | Evidence-bounded supervisory interpretation and Vietnam adaptation, [Figure 8](docs/figures/fig8_cost_and_regime_analysis.png) |
| Reproducibility | 5 | [Pinned dependencies](requirements.txt), tests, integrity checks, documentation and explicit limitations |

*Weights mirror the rubric mapping maintained in this repository; they are not a claim of an awarded grade.*

## 2. Data lineage and temporal validation

**Source:** FDIC BankFind Suite API; recorded acquisition date: **23 November 2026**. The financial data span 170 reporting quarters from **1984Q1 through 2026Q2**.

| Stage | Bank-quarter records | Interpretation |
| --- | ---: | --- |
| Quarterly financial records acquired | 1,682,738 | Raw financial filings across 170 quarters |
| Records removed after confirmed exit | 5,631 | Excluded before construction of the analytical panel |
| Clean analytical panel | 1,677,107 | Lifecycle-aware bank-quarter observations |
| Labeled Development (`1984Q1–2007Q4`) | 1,176,223 | Historical training and time-series CV |
| Embargo (`2008Q1–2008Q4`) | — | Not used for Development fitting or held-out evaluation |
| Labeled held-out Test (`2009Q1–2025Q2`) | 386,964 | 1,775 positive bank-quarters; 500 distinct positive CERTs |
| Unexpired horizons (`2025Q3–2026Q2`) | — | Censored rather than automatically treated as negatives |

The target denotes a failure **within the following four calendar quarters**. Positive **bank-quarter observations** are not the same as distinct failing **banks**. Unresolved/unknown exits are censored in the documented label construction rather than silently treated as surviving banks.

**Source-file integrity:** on **25 November 2026**, SHA-256 hashes were recomputed for **170/170 local quarterly Parquet files** and matched against the saved acquisition manifest; the verified manifest entries sum to **1,682,738 rows**. This checks **local file integrity against stored checksums**, not independent confirmation of the FDIC API's original response, first-publication dates, or historical-vintage provenance. See the [quarter-by-quarter audit](docs/evidence/quarter_sha256_independent_20261125.md) and [integrity status](docs/evidence/part5_integrity_status.json).

## 3. Features and leakage controls

The documented final feature contract comprises **30 CAMELS-inspired financial indicators**, augmented by size, growth and peer-relative variables. Each base indicator has a corresponding missingness indicator, giving **60 model predictors** in the full-Development specification. In regulatory CAMELS, **S means Sensitivity to Market Risk**; institution size is an additional research feature, not a replacement definition of S.

Preprocessing consists of **1st/99th percentile winsorization**, median imputation, and mean/standard-deviation (**z-score**) scaling, with parameters fitted on the relevant training partition. It is **not** IQR-based RobustScaler preprocessing. Calendar-aware lags and rolling statistics are built within bank identifiers; the feature contract excludes identifiers and other direct outcome fields from model predictors.

### Expanding-window CV: audited correction

The original pipeline selected feature availability from the complete labeled Development sample **before** running historical CV. An audit showed that this allowed one feature to be included in Fold 1 even though it was entirely unavailable in that fold's training period. The production CV code was subsequently corrected to **select available features from each fold's Train only**, before fitting that fold's preprocessor.

| CV fold | Training period | Validation period | Base features after correction |
| --- | --- | --- | ---: |
| Fold 1 | 1984Q1–1997Q4 | 1999Q1–2002Q4 | **29** |
| Fold 2 | 1984Q1–2001Q4 | 2003Q1–2005Q4 | **30** |
| Fold 3 | 1984Q1–2004Q4 | 2006Q1–2007Q4 | **30** |

The intervening calendar year creates a four-quarter purge before each validation period. Fold 1 drops `nonperf_asset_ratio`, which depends on `P3ASSET`, unavailable in its Train observations. The final model uses **30 base features** because all are observed within the full Development period used for final fitting.

**Controlled before/after validation comparison (Fold 1):**

| Measure | Reproduced pre-correction CV | Corrected fold-local CV |
| --- | ---: | ---: |
| Logistic Regression **Average Precision** | 0.154802 | **0.210628** |
| Logistic Regression ROC-AUC | 0.839364 | 0.841550 |
| LightGBM **Average Precision** | 0.239183 | **0.239183** |
| LightGBM ROC-AUC | 0.892996 | 0.892996 |

The corrected-versus-original predictions in Fold 2 and Fold 3 were unchanged in this audit. In Fold 1, **LightGBM predictions were unchanged**, whereas **Logistic Regression predictions and AP changed materially**. Consequently, this project **does not claim that the correction had zero impact across all models**. The audit reproduced *current-source* pre-correction CV behavior; it does not establish numerical identity with every older archived experiment.

Evidence: [feature-availability root cause](docs/evidence/cv_feature_availability_audit.md), [full before/after metrics and probability differences](docs/evidence/cv_fold_local_impact_20261125_145302_363270.md), and [source implementation](src/fdic_pipeline/model.py).

## 4. Held-out predictive results and supervisory policy

The following are **saved historical held-out Test** scores on 386,964 labeled bank-quarter observations. These models were trained on the full Development partition; **no post-audit refit of the final Test models was claimed**.

| Held-out Test model | Average Precision (AP) | ROC-AUC |
| --- | ---: | ---: |
| **Logistic Regression** | **0.679477** | **0.986308** |
| LightGBM | 0.668168 | 0.986115 |
| Spark MLlib Logistic Regression | 0.569949 | 0.979381 |

**Metric convention:** AP above is computed using `sklearn.metrics.average_precision_score`. It must not be silently equated with Spark MLlib's native interpolated/integrated `areaUnderPR` (recorded as **0.554674** for the Spark model). Thus, **AP** is the preferred label for the scikit-learn results throughout this README.

**Ranking and decisions are different objectives.** Logistic Regression had the higher saved Test AP, while threshold-based operating outcomes depend on the chosen loss assumptions and the thresholds obtained from Development OOF probabilities. The 0.5%-of-assets false-alert examination cost is **assumed for scenario analysis**, not an observed FDIC examination expense; any reported cost reduction is **modeled**, not a realized regulatory saving.

### Frozen historical policy versus post-audit Development sensitivity

At the approximately **40.3:1** assumed false-negative-to-false-positive cost ratio:

| Threshold source | Logistic Regression | LightGBM | Interpretation |
| --- | ---: | ---: | --- |
| **Historically frozen before Test** | **0.27549287** | **0.02008020** | Used in the saved historical Test policy tables |
| Reproduced, pre-correction Development OOF | 0.28266263 | 0.02008020 | Re-run of the pre-correction CV logic in the current source environment |
| **Corrected, fold-local Development OOF** | **0.03219052** | **0.02008020** | **Post-audit sensitivity result only** |

The corrected LR threshold **must not be presented as a pre-Test-frozen policy**, nor should the historical Test policy table be silently rewritten using it. The frozen predictions and Test ranking metrics were preserved; any later policy re-evaluation using the corrected threshold would require an explicit post-audit disclosure and careful interpretation of prior Test exposure. The LightGBM OOF threshold remained unchanged in the reported controlled comparison.

See the [CV impact audit](docs/evidence/cv_fold_local_impact_20261125_145302_363270.md) and [original-versus-revised correction log](deliverables/targeted_corrections_log.md).

## 5. Processing benchmark: measured scope, not extrapolation

The engine benchmark evaluated the same **representative seven-feature, calendar-aware risk-analytics workload** in pandas, Polars Lazy and local-mode PySpark. It **did not implement or time all 30 predictive CAMELS-inspired features** in every engine. Each engine was run three times at each of three sizes (**27 recorded measurements**); the table reports median wall-clock seconds.

| Scale | Records | pandas | Polars Lazy | PySpark local |
| --- | ---: | ---: | ---: | ---: |
| **1×** | 1,677,107 | 5.157 s | **0.797 s** | 14.757 s |
| **2× synthetic** | 3,354,214 | 9.133 s | **1.559 s** | 17.988 s |
| **5× synthetic** | 8,385,535 | 21.940 s | **2.464 s** | 31.514 s |

The 2× and 5× samples are **synthetic replications with distinct pseudo-bank IDs**, not additional FDIC observations. Equivalence checks and execution details are documented in the [technical results](docs/evidence/final_verified_results_20261124.md). Polars was the fastest engine **on the measured workstation and workload**; this does not establish that Polars is universally faster than Spark. Spark was measured in **local mode**, not on a multi-node cluster. **No 10× result, cluster break-even point or extrapolated speedup is claimed.** Sampled process-tree RSS is not equivalent to total operating-system memory consumption.

The separate storage experiment measured **424.1 MiB CSV versus 143.9 MiB Zstandard Parquet**, and read times of **10.26 s versus 0.47 s** under the reported local setup. These are measured outcomes, not guarantees for other hardware or datasets.

## 6. How to inspect and reproduce

### Repository map

| Location | Contents |
| --- | --- |
| [`deliverables/`](deliverables/) | Submitted PDF/DOCX, report validation, rubric matrix and correction log |
| [`src/fdic_pipeline/`](src/fdic_pipeline/) | FDIC ingestion, panel construction, feature engineering, model evaluation and benchmark code |
| [`scripts/`](scripts/) | Environment setup, preflight, audits and reproducibility helpers |
| [`tests/`](tests/) | Tests for temporal-feature contracts, lifecycle logic and other pipeline assumptions |
| [`docs/figures/`](docs/figures/) | Eight labeled submission figures |
| [`docs/evidence/`](docs/evidence/) | Technical results, quarterly checksums, CV impact, figure manifests and methodological checks |
| [`requirements.txt`](requirements.txt) | Recorded package versions |

**Recorded software environment:** Python 3.11.9; Java 17; NumPy 1.26.4; pandas 2.2.3; Polars 2.1.0; PyArrow 12.0.1; PySpark 3.5.3; LightGBM 4.7.0. Refer to `requirements.txt` for the full set. A matching software environment does not alone reproduce an archived result without the original inputs and computational conditions.

### Source-level setup (Windows PowerShell)

```powershell
git clone https://github.com/vinhong0506-coder/fdic-bank-risk-research.git
Set-Location .\fdic-bank-risk-research
py -3.11 -m venv .venv311
& .\.venv311\Scripts\python.exe -m pip install -r requirements.txt

# Configure JAVA_HOME / SPARK_HOME / HADOOP_HOME for the workstation.
. .\scripts\setup_verified_env.ps1
$py = (Resolve-Path '.\.venv311\Scripts\python.exe').ProviderPath

& $py -m pip check
& $py -m pytest -q
```

**On the original research workstation**, the final logged run passed **15 unit tests (9 non-fatal pandas deprecation warnings)**; `validate_entire_project.py --check` reported **0 failures**. A fresh clone cannot run the complete evidence audit until its uncommitted local input data and artifacts have been restored. This is **verified source/tests and saved evidence**, not a claim that a full pipeline was rebuilt on a new machine.

### Full pipeline entry points (separate fresh workspace)

The following commands **require the raw FDIC download, sufficient RAM/disk, and a fresh output directory**. They are documented entry points, **not** a recommended action on the original frozen submission workspace.

```powershell
# Acquisition can be lengthy and the current FDIC API may return revised data.
& $py -m fdic_pipeline.ingest --start 1984-03-31 --end 2026-06-30 --compression zstd

# Build the lifecycle-aware analytical panel; inspect the exit mapping first.
& $py -m fdic_pipeline.audit --raw data_raw/fdic --out artifacts/audit --panel data_processed/panel_pit.parquet

# Construct the Development-based feature store.
& $py -m fdic_pipeline.features

# Model entry point; will refuse to overwrite existing frozen Test metrics.
# Execute only in a separately prepared reproduction workspace.
& $py -m fdic_pipeline.model
```

For lightweight checks on the original workstation (with existing model evidence), use:

```powershell
& $py scripts/validate_entire_project.py --check
& $py -m fdic_pipeline.make_figures --check
& $py scripts/prepush_qa_fdic.py
```

The pre-push audit checks repository hygiene and **recomputes local manifest hashes** when the 170 source files are available; it does not independently re-download FDIC records. Check the audit report's `PASS`, `WARN` and `FAIL` statuses rather than assuming every optional check was executed.

## 7. Findings, safeguards and unresolved limitations

- **Historical filing availability:** Report-quarter features and train-only fitting address several forms of lookahead, but historical first-publication/revision timestamps were not reconstructed from a vintage archive.
- **CV correction:** Fold-local availability lookahead was identified and corrected. LR CV predictions and its Development-based decision threshold changed; the previously frozen Test results and policy remain identified as historical outputs.
- **Lifecycle adjudication:** **29 CERTs** with conflicting historical exit dates correspond to **106 positive Development bank-quarters** in the recorded audit; no positive Test bank-quarters were counted in that conflict subset. This **does not prove that all other Test labels or features are unaffected**. Unknown exits are censored, and unresolved event mappings remain a limitation.
- **Computational scope:** 27 local benchmark runs at 1×, 2× and 5×; **no 10× test and no multi-node Spark result**. Runtime and sampled memory measurements are hardware- and workload-specific.
- **Loss identification:** The 0.5%-of-assets examination-cost assumption and cost-based thresholds are **scenario constructs**; they are not observed FDIC expenditures, causal intervention benefits or actual budget savings.
- **Comparative interpretation:** Test AP and threshold-based utility address different questions; Spark native PR-AUC is not numerically interchangeable with scikit-learn AP.
- **External validity:** Potential application to the State Bank of Vietnam is a conceptual adaptation, **not** an empirical evaluation on Vietnamese banks.
- **Reproduction boundary:** Raw institution-level data, source Parquet files and large intermediate artifacts are excluded from Git. A full clean-room rebuild, including source-vintage verification, has not been demonstrated here.

These constraints are recorded to keep the conclusions **auditable and proportional to the evidence**, rather than to imply error-free data or guaranteed regulatory performance.

## 8. Sources, licenses and AI-assisted workflow

The submitted [report](deliverables/DaoHuyThanhVinh_11231024_FDIC_EWS_SUBMISSION.pdf) contains the academic and regulatory reference list. Primary data sources and technical tools utilized in this study comprise the FDIC BankFind Suite API, Parquet, pandas, Polars, Apache Spark, scikit-learn, and LightGBM. Please refer to the original data providers and official library documentation for specific licensing and reuse conditions.

The student author independently led the core research process, including problem formulation, solution exploration, workflow design, output verification, scientific interpretation, source attribution, and overall accuracy of the submitted work. 

OpenAI ChatGPT and Google Antigravity were utilized solely as supplementary tools to assist with code debugging, technical documentation, and report preparation.

---

**Review path:** [Read the PDF](deliverables/DaoHuyThanhVinh_11231024_FDIC_EWS_SUBMISSION.pdf) · [Check the rubric mapping](deliverables/rubric_compliance_matrix.md) · [Inspect CV correction evidence](docs/evidence/cv_fold_local_impact_20261125_145302_363270.md) · [Verify the quarter hashes](docs/evidence/quarter_sha256_independent_20261125.md)
