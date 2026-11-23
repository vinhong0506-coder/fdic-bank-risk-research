import numpy as np
import pandas as pd
from fdic_pipeline.workload import pandas_workload

def test_calendar_gap_blocks_rolling(monkeypatch):
    raw=pd.DataFrame({
        'CERT':[1]*5+[2]*4,
        'REPDTE':['20050331','20050630','20051231','20060331','20060630',
                  '20050331','20050630','20050930','20051231'],
        'ASSET':[100,110,120,130,140,100,100,100,100],
        'EQ':[10]*9,'DEP':[80]*9,'CHBAL':[10]*9,'SC':[10]*9,
        'LNLSNET':[50]*9,'ROA':[1,2,3,4,5,1,2,3,4],
    })
    monkeypatch.setattr(pd,'read_parquet',lambda *a,**kw:raw.copy())
    df=pandas_workload('unused.parquet')
    first=df[df.CERT==1].sort_values('REPDTE')
    assert np.isnan(first.iloc[2].asset_growth_qoq)
    assert np.isnan(first.iloc[3].roa_std_4q)
    assert np.isnan(first.iloc[4].roa_std_4q)
    assert np.isnan(first.iloc[4].asset_growth_yoy)  # q4 vs 4 rows ago is 5 quarters
    other=df[df.CERT==2].sort_values('REPDTE')
    assert np.isfinite(other.iloc[3].roa_std_4q)
