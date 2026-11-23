# U.S. Bank Failure Early-Warning System (FDIC Data, 1984Q1-2026Q2)

Course: Big Data Analytics in Finance - National Economics University (NEU)
Class: 65B-BFT | Student: Dao Huy Thanh Vinh (MSV: 11231024)

## 1. Repository Structure
- src/fdic_pipeline/: End-to-end pipeline (ingest.py, storage_benchmark.py, audit.py, benchmark.py, features.py, model.py, make_figures.py, qa_check.py)
- tests/: Automated anti-leakage and schema unit tests (test_ingest_helpers.py, test_feature_leakage.py)
- artifacts/: Audit tables, 3-engine and scaling benchmarks, execution plans, model metrics, 300 DPI figures (fig1-fig8), and qa_master_checklist.csv

## 2. Reproducibility Execution Order (Python 3.13 + OpenJDK 17)
1. python -m venv .venv
2. .venv/Scripts/Activate.ps1
3. pip install -r requirements.txt
4. Set PYTHONPATH=src
5. python -m fdic_pipeline.ingest
6. python -m fdic_pipeline.storage_benchmark
7. python -m fdic_pipeline.audit
8. python -m fdic_pipeline.benchmark
9. python -m fdic_pipeline.features
10. python -m fdic_pipeline.model
11. python -m fdic_pipeline.make_figures
12. pytest -v
13. python -m fdic_pipeline.qa_check
