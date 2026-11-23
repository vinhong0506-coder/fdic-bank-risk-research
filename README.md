# FDIC EWS — audited replacement code (2026-11-23)

**Status: code patch, NOT an independently reproduced empirical result.** Copy the `src/fdic_pipeline` and `tests` folders into a **new branch** of the public project. Original FDIC data and `artifacts/` from the user's machine were not available in the review environment. Do not reuse old report tables after rebuilding the panel.

## Changes and limitations

1. `benchmark.py` is now a Python program rather than Markdown. It runs an identical calendar-strict workload in pandas, Polars Lazy and Spark Local. It checks full-row numeric equivalence before timed runs, generates physical/optimized execution plans and produces synthetic 1x/2x/5x/10x benchmarks with disjoint pseudo-bank CERTs. Synthetic scale does not establish a multi-node cluster break-even.
2. `audit.py` writes `q_idx`, `split`, `label_reason`, `exit_type`, `failure_date`, `horizon_end_date` and `confirmed_exit_date`; deduplicates failure event keys; removes post-exit records. Known non-failure mergers/liquidations are 0; UNKNOWN exits before horizon end are censored. Institutional exit codes are **not guessed**. To reproduce non-failure event labels, supply an audited `data_reference/exit_mapping.csv` containing `CERT,event_date,event_type`.
3. `features.py` uses calendar-strict lag/rolling; excludes all-missing financial features, and fits winsorization/imputation/scaling on Development only. `model.py` purges four whole observation quarters before each validation period and saves frozen OOF thresholds prior to held-out Test. An existing `final_test_metrics.csv` blocks an accidental second run.
4. `COST/QBFASSET` is a *resolution-loss proxy* and `C_FP=0.005` of assets is **assumed**, not measured from FDIC.
5. Every previous published numeric benchmark, risk metric, label count and report table requires a reproducible rerun and comparison before final submission.

## Setup (PowerShell, Windows)

Use an existing verified environment, or create a separate compatible environment using Python 3.11 and JDK 17 for Spark 3.5.x. Do not use an untested Python 3.13 + Spark 3.5.3 combination as the reproduction contract.

```powershell
py -3.11 -m venv .venv-repair
.\.venv-repair\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PYTHONPATH="src"
java -version
python -m pytest -q
```

Run in this order, **after copying the patch and preserving the original results**:

```powershell
# Optional original data ingestion; do not redownload if verified manifest is intact
python -m fdic_pipeline.audit --raw data_raw/fdic --out artifacts/audit --panel data_processed/panel_pit.parquet --exit-map data_reference/exit_mapping.csv
python -m fdic_pipeline.storage_benchmark --raw data_raw/fdic --out artifacts/benchmark/storage_full
python -m fdic_pipeline.features
python -m fdic_pipeline.benchmark --input data_processed/panel_pit.parquet --out artifacts/benchmark/engine --scales 1 --repeats 3
# If 1x equivalence PASS and disk/RAM budget allows:
python -m fdic_pipeline.benchmark --input data_processed/panel_pit.parquet --out artifacts/benchmark/engine --scales 1,2,5,10 --repeats 3

# CAUTION: this reads Test. Explicitly archive any old model output first,
# freeze research decisions, and perform final once per research version.
python -m fdic_pipeline.model
python -m fdic_pipeline.qa_check
```

`storage_benchmark.py` on the full panel creates large disposable samples in artifacts. Do not commit those samples. The `benchmarks` compare end-to-end process time including start-up, plus compute time, and approximate child-process RSS. Workload is FULL DATA; Spark Local is NOT a multi-node cluster. Run after any JVM warmup protocol is documented.

**Known remaining research work**: map exit `CHANGEC1` with its official FDIC data dictionary; verify historical regulatory-capital field semantics; evaluate report-availability-lag as sensitivity; review whether the `COST`-based loss is avoidable; and validate bank IDs across charter transitions. These are not silently treated as completed.

## Artifacts to commit (small only)

Commit small summary CSV/JSON, audited exception tables and selected plans/figures when confidentiality and size permit. Do not commit raw/processed FDIC datasets, large benchmark replicas, credentials or private data. If `.gitignore` excludes all `artifacts/`, add a safe allowlist or copy selected evidence to `docs/evidence/`.

## Reporting policy

Update the report after rerunning. In particular, remove claims that Spark Local proves a precise cluster transition threshold or that a 44.3% reduction in *scenario loss units* equals observed supervision spending saved. Recount overlapping unique failures across diagnostic regimes.

Once metrics are validated, run `python scripts/publish_evidence.py` and commit only the selected `docs/evidence/` contents. Regenerate figures from current artifact schema; the old `make_figures.py` may expect column names from the previous benchmark design and may require adaptation after verification.

## Data Sources, Software and AI Disclosure

### Data sources

The primary data source is the U.S. Federal Deposit
Insurance Corporation (FDIC), including quarterly
institution financial reports and bank failure records.

Official references:

- FDIC BankFind Suite API documentation:
  https://api.fdic.gov/banks/docs/
- FDIC Data Downloads:
  https://www.fdic.gov/bank-data-guide/data-downloads
- FDIC Quarterly Banking Profile:
  https://www.fdic.gov/quarterly-banking-profile

The study uses public FDIC data. It does not provide
raw research data or large intermediate data files
through this repository.

### Software and reproducibility

The implementation uses Python, pandas, Polars,
PyArrow, PySpark MLlib, scikit-learn, LightGBM,
matplotlib and pytest.

Exact installed package versions are specified in
`requirements.txt`.

Run the pipeline in the order given in the
reproducibility instructions above. Spark benchmarking
uses local execution and does not establish multi-node
cluster performance.

### Generative AI disclosure

OpenAI ChatGPT was used as an AI-assisted development
tool for discussing methodology, reviewing Python
code, troubleshooting Windows/PySpark compatibility,
drafting documentation and suggesting validation
checks.

AI-generated suggestions require independent review
and execution. Reported numerical results are based
on executed research scripts and saved experiment
outputs, not on AI-generated numerical estimates.

The author remains responsible for the correctness
of the implementation, interpretation, citations
and final submitted work.

### Interpretation and limitations

The 5x and 10x scaling experiments use synthetic
replication of the original bank-quarter panel and
must not be interpreted as newly observed FDIC banks.

The reported cost-sensitive decision scenarios rely
partly on an assumed false-positive examination cost.
They are not empirical estimates of realized
supervisory savings.

Unresolved bank exits are censored rather than
automatically assigned negative failure labels.
