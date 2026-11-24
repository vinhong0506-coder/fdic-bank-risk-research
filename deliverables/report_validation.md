# Deliverable Quality Assurance and Verification Audit Dossier

**Document Title:** U.S. Bank Failure Early-Warning System: A Point-in-Time Big Data Engineering, Multi-Engine Scalability, and Cost-Sensitive Predictive Framework (1984Q1–2026Q2)
**Student Author:** Dao Huy Thanh Vinh (Student ID: `11231024`)
**Course & Program:** Big Data Analytics in Finance — Bachelor of Financial Technology (Class BFT65B), School of Banking and Finance, National Economics University (NEU)
**Public GitHub Repository:** [https://github.com/vinhong0506-coder/fdic-bank-risk-research](https://github.com/vinhong0506-coder/fdic-bank-risk-research) (branch `main`)
**Audit Timestamp:** 2026-11-24T19:28:00+07:00

---

## 1. Generated Output Files and Physical Attributes

| Deliverable File Path | File Format | File Size | Generation Engine | Verification Status |
| :--- | :---: | :---: | :---: | :---: |
| `deliverables/DaoHuyThanhVinh_11231024_FDIC_EWS_SUBMISSION.docx` | Microsoft Word (.docx) | 808,838 bytes (~790 KB) | Python `python-docx` 1.2.0 | **PASS** (Strict Word Styles, no XML corruption) |
| `deliverables/DaoHuyThanhVinh_11231024_FDIC_EWS_SUBMISSION.pdf` | Adobe Portable Document (.pdf) | 1,072,785 bytes (~1.02 MB) | Native Word COM Engine (Windows DCOM) | **PASS** (100% layout and text fidelity) |
| `deliverables/report_validation.md` | Markdown Audit (.md) | ~15 KB | Deterministic Audit Pipeline | **PASS** |
| `deliverables/rubric_compliance_matrix.md` | Rubric Compliance (.md) | ~14 KB | Comprehensive 100-Point Rubric Audit | **PASS** |

*Baseline Preservation Note:* The original files `DaoHuyThanhVinh_11231024_FDIC_EWS_FINAL.docx` and `DaoHuyThanhVinh_11231024_FDIC_EWS_FINAL.pdf` remain **preserved completely intact and unmodified** in the project root. Prior submission files were backed up safely to `deliverables/backup/`.

---

## 2. Page Count Audit and Structural Budget Compliance

Page counts were independently measured from `deliverables/DaoHuyThanhVinh_11231024_FDIC_EWS_SUBMISSION.pdf` via PyMuPDF (`pymupdf` 2.1) and cross-verified by rendering all 23 pages to PNG (`deliverables/rendered_pages/page_01.png` to `page_23.png`):

| Document Structural Partition | Starting Page | Ending Page | Measured Pages | Allowed Budget Limit | Compliance Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Cover Page & Mandatory First-Page Snapshot** | Page 1 | Page 1 | 1 page | N/A | **PASS** |
| **Table of Contents (TOC)** | Page 2 | Page 2 | 1 page | N/A | **PASS** |
| **Main Academic Report (Exec Summary to Conclusions)** | **Page 3** | **Page 19** | **17 pages** | **Max 20 pages (Target: 16–19)** | **PASS (3 pages headroom)** |
| **Academic & Regulatory References** | Page 20 | Page 20 | 1 page | N/A | **PASS** |
| **Technical Appendices (Appendices A to E)** | **Page 21** | **Page 23** | **3 pages** | **Max 10 pages** | **PASS (7 pages headroom)** |
| **Total Combined Document Length** | **Page 1** | **Page 23** | **23 pages** | Max 32 pages | **PASS** |

*Visual QA Verification:*
- **Zero text clipping:** No paragraph cutoffs, missing formulas, or truncated sentences across page boundaries.
- **Zero broken tables:** Every table row enforces `<w:cantSplit/>`, and header rows repeat `<w:tblHeader/>`.
- **Zero orphaned headings:** All Heading 1, Heading 2, and Heading 3 styles enforce `keep_with_next = True`.
- **Zero image overflows:** All 8 figures are scaled to 6.2 inches width, centered with italicized captions beneath.

---

## 3. Official Figures Embedding and Cryptographic Hash Audit

All 8 figures embedded in the report were drawn exclusively from `docs/figures/` and checked against the immutable manifest `docs/evidence/verified_figures_manifest.json` before insertion:

| Figure Identifier | Figure File Name | Expected SHA-256 Checksum | Verified SHA-256 Checksum | In-Doc Caption and Placement |
| :--- | :--- | :--- | :--- | :---: |
| **Figure 1** | `fig1_storage_benchmark.png` | `3165d89a90d446dffba2a8c9e4f3a262df95b001b6bc36c5cfa7a213a7745630` | `3165d89a90d446dffba2a8c9e4f3a262df95b001b6bc36c5cfa7a213a7745630` | **MATCH (PASS)** |
| **Figure 2** | `fig2_capital_regime_audit.png` | `4a0551bfef2d66297c8bf750ca7aeb0087c1c9b75245cd19f8494fca8f00d434` | `4a0551bfef2d66297c8bf750ca7aeb0087c1c9b75245cd19f8494fca8f00d434` | **MATCH (PASS)** |
| **Figure 3** | `fig3_temporal_split_overview.png` | `30da47802e29e3e896b08bd84465108bf85f7d82c07a8d4bbd2cb39acedc98cc` | `30da47802e29e3e896b08bd84465108bf85f7d82c07a8d4bbd2cb39acedc98cc` | **MATCH (PASS)** |
| **Figure 4** | `fig4_engine_benchmark_1x.png` | `ee3cabd83aafa7ad32882667d281ec64c5dfe853c0b8feed0fde92d6d61a78fd` | `ee3cabd83aafa7ad32882667d281ec64c5dfe853c0b8feed0fde92d6d61a78fd` | **MATCH (PASS)** |
| **Figure 5** | `fig5_synthetic_scaling_5x.png` | `758b9d1e8f923a4b303efae438cd298feaa867e3fdc693f26c298a4e04f6fe79` | `758b9d1e8f923a4b303efae438cd298feaa867e3fdc693f26c298a4e04f6fe79` | **MATCH (PASS)** |
| **Figure 6** | `fig6_test_pr_and_calibration.png` | `7d687ab53591771819db05246eb9c3c83694addd20317849e9d0eab30b675e9a` | `7d687ab53591771819db05246eb9c3c83694addd20317849e9d0eab30b675e9a` | **MATCH (PASS)** |
| **Figure 7** | `fig7_top10_camels_importance.png` | `7651aa74214c029f15db6df4ecfdca22f5061fc3026a678b23a1a3238b78a7a5` | `7651aa74214c029f15db6df4ecfdca22f5061fc3026a678b23a1a3238b78a7a5` | **MATCH (PASS)** |
| **Figure 8** | `fig8_cost_and_regime_analysis.png` | `fdd9694c0021ba74ffd345ae69089906134ea0f76350ef2b2e4f9a71d06d84ea` | `fdd9694c0021ba74ffd345ae69089906134ea0f76350ef2b2e4f9a71d06d84ea` | **MATCH (PASS)** |

---

## 4. Key Empirical Reconciliation Matrix

Every empirical statistic stated in the submission report was verified against its source artifact:

| Empirical Research Statistic | Report Value | Source File in Repository | Verified Ground-Truth Value | Status |
| :--- | :---: | :--- | :---: | :---: |
| **Temporal Coverage** | 170 Quarters (`1984Q1–2026Q2`) | `data_raw/fdic/manifest_financials.json` | 170 quarters, 100% manifest match | **VERIFIED** |
| **Raw Financial Records** | `1,682,738` | `artifacts/audit/panel_flow.json` | `1,682,738` | **VERIFIED** |
| **Post-Exit Zombie Rows Purged** | `5,631` | `artifacts/audit/panel_flow.json` | `5,631` (across 62 unique CERTs) | **VERIFIED** |
| **Clean PIT Panel Observations** | `1,677,107` | `artifacts/audit/panel_flow.json` | `1,677,107` | **VERIFIED** |
| **Historical Failure Records** | `4,117` raw / `3,585` unique CERTs | `artifacts/audit/failure_reconciliation.json` | 4,117 raw; 488 null; 3,585 unique | **VERIFIED** |
| **Failures Matched in Panel** | `3,241` unique CERTs | `artifacts/audit/failure_reconciliation.json` | `3,241` matched; `344` pre-1984 | **VERIFIED** |
| **Development Valid Observations** | `1,176,223` | `artifacts/audit/panel_flow.json` | `1,176,223` (48,719 unknown exits censored) | **VERIFIED** |
| **Development Failure Events** | `10,153` bank-quarters / `2,680` CERTs | `artifacts/model_30feature_corrected/` | 10,153 positive bank-quarters; 2,680 CERTs | **VERIFIED** |
| **Embargo Gap (2008)** | `33,039` valid / `176` failed CERTs | `artifacts/audit/temporal_split_summary.csv` | 33,039 valid; 402 positive; 176 CERTs | **VERIFIED** |
| **Held-Out Test Observations** | `386,964` | `artifacts/model_30feature_corrected/final_test_metrics.csv` | `386,964` | **VERIFIED** |
| **Held-Out Test Positives** | `1,775` bank-quarters / `500` CERTs | `artifacts/model_30feature_corrected/final_test_metrics.csv` | 1,775 positive bank-quarters; 500 CERTs | **VERIFIED** |
| **Terminal Censored Horizon** | `17,501` observations (`2025Q3–2026Q2`) | `artifacts/audit/temporal_split_summary.csv` | `17,501` right-censored | **VERIFIED** |
| **Feature Space Contract** | 30 base features / 60 predictors | `docs/evidence/feature_contract.md` | 30 active base + 30 `_isna` = 60 | **VERIFIED** |
| **Polars 1x Latency & Speedup** | `0.797 s` (6.47x vs pandas, 18.52x vs Spark) | `artifacts/stageC/final/benchmark_runs.csv` | 3-run median = `0.797 s` (rows=1,677,107) | **VERIFIED** |
| **pandas 1x Latency** | `5.157 s` | `artifacts/stageC/final/benchmark_runs.csv` | 3-run median = `5.157 s` | **VERIFIED** |
| **PySpark Local[*] 1x Latency** | `14.757 s` | `artifacts/stageC/final/benchmark_runs.csv` | 3-run median = `14.757 s` | **VERIFIED** |
| **Synthetic Scaling Scope** | 27 executed runs (1x, 2x, 5x) | `artifacts/stageC/final/benchmark_runs.csv` | 27 total runs; 10x NOT measured | **VERIFIED** |
| **Numeric Equivalence Max Diff** | `5.68e-14` (variance), `1.42e-13` (z-score) | `artifacts/stageC/*/numeric_equivalence.json` | Max abs diff < 1.0e-06 (PASS) | **VERIFIED** |
| **Logistic Regression Test AP** | `0.6795` (ROC-AUC `0.9863`) | `artifacts/model_30feature_corrected/final_test_metrics.csv` | AP = 0.679477, ROC = 0.986308 | **VERIFIED** |
| **LightGBM Test AP** | `0.6682` (ROC-AUC `0.9861`) | `artifacts/model_30feature_corrected/final_test_metrics.csv` | AP = 0.668168, ROC = 0.986115 | **VERIFIED** |
| **Spark MLlib Test AP** | `0.5699` sklearn AP / `0.5547` native PR | `artifacts/model_30feature_corrected/spark_mllib_validation.json` | sklearn AP = 0.569949, Spark PR = 0.554674 | **VERIFIED** |
| **Median Resolution Loss (L_FN)** | `20.17%` of total assets | `artifacts/model_30feature_corrected/empirical_cost_estimation.csv` | Median loss = 0.2017 (N = 1,275 failures) | **VERIFIED** |
| **Assumed Examination Cost (C_FP)**| `0.50%` of total assets (Assumed) | `artifacts/model_30feature_corrected/empirical_cost_estimation.csv` | 0.005 (Explicit scenario benchmark) | **VERIFIED** |
| **Empirical Loss Ratio** | `40.3:1` | `artifacts/model_30feature_corrected/empirical_cost_estimation.csv` | `40.3` | **VERIFIED** |
| **LightGBM Institutional Recall** | `484 / 500` (96.8%) | `artifacts/model_30feature_corrected/test_cost_sensitive_decisions.csv` | 484/500 unique banks at tau* = 0.0201 | **VERIFIED** |
| **LightGBM Alert Rate** | `1.78%` of bank-quarters | `artifacts/model_30feature_corrected/test_cost_sensitive_decisions.csv` | `1.78%` | **VERIFIED** |
| **Expected Cost Reduction** | `59.7%` reduction vs Logistic Regression | `artifacts/model_30feature_corrected/test_cost_sensitive_decisions.csv` | 10,025.7 vs 24,863.0 units | **VERIFIED** |
| **Sub-Regime Non-Additivity** | `468 + 30 + 9 = 507` vs `500` unique | `artifacts/model_30feature_corrected/regime_nonadditivity.json` | 7 failed banks span calendar boundaries | **VERIFIED** |

---

## 5. Summary of Corrections from Historical Drafts

1. **Feature Space Normalization:**
   - *Previous Drafts:* Claimed 31 base features and 62 transformed predictors.
   - *Submission Standard:* Strictly corrected to **30 base features and 60 predictors**, reflecting the omission of structurally absent `eff_ratio` (`EEFFR`), where missingness was constant.
2. **Benchmark Scaling Realism:**
   - *Previous Drafts:* Claimed synthetic 10x measurements and asserted a single-node crossover where Spark surpassed Polars at 2x.
   - *Submission Standard:* Strictly restricted to the **27 executed runs at 1x, 2x, and 5x**. Clearly disclosed that 10x was not measured and that Polars maintains undisputed single-node superiority across all evaluated scales.
3. **Unit of Observation Disentanglement:**
   - *Previous Drafts:* Occasionally conflated quarterly positive bank-quarters ($y=1$) with unique failed bank institutions.
   - *Submission Standard:* Systematically disaggregated: Test set contains **1,775 positive bank-quarters** representing exactly **500 unique failed bank charters**.
4. **PySpark Metric Distinction:**
   - *Previous Drafts:* Reported Spark MLlib PR-AUC without explaining discrepancies with scikit-learn.
   - *Submission Standard:* Documented that Spark's native `areaUnderPR` (0.5547) uses trapezoidal interpolation, while scikit-learn's `Average Precision` (0.5700) uses step-weighted integration over the exact same prediction probabilities.
5. **Supervisory Cost Disclosure:**
   - *Previous Drafts:* Presented the 40:1 cost ratio as fully identified.
   - *Submission Standard:* Disclosed that while $L_{FN} = 20.17\%$ is empirically derived from 1,275 FDIC failure resolutions, $C_{FP} = 0.50\%$ is an assumed supervisory operational benchmark.
6. **Cross-Validation Realism:**
   - *Previous Drafts:* Cited an unverified 5-fold cross-validation scheme.
   - *Submission Standard:* Replaced with the empirically verified **3-fold expanding time-series CV on Development** (Fold 1: 1999–2002, Fold 2: 2003–2005, Fold 3: 2006–2007) with 4-quarter purging buffers.
7. **Official Figures Replacement:**
   - *Previous Drafts:* Embedded older, unverified, or unlabeled figures from `artifacts/figures/`.
   - *Submission Standard:* Replaced with the **8 official labeled figures from `docs/figures/`**, validated by binary SHA-256 hashes matching `verified_figures_manifest.json`.

---

## 6. Disclosed Research Limitations

In accordance with strict academic research ethics, the following known limitations are explicitly declared in the report:
1. **Unmeasured 10x Workload:** Due to single-workstation memory bounds (16 GB RAM), 10x synthetic scaling was not executed. Single-node superiority of Polars is proven up to 5x (8.39M rows); distributed Spark scaling requires a multi-node cluster (>64 GB RAM).
2. **Lifecycle Exception Adjudication:** 29 conflicting historical CERTs with `inst_end_date < failure_date` (106 positive bank-quarters historically, 0 in Test) remain pending event-level merger confirmation. Unknown non-failure exits remain censored to avoid negative label corruption.
3. **Assumed Examination Cost:** $C_{FP} = 0.005 \times \text{assets}$ is a supervisory scenario parameter, not an FDIC invoice audit.
4. **Intraday Liquidity Blindness:** Quarterly Call Reports cannot capture viral, social-media-accelerated deposit runs within hours (e.g., Silicon Valley Bank in March 2023).

---

## 7. Final Declaration and Certification

Based on comprehensive visual inspection of all 23 rendered pages, complete textual and formula comparison, cryptographic hash matching of all 8 embedded figures, and rigorous data cross-referencing against verified repository artifacts:

```
========================================================================================
FINAL VERIFICATION DECLARATION:
REPORT READY WITH DISCLOSED LIMITATIONS
========================================================================================
• Deliverables Generated:
  - deliverables/DaoHuyThanhVinh_11231024_FDIC_EWS_SUBMISSION.docx (808,838 bytes)
  - deliverables/DaoHuyThanhVinh_11231024_FDIC_EWS_SUBMISSION.pdf  (1,072,785 bytes)
  - deliverables/report_validation.md                              (~15 KB)
  - deliverables/rubric_compliance_matrix.md                       (~14 KB)
• Page Count Audit:
  - Main Academic Report: 17 pages (Target: 16–19 pages; Budget <= 20 pages) [PASS]
  - Technical Appendices: 3 pages (Budget <= 10 pages) [PASS]
  - Academic & Regulatory References: 1 page [PASS]
  - Cover Page & Table of Contents: 2 pages [PASS]
  - Total Document Length: 23 pages [PASS]
• Official Figures: 8 / 8 figures verified via SHA-256 and embedded [PASS]
• Key Numbers: 100% reconciled against verified CSV/JSON artifacts [PASS]
• Prohibited Claims: Zero fabricated 10x claims, zero old 31-feature mentions [PASS]
• Unit Tests: 13 / 13 passed in 3.81s; validate_entire_project PASS [PASS]
========================================================================================
```

**Signed:**
Dao Huy Thanh Vinh (Student ID: `11231024`)
Bachelor of Financial Technology (Cohort BFT65B), National Economics University (NEU)
