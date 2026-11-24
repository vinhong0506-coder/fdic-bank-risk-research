# FDIC Feature Contract Audit

**Current source specification:** 30 DEV-available base CAMELS features,
each transformed to a scaled/imputed predictor and a missingness indicator:
60 predictors plus 8 panel metadata columns in the feature-store Parquet.

**Historical fitted models:** the original frozen Development decisions
contain 31 base features (62 transformed predictors).
The sole discrepancy is `eff_ratio`, derived from absent `EEFFR`:
it is NULL for all panel rows. Hence `eff_ratio_isna` was constant 1.
Its historical Logistic Regression coefficient was not necessarily zero,
so prediction identity after refitting is NOT presumed.
The original frozen JSON and Test results were preserved unchanged.

**Leakage control:** selection is made from a fixed feature definition
validated on labeled Development data; Test missingness never selects features.
The shared feature specification is now in `features.py` and imported by `model.py`.

**Required empirical next step:** after lifecycle labels are adjudicated,
run a separately versioned 30-feature model and compare predictions,
Development CV, thresholds, and Test metrics. Do not replace old Test artifacts
or present them as the results of a 30-feature refit.

Feature list (in fitting order):

1. `cap_ratio`
2. `rbc_tier1`
3. `rbc_total`
4. `neg_equity_flag`
5. `is_pre_basel`
6. `npl_ratio`
7. `reserve_coverage`
8. `nonperf_asset_ratio`
9. `ore_ratio`
10. `re_loan_share`
11. `ci_loan_share`
12. `nonix_asset_ratio`
13. `roa`
14. `roe`
15. `nimy`
16. `roa_lag1`
17. `roa_lag4`
18. `roa_diff_qoq`
19. `roa_std_4q`
20. `nimy_std_4q`
21. `liq_asset_ratio`
22. `liq_dep_ratio`
23. `ldr`
24. `brokered_dep_ratio`
25. `log_asset`
26. `asset_growth_qoq`
27. `asset_growth_yoy`
28. `cap_zscore_q`
29. `roa_zscore_q`
30. `npl_zscore_q`

Old frozen decisions SHA-256: `7edeccbc8ae305feba00685d5348e530cc1bd9097b72defcad2151abd9046356`
