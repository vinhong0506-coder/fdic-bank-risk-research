# FDIC: Verified Technical Results

Generated: 2026-11-24T14:09:34

> **Post-audit addendum (25 November 2026):** Fold-local feature selection was implemented. Fold 1 Logistic Regression AP changed from 0.154802 to 0.210628; LightGBM AP remained 0.239183. The corrected Development OOF LightGBM threshold remained 0.02008020, while LR changed from 0.28266263 to 0.03219052. The historical held-out Test artifacts were preserved. Unit tests: 15 PASS. The final PDF was reported as 24 pages. Local quarterly SHA-256: 170/170 matched the saved manifest. See [CV audit](cv_fold_local_impact_20261125_145302_363270.md) and [checksum evidence](quarter_sha256_independent_20261125.md).

## Reproduction status

- Stage E: 11 PASS, 4 WARN, 0 FAIL.
- Base features: 30.
- ML predictors: 60.
- TEST bank-quarters: 386,964.
- Positive TEST bank-quarters: 1,775.
- Frozen development decisions SHA256: `be0d5cd227f5c27713ad82b2c9ceb017836e9d9637ce2721531a0ac2c18ad5b8`.
- Repository commit at evidence creation: `4f3102f4553fbc8f75934a75c2a9dd3b373f16e8`.
- Local uncommitted changes may not be represented by that commit.

## Model comparison on held-out TEST

All values in this table are independently calculated
using scikit-learn metrics from saved predictions.

| Model | Average Precision | ROC-AUC |
|---|---:|---:|
| Logistic Regression | 0.679477 | 0.986308 |
| LightGBM | 0.668168 | 0.986115 |
| Spark MLlib Logistic Regression | 0.569949 | 0.979381 |

Spark native metrics (BinaryClassificationEvaluator):

- Spark areaUnderPR: 0.554674.
- Spark areaUnderROC: 0.979361.
- Spark sklearn Average Precision: 0.569949.
- Spark sklearn ROC-AUC: 0.979381.

Spark areaUnderPR and sklearn Average Precision use
different integration conventions and must not be
described as identical metrics.

## Benchmark: verified 27 measurements

Each engine was measured three times at 1x, 2x, 5x.
Values below are three-run medians.

| Scale | Engine | Median wall seconds | Median sampled RSS MiB | Rows |
|---|---|---:|---:|---:|
| 1x | pandas | 5.157 | 793.6 | 1,677,107 |
| 1x | polars | 0.797 | 774.3 | 1,677,107 |
| 1x | spark | 14.757 | 1013.3 | 1,677,107 |
| 2x | pandas | 9.133 | 1489.1 | 3,354,214 |
| 2x | polars | 1.559 | 1340.6 | 3,354,214 |
| 2x | spark | 17.988 | 1010.0 | 3,354,214 |
| 5x | pandas | 21.940 | 3554.5 | 8,385,535 |
| 5x | polars | 2.464 | 2346.7 | 8,385,535 |
| 5x | spark | 31.514 | 1443.5 | 8,385,535 |

- 10x was NOT measured on this computer.
- 2x and 5x are synthetic replications of bank-quarters.
- Spark was executed in local mode, not a multi-node cluster.
- Sampled process-tree RSS is not a total OS RAM metric.
- No measured 10x crossover or distributed Spark speed claim.

## Figures

- 8 PNG figures created.
- 80 data-label entries recorded.
- Source folder: `artifacts/stageD/figures_labeled`.
- Visual inspection for overlaps and legibility is still required.

## Lifecycle labels: outstanding limitation

- Conflicting CERTs observed in panel: 29.
- Positive bank-quarters in this conflict subset:
  106.
- Positive TEST bank-quarters in this conflict subset:
  0.
- These counts do not establish that all TEST labels
  and features are unaffected.
- Non-failure exit events and ENDEFYMD conflicts
  are not yet fully adjudicated.
- Unknown exits must not be silently relabeled as negatives.

## Cost analysis

- Decision thresholds were frozen from Development OOF.
- False-positive examination cost is assumed, not observed.
- Scenario cost units must not be presented as realized
  supervisory expenditure savings.

## Outstanding research tasks

1. Independently adjudicate lifecycle conflicts where possible.
2. Visually inspect all eight labeled figures.
3. Word tables and figures were updated in the 25 November submission; keep later edits consistent.
4. README and reproducibility instructions were updated for the 25 November release.
5. Review Git changes and commit curated evidence only.

This document records completed checks and known
limitations; it is not a claim of full event-level
ground-truth verification.
