# BFT65B — FDIC Bank Failure Early-Warning Data Pipeline

Research implementation scaffold for a reproducible FDIC quarterly Call Report pipeline.


## Research integrity / important caveats
- Do not commit downloaded FDIC data (`data_raw/`, `data_processed/`) or credentials.
- Raw values are not silently corrected. Audit flags are outputs; decisions must be documented.
- `exit_mapping.csv` is a manually-reviewed event adjudication table. Do not infer every `ENDEFYMD` is a failure.
- Before using the panel for modeling, validate date parsing, event classifications, label horizons, duplicate CERT-quarter rows, and quarter-end coverage. The starter `create_panel` function is intentionally conservative but requires validation against FDIC metadata and the official assignment rules.
- Development/Test split and threshold selection must be frozen before final test evaluation. No test-set tuning.

## Setup

Python 3.11 recommended. In a virtual environment:

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Download

```bash
python -m fdic_pipeline.ingest --start 1984-03-31 --end 2026-06-30 --out data_raw/fdic
```
Run from `src` or set `PYTHONPATH=src`:
```bash
# PowerShell
$env:PYTHONPATH='src'; python -m fdic_pipeline.ingest
# bash
PYTHONPATH=src python -m fdic_pipeline.ingest
```
Quarter-level manifest records API count, observed count, duplicate keys, checksum, and compression.

## Audit and panel prototype
```bash
PYTHONPATH=src python -m fdic_pipeline.audit --raw data_raw/fdic --out artifacts/audit --panel data_processed/panel_pit.parquet
```
Create `data_reference/exit_mapping.csv` with columns `CERT,event_date,event_type` and audited classifications before treating unknown exits as non-failures. Accepted types in prototype: `FAILURE`, `MERGER`, `VOLUNTARY_LIQUIDATION`, `OTHER_EXIT`, `UNKNOWN`.

## Benchmarks
```bash
PYTHONPATH=src python -m fdic_pipeline.benchmark --raw data_raw/fdic --out artifacts/benchmark
PYTHONPATH=src python -m fdic_pipeline.benchmark --raw data_raw/fdic --out artifacts/benchmark --spark
python -m fdic_pipeline.storage_benchmark --input data_raw/fdic/financials/YEAR=2026/QUARTER=Q2/REPDTE=20260630.parquet
```
Benchmark on the same hardware, same data, warm/cold cache protocol, at least 3 runs; report median and spread, not one run. Save OS, CPU, RAM, Python/library versions and available RAM.

## Folder structure
- `src/fdic_pipeline`: reusable ingestion, audit, processing, benchmark modules
- `tests`: automated tests
- `notebooks`: EDA and figures (not the canonical pipeline)
- `artifacts`: generated outputs/tables/figures (not raw inputs)
- `data_raw`, `data_processed`: local-only data

## AI use statement
AI tools may assist with debugging, code drafting, and editing. Verify every generated function, document the prompts/use in the report, and do not cite AI output as empirical evidence. All results must be reproduced from the code and raw data.

## Exit adjudication template
Copy `data_reference/exit_mapping_template.csv` to your local `data_reference/exit_mapping.csv` and fill only with reviewed lifecycle events. Keep the template empty in Git if it contains derived institution-level records; never commit sensitive/private data.
