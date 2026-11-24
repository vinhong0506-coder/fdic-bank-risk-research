# FDIC Bank Failure Early-Warning System

**Verified locally on 24 November 2026.**

This GitHub repository publishes code, tests, lightweight evidence
and eight official labeled figures. Raw/processed FDIC data,
large model outputs and benchmark logs remain local.

## Research data and leakage safeguards

- 170 quarters, 1984Q1?2026Q2; 1,682,738 raw records.
- 5,631 post-exit rows removed; 1,677,107 PIT bank-quarter rows.
- Labeled Development: 1,176,223 rows.
- Labeled held-out Test: 386,964 rows.
- Test: 1,775 positive quarters from 500 distinct positive CERTs.
- Development through 2007Q4, embargo in 2008,
  Test 2009Q1?2025Q2.
- Four-quarter prediction horizon, calendar-strict lags,
  Development-only preprocessing and frozen OOF thresholds.
- Corrected contract: **30 base features and 60 predictors**,
  including missingness indicators.

Historical 31/62-feature outputs are not official model results.

## Verified held-out Test models

The following values use scikit-learn metrics on saved predictions.

| Model | Average Precision | ROC-AUC |
|---|---:|---:|
| Logistic Regression | **0.679477** | **0.986308** |
| LightGBM | 0.668168 | 0.986115 |
| Spark MLlib Logistic Regression | 0.569949 | 0.979381 |

Spark's native evaluator separately reported
areaUnderPR=0.554674 and areaUnderROC=0.979361.

Spark areaUnderPR and scikit-learn Average Precision
must not be presented as the same metric.

Spark predictions were exported using PyArrow after a
Windows Hadoop-native file writer failure.

## Engine benchmark: 27 verified runs

Three repetitions per engine and scale.
Median wall-clock runtime in seconds:

| Scale | Rows | pandas | Polars Lazy | Spark local[2] |
|---|---:|---:|---:|---:|
| 1x | 1,677,107 | 5.157 | **0.797** | 14.757 |
| 2x | 3,354,214 | 9.133 | **1.559** | 17.988 |
| 5x | 8,385,535 | 21.940 | **2.464** | 31.514 |

The 2x and 5x inputs are synthetic replications,
not additional real FDIC observations.

**10x has not been measured.**
No 10x performance or Spark crossover is claimed.

Spark was evaluated locally, not on a multi-node cluster.

## Verified environment

- Python 3.11.9
- OpenJDK 17
- PySpark 3.5.3
- NumPy 1.26.4
- pandas 2.2.3
- PyArrow 12.0.1
- Polars 2.1.0

Installed package versions are synchronized with the
existing pins in `requirements.txt` where available.
This is not an independently certified clean installation.

Adapt Spark/Hadoop installation paths to the target machine.

## Verification commands

Run from the repository root with the compatible
`.venv311` environment and local research inputs.

```powershell
. .\scripts\setup_verified_env.ps1

& .\.venv311\Scripts\python.exe -m pip check
& .\.venv311\Scripts\python.exe -m pytest -q
& .\.venv311\Scripts\python.exe scripts\stage1_preflight.py
& .\.venv311\Scripts\python.exe -m fdic_pipeline.make_figures --check
& .\.venv311\Scripts\python.exe scripts\validate_entire_project.py --check
```

These checks require existing local FDIC files and outputs.
They do not perform an independent full-data rebuild.

## Published evidence

- `src/fdic_pipeline/`: PIT audit, features, modeling and benchmarks.
- `tests/`: audit, leakage, feature-contract and workload tests.
- `docs/figures/`: eight official labeled PNG figures.
- `docs/evidence/verified_figures_manifest.json`:
  eight PNG SHA-256 hashes.
- `docs/evidence/figure_data_labels.json`:
  80 numerical-label records.
- `docs/evidence/final_verified_results_20261124.md`:
  verified model and benchmark results.
- `docs/evidence/lifecycle_exception_review.md`:
  unresolved exit mapping.
- Stage E technical audit: **11 PASS, 4 WARN, 0 FAIL**.

## Limitations and research integrity

1. Event adjudication of some merger, liquidation and
   unknown exits remains unresolved.
   The 29-CERT conflict subset contained 106 historical
   positive bank-quarters and no positive Test
   bank-quarters in that subset. This does not prove
   the full Test set is unaffected.
2. The false-positive examination cost of 0.5% of assets
   is an **assumed scenario**, not an observed
   FDIC supervisory saving.
3. The 10x benchmark, fresh-install/full-data rebuild
   and final report review are not certified as complete.
4. Application to the State Bank of Vietnam is a proposed
   adaptation, not validation on Vietnamese bank data.

## Data sources and AI disclosure

FDIC BankFind API:
https://api.fdic.gov/banks/docs/

FDIC data downloads:
https://www.fdic.gov/bank-data-guide/data-downloads

OpenAI ChatGPT assisted with debugging, testing
and documentation. Reported numerical results were
obtained from executed research code and saved evidence.

The author remains responsible for research
interpretation, validation and final reporting.
