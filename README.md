# FDIC Bank Failure Early-Warning System

**Point-in-Time Data Engineering, Scalable Processing, and Cost-Sensitive Bank Risk Prediction (1984Q1–2026Q2)**

- **Author:** Dao Huy Thanh Vinh (Student ID: 11231024)
- **Course:** BFT65B – Big Data Analytics in Finance, National Economics University
- **Repository:** https://github.com/vinhong0506-coder/fdic-bank-risk-research

## Final submission — start here

- [Read the completed report (PDF)](deliverables/DaoHuyThanhVinh_11231024_FDIC_EWS_SUBMISSION.pdf)
- [Download the completed report (Word)](deliverables/DaoHuyThanhVinh_11231024_FDIC_EWS_SUBMISSION.docx)
- [Report validation and page-count audit](deliverables/report_validation.md)
- [100-point rubric and evidence matrix](deliverables/rubric_compliance_matrix.md)

According to the submitted verification dossier, the report contains 18 pages of main analysis, 3 pages of appendices, and 24 pages overall, including cover, contents and references. The report includes eight labeled research figures.

## Research overview

The project develops and evaluates a four-quarter-ahead bank-failure early-warning system using U.S. FDIC data. It combines reproducible API acquisition, Parquet storage, lifecycle-aware data quality, point-in-time feature engineering, Polars/PySpark processing benchmarks, and cost-sensitive predictive decisions.

| Course component | Weight | Design and evidence |
| --- | ---: | --- |
| Part 1 — Acquisition & Storage | 15 | Resumable quarterly FDIC downloads, manifest checks and measured CSV-versus-Parquet performance; [Figure 1](docs/figures/fig1_storage_benchmark.png) |
| Part 2 — Data Quality & Panel | 20 | Automated data-quality audit, failure versus other exits, unknown-exit censoring and PIT panel; [Figures 2–3](docs/figures/) |
| Part 3 — Scalable Processing | 25 | pandas baseline, Polars Lazy, PySpark, query plans, numeric equivalence and 27 benchmark runs; [Figures 4–5](docs/figures/) |
| Part 4 — Feature Pipeline | 15 | 30 CAMELS-related base attributes, 30 missingness flags and Development-only preprocessing; [feature contract](docs/evidence/feature_contract.md) |
| Part 5 — Modelling & Validation | 15 | Logistic Regression, LightGBM, Spark MLlib, expanding time-series CV, held-out Test and cost-based thresholding; [Figures 6–8](docs/figures/) |
| Part 6 — Conclusions | 5 | Answers to the assignment questions, study limitations and implications for Vietnam |
| Reproducibility | 5 | Pinned packages, research source code, fixed random seeds, staged execution instructions and automated checks |

The [full report](deliverables/DaoHuyThanhVinh_11231024_FDIC_EWS_SUBMISSION.pdf) explains design choices and interprets the measurements.

## FDIC acquisition, sample and data quality

**Data source:** FDIC BankFind Suite API. **Recorded download date:** 23 November 2026. The raw dataset spans 170 quarterly periods (`1984Q1–2026Q2`).

| Stage | Records | Notes |
| --- | ---: | --- |
| Raw quarterly financial filings | 1,682,738 | 170 downloaded quarters |
| Post-exit records removed | 5,631 | Excluded from the PIT panel |
| Clean bank–quarter panel | 1,677,107 | Lifecycle-aware analytical panel |
| Development (`1984Q1–2007Q4`) | 1,176,223 labeled | 10,153 positive bank-quarters / 2,680 distinct positive CERTs |
| Embargo | `2008Q1–2008Q4` | Separation between Development and Test |
| Test (`2009Q1–2025Q2`) | 386,964 labeled | 1,775 positive bank-quarters / 500 distinct positive CERTs |
| Last four quarters | `2025Q3–2026Q2` | Unexpired prediction horizons censored |

The target is failure within the next four calendar quarters. Positive bank-quarters and unique bank identifiers (CERTs) are different units; they must not be conflated. Unknown exit events remain censored rather than automatically labeled as nonfailures.

On 25 November 2026, all 170 local quarterly Parquet files passed SHA-256 recomputation against the stored acquisition manifest (1,682,738 total rows); see [checksum evidence](docs/evidence/quarter_sha256_independent_20261125.md) and [integrity status](docs/evidence/part5_integrity_status.json). This verifies local files against stored checksums, not independent FDIC API provenance or a historical vintage archive.

## Storage and scalable processing

Parquet with Zstandard compression reduced the measured storage file from 424.1 MiB (CSV) to 143.9 MiB; measured read time changed from 10.26 s to 0.47 s.

Each engine was measured three times per scale, giving 27 benchmark runs. The following are median wall-clock seconds:

| Scale | Bank-quarter rows | pandas | Polars Lazy | PySpark local |
| --- | ---: | ---: | ---: | ---: |
| 1× | 1,677,107 | 5.157 | **0.797** | 14.757 |
| 2× synthetic | 3,354,214 | 9.133 | **1.559** | 17.988 |
| 5× synthetic | 8,385,535 | 21.940 | **2.464** | 31.514 |

The 2× and 5× data are synthetic replications using distinct pseudo-bank identifiers, not additional FDIC observations. Cross-engine outputs were checked for numeric agreement at the documented tolerance. Polars was fastest on the measured workstation; multi-node cluster performance was not measured. See [technical results](docs/evidence/final_verified_results_20261124.md).

## Models and policy decisions

The final modeling contract includes 30 base financial features + 30 missingness indicators = 60 predictors. Features use calendar-aware lags and training-only preprocessing. Expanding Development validation includes a four-quarter purge, followed by a separate held-out Test evaluation.

| Held-out Test model | Average Precision | ROC-AUC |
| --- | ---: | ---: |
| Logistic Regression | **0.679477** | **0.986308** |
| LightGBM | 0.668168 | 0.986115 |
| Spark MLlib Logistic Regression | 0.569949 | 0.979381 |

Spark's native `areaUnderPR = 0.554674` and scikit-learn Average Precision use different PR integration conventions. The alarm policy is evaluated using Development-selected thresholds, unique-bank capture, alert rates, sensitivity to assumed examination costs and historical regime analysis. The 0.5% of assets false-alert examination cost is a scenario assumption, not an observed FDIC expense.

## Post-audit CV correction (25 November 2026)

Feature availability is now selected from each fold's own Train observations before fitting the train-only preprocessor. Fold 1 uses **29 base features**, excluding `nonperf_asset_ratio`; Folds 2 and 3 and the full-Development final model retain **30 features**.

| Fold 1 validation | Before correction | After correction |
| --- | ---: | ---: |
| Logistic Regression Average Precision | 0.154802 | **0.210628** |
| LightGBM Average Precision | 0.239183 | **0.239183** |
| Logistic Regression ROC-AUC | 0.839364 | 0.841550 |

At the 40.3:1 assumed cost ratio, the Development OOF threshold for **LightGBM remains 0.02008020**. The Logistic Regression threshold changes from **0.28266263 to 0.03219052**.

The historically frozen Logistic Regression Test policy used **0.27549287**, which differs from the reproduced pre-correction OOF threshold. The corrected LR threshold is a **post-audit Development-only diagnostic**, not a new pre-Test-frozen policy. Original held-out Test predictions, ranking metrics and historical policy results were preserved.

Evidence: [fold-local impact audit](docs/evidence/cv_fold_local_impact_20261125_145302_363270.md), [feature availability audit](docs/evidence/cv_feature_availability_audit.md), and [correction log](deliverables/targeted_corrections_log.md).

## Repository guide

| Path | Contents |
| --- | --- |
| [`deliverables/`](deliverables/) | Final PDF, DOCX, verification dossier and rubric matrix |
| [`src/fdic_pipeline/`](src/fdic_pipeline/) | FDIC ingestion, lifecycle audit, features, modeling and benchmark implementations |
| [`scripts/`](scripts/) | Environment setup, audit, publication and supporting validation scripts |
| [`tests/`](tests/) | Data-contract, feature-leakage and processing tests |
| [`docs/figures/`](docs/figures/) | Eight official labeled figures |
| [`docs/evidence/`](docs/evidence/) | Numerical research evidence, feature contract and figure checksums |
| [`requirements.txt`](requirements.txt) | Pinned Python packages for the tested research runtime |

To respect the course submission rules, raw FDIC data, institution-level processed datasets and large intermediate artifacts are not committed.

## Reproducibility

Recorded environment: Python 3.11.9, Java 17, PySpark 3.5.3, Polars 2.1.0, pandas 2.2.3, NumPy 1.26.4 and PyArrow 12.0.1. See pinned [`requirements.txt`](requirements.txt). Model code sets fixed random seeds where relevant, including `random_state=42`.

The following commands assume Windows PowerShell. Java 17, Spark and Hadoop local paths must be configured for your machine; `setup_verified_env.ps1` contains defaults from the original workstation.

### 1. Setup

```powershell
git clone https://github.com/vinhong0506-coder/fdic-bank-risk-research.git
cd fdic-bank-risk-research
py -3.11 -m venv .venv311
.\.venv311\Scripts\python.exe -m pip install -r requirements.txt

# Configure JAVA_HOME, SPARK_HOME and HADOOP_HOME first.
. .\scripts\setup_verified_env.ps1
$py = (Resolve-Path '.\.venv311\Scripts\python.exe').ProviderPath
```

### 2. Pipeline stages (network access and sufficient disk/RAM required)

`fdic_pipeline.ingest` downloads FDIC source files using resumable quarter manifests. The remaining steps build the panel, features and predictive results. Run in a fresh working directory for a full reproduction.

```powershell
& $py -m fdic_pipeline.ingest --start 1984-03-31 --end 2026-06-30 --compression zstd
& $py -m fdic_pipeline.audit --raw data_raw/fdic --out artifacts/audit --panel data_processed/panel_pit.parquet
& $py -m fdic_pipeline.features
& $py -m fdic_pipeline.model
```

Note: the modeling command intentionally refuses to overwrite existing frozen Test outputs. Preserve prior evidence when rerunning experiments.

To repeat the 1×, 2× and 5× processing benchmark on adequately provisioned hardware:

```powershell
& $py -m fdic_pipeline.benchmark --input data_processed/panel_pit.parquet --out artifacts/benchmark/reproduction --scales 1,2,5 --repeats 3 --master 'local[2]' --partitions 4
```

### 3. Automated checks

```powershell
& $py -m pip check
& $py -m pytest -q
& $py scripts/stage1_preflight.py
& $py -m fdic_pipeline.make_figures --check
```

With local full-study outputs and Stage E evidence in place, also run:

```powershell
& $py scripts/validate_entire_project.py --check
```

The research environment recorded 15 passing unit tests, 11 PASS / 4 WARN / 0 FAIL in the Stage E audit and matching SHA-256 hashes for eight published figures. These checks validate code and available evidence; they are not presented as proof of a separately executed clean-machine, full-data rebuild.

## Research scope and limitations

- **Compute:** measured at 1×, 2× and 5× on a workstation. Neither 10× nor distributed Spark cluster timing was evaluated.
- **Event taxonomy:** some historic nonfailure exits and conflicting exit dates remain unresolved; unknown exits are censored.
- **Decision costs:** false-alert costs are scenario assumptions; modeled cost differences are not realized FDIC savings.
- **Transferability:** the State Bank of Vietnam discussion is a conceptual adaptation, not an empirical Vietnamese bank evaluation.

## Data sources, software and AI acknowledgment

The [full report](deliverables/DaoHuyThanhVinh_11231024_FDIC_EWS_SUBMISSION.pdf) contains the research bibliography and regulatory citations. Principal data and software sources are:

- FDIC BankFind Suite API documentation and FDIC data downloads.
- Apache Parquet, Polars, Apache Spark, pandas, scikit-learn and LightGBM.

The author conceived the core research framework, formulated the methodological approach, evaluated alternative strategies, and designed the end-to-end experimental workflow. OpenAI ChatGPT and Google Antigravity served as assistive tools for code debugging, programming implementation, technical documentation, and manuscript formatting. The author retains sole responsibility for the validation of all empirical results, scientific analysis and interpretation, accuracy of citations, and the integrity of the final submission.

[Open the final PDF report](deliverables/DaoHuyThanhVinh_11231024_FDIC_EWS_SUBMISSION.pdf)
