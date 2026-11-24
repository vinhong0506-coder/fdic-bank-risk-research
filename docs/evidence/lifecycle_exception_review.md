# FDIC Lifecycle Exception Review (not yet adjudicated)

- Financial-reporting-after-ENDEFYMD exceptions: **3 CERT rows** in the local diagnostic summary.
- ENDEFYMD-before-FAILDATE exceptions: **35 distinct CERTs** in the complete historical registry. Some are outside the study period.
- No verified merger/liquidation mapping has been supplied. Unknown exits therefore remain censored and should not be relabeled as mergers.
- Status: **PENDING manual confirmation using FDIC History / Bank Structure Changes**. Do not assert that these dates are wrong without event-level verification.
- Local, uncommitted detail files: `logs/exit_review/reporting_after_end_date.csv` and `logs/exit_review/failure_end_date_conflicts.csv`.
- Public reference: https://banks.data.fdic.gov/bankfind-suite/oscr

This review does not change the existing panel, targets, CV, or Test predictions.
