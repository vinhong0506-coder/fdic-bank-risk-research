from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import polars as pl

EXCLUDE_LEAKAGE_COLS = {
    'CERT', 'REPDTE', 'STNAME', 'quarter_date', 'q_idx', 'horizon_end', 'horizon_end_date',
    'exit_type', 'failure_date', 'inst_end_date', 'confirmed_exit_date',
    'bkclass', 'est_date', 'target_4q', 'label_reason', 'split'
}

SELECTED_CAMELS_FEATURES = (
    'cap_ratio',
    'rbc_tier1',
    'rbc_total',
    'neg_equity_flag',
    'is_pre_basel',
    'npl_ratio',
    'reserve_coverage',
    'nonperf_asset_ratio',
    'ore_ratio',
    're_loan_share',
    'ci_loan_share',
    'nonix_asset_ratio',
    'roa',
    'roe',
    'nimy',
    'roa_lag1',
    'roa_lag4',
    'roa_diff_qoq',
    'roa_std_4q',
    'nimy_std_4q',
    'liq_asset_ratio',
    'liq_dep_ratio',
    'ldr',
    'brokered_dep_ratio',
    'log_asset',
    'asset_growth_qoq',
    'asset_growth_yoy',
    'cap_zscore_q',
    'roa_zscore_q',
    'npl_zscore_q',
)

def safe_div(num: pl.Expr, den: pl.Expr) -> pl.Expr:
    return pl.when(den.is_not_null() & (den > 0)).then(num / den).otherwise(None)

def run_supplemental_audits(raw_dir: Path, pit_path: Path, audit_dir: Path) -> None:
    audit_dir.mkdir(parents=True, exist_ok=True)
    pit = pl.read_parquet(pit_path)
    fails = pl.read_parquet(raw_dir / 'failures.parquet')

    # A. Reconcile 4,117 failure rows vs 3,585 matched CERTs
    pit_certs = set(pit['CERT'].unique().to_list())
    fails_clean = fails.with_columns([
        pl.col('CERT').cast(pl.Int64, strict=False),
        pl.col('FAILDATE').cast(pl.String).str.strip_chars().alias('fail_str')
    ])
    total_rows = len(fails_clean)
    null_cert = fails_clean.filter(pl.col('CERT').is_null()).height
    valid_fails = fails_clean.filter(pl.col('CERT').is_not_null())
    unique_fail_certs = valid_fails['CERT'].n_unique()
    dup_cert_rows = len(valid_fails) - unique_fail_certs
    in_pit = valid_fails.filter(pl.col('CERT').is_in(list(pit_certs)))['CERT'].n_unique()
    not_in_pit_df = valid_fails.filter(~pl.col('CERT').is_in(list(pit_certs)))
    not_in_pit_certs = not_in_pit_df['CERT'].n_unique()

    rec_df = pd.DataFrame([
        {'Category': 'Total rows in raw failures.parquet', 'Count': total_rows},
        {'Category': 'Rows with null/unassigned CERT', 'Count': null_cert},
        {'Category': 'Duplicate failure records for same CERT', 'Count': dup_cert_rows},
        {'Category': 'Unique failed CERTs matched in 1984Q1-2026Q2 Financials', 'Count': in_pit},
        {'Category': 'Unique failed CERTs absent from Financials (pre-1984 / non-filers)', 'Count': not_in_pit_certs},
    ])
    rec_df.to_csv(audit_dir / 'failure_reconciliation.csv', index=False)

    # B. Pre-Basel Zero-Value Audit for Capital Ratios (RBC1AAJ, RBCRWAJ) by Year
    rbc_audit = (
        pit.with_columns(pl.col('REPDTE').str.slice(0, 4).alias('year'))
        .group_by('year')
        .agg([
            pl.len().alias('n_obs'),
            (pl.col('RBC1AAJ') == 0.0).mean().mul(100).round(2).alias('rbc1_zero_pct'),
            pl.col('RBC1AAJ').is_null().mean().mul(100).round(2).alias('rbc1_null_pct'),
            (pl.col('RBCRWAJ') == 0.0).mean().mul(100).round(2).alias('rbcrwa_zero_pct'),
            pl.col('RBCRWAJ').is_null().mean().mul(100).round(2).alias('rbcrwa_null_pct'),
        ])
        .sort('year')
        .to_pandas()
    )
    rbc_audit.to_csv(audit_dir / 'capital_availability_by_year.csv', index=False)

def build_raw_camels_features(lf: pl.LazyFrame) -> pl.LazyFrame:
    schema_cols = set(lf.collect_schema().names())

    # Ensure q_idx exists for strict calendar-quarter gap checks
    base = lf.sort(['CERT', 'quarter_date'])
    if 'q_idx' not in schema_cols:
        base = base.with_columns((pl.col('quarter_date').dt.year()*4 + pl.col('quarter_date').dt.quarter() - 1).alias('q_idx'))

    exprs = [
        # C - Capital Adequacy
        safe_div(pl.col('EQ'), pl.col('ASSET')).alias('cap_ratio'),
        pl.col('RBC1AAJ').alias('rbc_tier1'),
        pl.col('RBCRWAJ').alias('rbc_total'),
        (pl.col('EQ') < 0).cast(pl.Float64).alias('neg_equity_flag'),
        (pl.col('REPDTE') < '19900331').cast(pl.Float64).alias('is_pre_basel'),

        # A - Asset Quality
        safe_div(pl.col('NCLNLS'), pl.col('LNLSNET')).alias('npl_ratio'),
        safe_div(pl.col('LNATRES'), pl.col('NCLNLS')).alias('reserve_coverage'),

        # M - Management Efficiency
        pl.col('EEFFR').alias('eff_ratio') if 'EEFFR' in schema_cols else pl.lit(None, dtype=pl.Float64).alias('eff_ratio'),

        # E - Earnings & Profitability
        pl.col('ROA').alias('roa'),
        pl.col('ROE').alias('roe'),
        pl.col('NIMY').alias('nimy'),

        # L - Liquidity
        safe_div(pl.col('CHBAL') + pl.col('SC'), pl.col('ASSET')).alias('liq_asset_ratio'),
        safe_div(pl.col('CHBAL') + pl.col('SC'), pl.col('DEP')).alias('liq_dep_ratio'),
        safe_div(pl.col('LNLSNET'), pl.col('DEP')).alias('ldr'),

        # S - Size & Sensitivity
        pl.when(pl.col('ASSET') > 0).then(pl.col('ASSET').log()).otherwise(None).alias('log_asset'),
    ]

    if {'P3ASSET', 'P9ASSET', 'NAASSET'}.issubset(schema_cols):
        exprs.append(safe_div(pl.col('P3ASSET') + pl.col('P9ASSET') + pl.col('NAASSET'), pl.col('ASSET')).alias('nonperf_asset_ratio'))
    if 'ORE' in schema_cols:
        exprs.append(safe_div(pl.col('ORE'), pl.col('ASSET')).alias('ore_ratio'))
    if {'LNRE', 'LNLSGR'}.issubset(schema_cols):
        exprs.append(safe_div(pl.col('LNRE'), pl.col('LNLSGR')).alias('re_loan_share'))
    if {'LNCI', 'LNLSGR'}.issubset(schema_cols):
        exprs.append(safe_div(pl.col('LNCI'), pl.col('LNLSGR')).alias('ci_loan_share'))
    if 'NONIX' in schema_cols:
        exprs.append(safe_div(pl.col('NONIX'), pl.col('ASSET')).alias('nonix_asset_ratio'))
    if 'BRO' in schema_cols:
        exprs.append(safe_div(pl.col('BRO'), pl.col('DEP')).alias('brokered_dep_ratio'))
    if 'COREDEP' in schema_cols:
        exprs.append(safe_div(pl.col('COREDEP'), pl.col('DEP')).alias('core_dep_ratio'))

    step1 = base.with_columns(exprs)

    # Calendar-strict temporal lags and rolling volatility (within CERT only)
    q_gap_1 = (pl.col('q_idx') - pl.col('q_idx').shift(1).over('CERT')) == 1
    q_gap_4 = (pl.col('q_idx') - pl.col('q_idx').shift(4).over('CERT')) == 4
    q_gap_3 = (pl.col('q_idx') - pl.col('q_idx').shift(3).over('CERT')) == 3

    step2 = step1.with_columns([
        pl.when(q_gap_1).then(pl.col('roa').shift(1).over('CERT')).otherwise(None).alias('roa_lag1'),
        pl.when(q_gap_4).then(pl.col('roa').shift(4).over('CERT')).otherwise(None).alias('roa_lag4'),
        pl.when(q_gap_1).then(pl.col('roa') - pl.col('roa').shift(1).over('CERT')).otherwise(None).alias('roa_diff_qoq'),
        pl.when(q_gap_1 & (pl.col('ASSET').shift(1).over('CERT') > 0))
          .then(pl.col('ASSET') / pl.col('ASSET').shift(1).over('CERT') - 1.0)
          .otherwise(None).alias('asset_growth_qoq'),
        pl.when(q_gap_4 & (pl.col('ASSET').shift(4).over('CERT') > 0))
          .then(pl.col('ASSET') / pl.col('ASSET').shift(4).over('CERT') - 1.0)
          .otherwise(None).alias('asset_growth_yoy'),
        pl.when(q_gap_3).then(pl.col('roa').rolling_std(window_size=4, min_samples=4, ddof=1).over('CERT')).otherwise(None).alias('roa_std_4q'),
        pl.when(q_gap_3).then(pl.col('nimy').rolling_std(window_size=4, min_samples=4, ddof=1).over('CERT')).otherwise(None).alias('nimy_std_4q'),
    ])

    # Industry-quarter relative z-scores (strictly point-in-time within each REPDTE)
    step3 = step2.with_columns([
        ((pl.col('cap_ratio') - pl.col('cap_ratio').mean().over('REPDTE')) /
         pl.when(pl.col('cap_ratio').std().over('REPDTE') > 0).then(pl.col('cap_ratio').std().over('REPDTE')).otherwise(None)).alias('cap_zscore_q'),
        ((pl.col('roa') - pl.col('roa').mean().over('REPDTE')) /
         pl.when(pl.col('roa').std().over('REPDTE') > 0).then(pl.col('roa').std().over('REPDTE')).otherwise(None)).alias('roa_zscore_q'),
        ((pl.col('npl_ratio') - pl.col('npl_ratio').mean().over('REPDTE')) /
         pl.when(pl.col('npl_ratio').std().over('REPDTE') > 0).then(pl.col('npl_ratio').std().over('REPDTE')).otherwise(None)).alias('npl_zscore_q'),
    ])

    # Assign frozen temporal split labels
    step4 = step3.with_columns([
        pl.when((pl.col('REPDTE') >= '19840331') & (pl.col('REPDTE') <= '20071231')).then(pl.lit('DEV'))
          .when((pl.col('REPDTE') >= '20080101') & (pl.col('REPDTE') <= '20081231')).then(pl.lit('EMBARGO'))
          .when((pl.col('REPDTE') >= '20090101') & (pl.col('REPDTE') <= '20250630')).then(pl.lit('TEST'))
          .otherwise(pl.lit('CENSORED'))
          .alias('split')
    ])
    return step4

class LeakageSafePreprocessor:
    def __init__(self, feature_cols: list[str], lower_q: float = 0.01, upper_q: float = 0.99):
        self.feature_cols = feature_cols
        self.lower_q = lower_q
        self.upper_q = upper_q
        self.params: dict[str, dict[str, float]] = {}

    def fit(self, df_train: pd.DataFrame) -> 'LeakageSafePreprocessor':
        self.params = {}
        for c in self.feature_cols:
            s = pd.to_numeric(df_train[c], errors='coerce').replace([np.inf, -np.inf], np.nan)
            valid = s.dropna()
            if len(valid) == 0:
                lo, hi, med, mean, std = 0.0, 0.0, 0.0, 0.0, 1.0
            else:
                lo = float(valid.quantile(self.lower_q))
                hi = float(valid.quantile(self.upper_q))
                clipped = valid.clip(lo, hi)
                med = float(clipped.median())
                filled = s.clip(lo, hi).fillna(med)
                mean = float(filled.mean())
                std = float(filled.std(ddof=0))
                if std <= 1e-12 or np.isnan(std):
                    std = 1.0
            self.params[c] = {'low': lo, 'high': hi, 'median': med, 'mean': mean, 'std': std}
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        out = pd.DataFrame(index=df.index)
        for c in self.feature_cols:
            p = self.params[c]
            s = pd.to_numeric(df[c], errors='coerce').replace([np.inf, -np.inf], np.nan)
            out[f'{c}_isna'] = s.isna().astype(np.float32)
            clipped = s.clip(p['low'], p['high']).fillna(p['median'])
            out[c] = ((clipped - p['mean']) / p['std']).astype(np.float32)
        return out

def build_feature_dataset(pit_path: Path, out_parquet: Path, feat_art_dir: Path) -> None:
    feat_art_dir.mkdir(parents=True, exist_ok=True)
    out_parquet.parent.mkdir(parents=True, exist_ok=True)

    lf = pl.scan_parquet(str(pit_path))
    raw_feat_df = build_raw_camels_features(lf).collect()

    meta_cols = ['CERT', 'REPDTE', 'quarter_date', 'q_idx', 'target_4q', 'label_reason', 'exit_type', 'split']
    meta_cols = [c for c in meta_cols if c in raw_feat_df.columns]

    # Select engineered CAMELS features (exclude raw unscaled levels except log_asset & engineered ratios)
    candidate_feats = list(SELECTED_CAMELS_FEATURES)
    # Choose feature availability exclusively from labeled DEV.
    # Test and EMBARGO must not determine the model feature set.
    dev_for_selection = raw_feat_df.filter(
        (pl.col("split") == "DEV")
        & pl.col("target_4q").is_not_null()
    )
    if dev_for_selection.height == 0:
        raise ValueError("No labeled DEV rows for feature selection")
    dev_valid_features = raw_feat_df.filter(
        (pl.col("split") == "DEV") & pl.col("target_4q").is_not_null()
    )
    if dev_valid_features.height == 0:
        raise ValueError("No labeled Development observations for feature selection")
    feature_cols = [
        c for c in candidate_feats
        if c in raw_feat_df.columns
        and dev_valid_features[c].null_count() < dev_valid_features.height
    ]
    omitted = sorted(set(candidate_feats)-set(feature_cols))
    (feat_art_dir/'omitted_all_missing_features.json').write_text(json.dumps(omitted,indent=2))

    pdf = raw_feat_df.select(meta_cols + feature_cols).to_pandas()
    dev_mask = (pdf['split'] == 'DEV') & (pdf['target_4q'].notna())

    prep = LeakageSafePreprocessor(feature_cols=feature_cols)
    prep.fit(pdf.loc[dev_mask, feature_cols])
    X_trans = prep.transform(pdf[feature_cols])

    final_df = pd.concat([pdf[meta_cols].reset_index(drop=True), X_trans.reset_index(drop=True)], axis=1)
    spark_safe = pl.from_pandas(final_df)
    ns_cols = [name for name, dtype in spark_safe.schema.items()
               if dtype == pl.Datetime('ns')]
    if ns_cols:
        spark_safe = spark_safe.with_columns(
            [pl.col(name).dt.cast_time_unit('us') for name in ns_cols]
        )
    spark_safe.write_parquet(out_parquet, compression='zstd')

    (feat_art_dir / 'preprocessor_dev_params.json').write_text(json.dumps(prep.params, indent=2), encoding='utf-8')
    pd.DataFrame({'feature': feature_cols, 'processed_col': feature_cols}).to_csv(feat_art_dir / 'feature_dictionary.csv', index=False)
    print(f'Saved features_pit.parquet: {len(final_df):,} rows x {final_df.shape[1]} cols ({len(feature_cols)} base CAMELS features + missing flags)')

if __name__ == '__main__':
    run_supplemental_audits(Path('data_raw/fdic'), Path('data_processed/panel_pit.parquet'), Path('artifacts/audit'))
    build_feature_dataset(Path('data_processed/panel_pit.parquet'), Path('data_processed/features_pit.parquet'), Path('artifacts/features'))
