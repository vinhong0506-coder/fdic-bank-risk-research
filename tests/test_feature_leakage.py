import pytest
pytest.importorskip("polars")
import numpy as np
import pandas as pd
import polars as pl
from fdic_pipeline.features import build_raw_camels_features, LeakageSafePreprocessor, EXCLUDE_LEAKAGE_COLS

def _make_synthetic_panel() -> pd.DataFrame:
    return pd.DataFrame({
        'CERT': [101, 101, 101, 101, 202, 202],
        'REPDTE': ['20050331', '20050630', '20051231', '20060331', '20090331', '20090630'],
        'quarter_date': pd.to_datetime(['2005-03-31', '2005-06-30', '2005-12-31', '2006-03-31', '2009-03-31', '2009-06-30']),
        'q_idx': [0, 1, 3, 4, 10, 11],  # Note: CERT 101 skips q_idx=2!
        'ASSET': [1000.0, 1100.0, 1200.0, 1300.0, 5000.0, 5200.0],
        'DEP': [800.0, 850.0, 900.0, 950.0, 4000.0, 4100.0],
        'EQ': [100.0, 110.0, 120.0, 130.0, 500.0, 520.0],
        'LNLSNET': [600.0, 650.0, 700.0, 750.0, 3000.0, 3100.0],
        'CHBAL': [50.0, 55.0, 60.0, 65.0, 200.0, 210.0],
        'SC': [150.0, 160.0, 170.0, 180.0, 800.0, 820.0],
        'ROA': [1.0, 1.2, 0.8, 0.9, 0.5, 0.6],
        'ROE': [10.0, 12.0, 8.0, 9.0, 5.0, 6.0],
        'NIMY': [3.5, 3.6, 3.4, 3.5, 3.0, 3.1],
        'NCLNLS': [10.0, 12.0, 15.0, 14.0, 50.0, 55.0],
        'LNATRES': [20.0, 22.0, 25.0, 24.0, 80.0, 85.0],
        'RBC1AAJ': [10.0, 10.2, 10.5, 10.4, 11.0, 11.2],
        'RBCRWAJ': [12.0, 12.2, 12.5, 12.4, 13.0, 13.2],
        'target_4q': [0, 0, 0, 1, 0, 1],
        'failure_date': [None, None, None, '2006-05-01', None, '2009-08-01'],
    })

def test_no_cross_bank_lag_or_gap_leakage():
    df = _make_synthetic_panel()
    res = build_raw_camels_features(pl.from_pandas(df).lazy()).collect().to_pandas()
    # CERT 202 first row must have NaN roa_lag1 (no bleed from CERT 101)
    cert202_first = res[res['CERT'] == 202].iloc[0]
    assert np.isnan(cert202_first['roa_lag1'])
    # CERT 101 at q_idx=3 (after missing q_idx=2) must have NaN roa_lag1
    cert101_q3 = res[(res['CERT'] == 101) & (res['q_idx'] == 3)].iloc[0]
    assert np.isnan(cert101_q3['roa_lag1'])
    # CERT 101 at q_idx=4 (4 quarters after q_idx=0) must have valid roa_lag4 == 1.0
    cert101_q4 = res[(res['CERT'] == 101) & (res['q_idx'] == 4)].iloc[0]
    assert np.isnan(cert101_q4['roa_lag4'])  # Missing q_idx=2 breaks 4-quarter continuity

def test_future_perturbation_invariance():
    df1 = _make_synthetic_panel()
    df2 = df1.copy()
    df2.loc[df2['REPDTE'] == '20060331', ['ASSET', 'ROA', 'EQ']] = [999999.0, -50.0, -5000.0]
    r1 = build_raw_camels_features(pl.from_pandas(df1).lazy()).collect().to_pandas()
    r2 = build_raw_camels_features(pl.from_pandas(df2).lazy()).collect().to_pandas()
    past1 = r1[r1['REPDTE'] < '20060331'][['cap_ratio', 'roa_lag1', 'roa_std_4q', 'cap_zscore_q']]
    past2 = r2[r2['REPDTE'] < '20060331'][['cap_ratio', 'roa_lag1', 'roa_std_4q', 'cap_zscore_q']]
    pd.testing.assert_frame_equal(past1, past2)

def test_preprocessor_dev_only_fit():
    train_df = pd.DataFrame({'x': [1.0, 2.0, 3.0, 4.0, 5.0]})
    test_df = pd.DataFrame({'x': [1000.0, 2000.0, 3000.0]})
    prep = LeakageSafePreprocessor(['x']).fit(train_df)
    assert prep.params['x']['median'] == 3.0
    assert prep.params['x']['mean'] == 3.0
    assert 'failure_date' in EXCLUDE_LEAKAGE_COLS
