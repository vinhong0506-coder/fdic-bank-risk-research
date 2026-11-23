# Report amendments to apply AFTER verified rerun (English text)

**Do not replace measured numerical results with the example or previous results.** Results from this patch must first be generated and reconciled with the report.

## Executive Summary: Q1

Replace categorical statements that a multi-node Spark cluster becomes essential above 10 million rows with:

> The synthetic scaling experiment compares local execution engines under a fixed hardware configuration. It does not benchmark a multi-node Spark cluster or estimate its infrastructure costs. Consequently, the measured crossover, if reproduced, is a local-engine workload-specific result rather than a universal data-size threshold for adopting distributed computing. A cluster is justified only when measured memory, latency, resilience and operational requirements exceed the capacity of a suitably optimized single-node baseline.

## Part 2: failure reconciliation

Specify the following mutually exclusive quantities from new audit logs: total failure rows; null CERT rows; duplicate identifiable CERT rows; unique CERTs with a valid failure date; unique CERTs matched to a bank-quarter panel; and unmatched valid CERTs. Missing CERT cannot be categorically attributed to uninsured institutions or a pre-1934 history without record-level evidence.

## Part 2: competing risks and target

> The primary binary endpoint is an FDIC-recorded failure within four subsequent quarters. A verified merger or voluntary liquidation is a non-failure event (y=0) under the assignment-defined endpoint. Unresolved or unknown exits that prevent outcome ascertainment are censored (y=NULL). An alternative competing-risk sensitivity may exclude or censor identified non-failure exits; its estimand and sample size must be reported separately.

## Part 3: parity evidence

Replace abstract `PASS` claims with exported `numeric_equivalence.json`, ordered key comparisons, null-mask tests, and per-feature maximum differences. Include the exact Spark optimized *and physical* plans, and compare same calendar-strict lag/rolling transformations. Keep cold-start and in-process compute time distinct. Explain any non-monotonic speed outcomes.

## Part 4: rolling window

> Four-quarter volatility requires four observed consecutive calendar quarters, rather than four most recent available bank filings. Missing intermediate quarters produce unavailable volatility features and corresponding missingness indicators.

## Part 5: temporal CV

> Each expanding-window validation interval is preceded by a four-quarter purge of observation dates. Therefore, the forward four-quarter label resolution for the final training observation precedes the first validation quarter. All preprocessing parameters and model/threshold decisions are estimated on the development period only, using the purged folds.

## Part 5: loss function

> Historical FDIC loss ratios are measured as COST/QBFASSET on eligible development failures. The assumed false-positive examination cost of 0.5% of assets is a scenario parameter, not an empirical FDIC estimate. Thus the implied cost ratio, alarm threshold and percentage reduction describe a scenario-dependent classification-cost proxy, not demonstrated savings in government examination budgets or avoided receivership losses. Robustness to other intervention costs and avoidable-loss proportions is necessary.

## Table 5.6 overlapping failures

Add below the crisis regime table:

> Regime-level distinct failed-bank counts need not sum to the full-test distinct count because the same bank can contribute positive bank-quarter labels on both sides of a regime boundary. The global unique CERT count and sum of regime-specific counts are reported separately; the overlap is explicitly reconciled in `regime_nonadditivity.json`.

## References, limitations and AI disclosure

Update all quantitative figures, captions and abstract after code rerun. Cite FDIC field definitions and the official API, Polars and Spark execution documentation, state the AI tools used and their role in code drafting/review, and cite the exact repository commit SHA used to generate evidence.
