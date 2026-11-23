"""Identical PIT risk-computation benchmark for Polars and Spark.

Quarter index is used to forbid treating non-consecutive observations as consecutive.
Window std uses ddof=1, full 4 observed, consecutive calendar quarters.
"""
from __future__ import annotations

COLS = ('CERT','REPDTE','ASSET','EQ','DEP','CHBAL','SC','LNLSNET','ROA')
OUTPUT = ('CERT','REPDTE','capital_ratio','loan_asset_ratio','liquidity_ratio',
          'asset_growth_qoq','asset_growth_yoy','roa_std_4q','cap_zscore_pit')


def polars_workload(path: str):
    import polars as pl
    lf = pl.scan_parquet(path).select([pl.col(c) for c in COLS]).with_columns(
        pl.col('CERT').cast(pl.Int64),
        pl.col('REPDTE').cast(pl.Utf8).str.replace(r'\.0$', '').str.replace_all('-', '').str.strptime(pl.Date, format='%Y%m%d', strict=True).alias('REPDTE'),
        *[pl.col(c).cast(pl.Float64, strict=False) for c in COLS[2:]],
    )
    lf = lf.with_columns(
        (pl.col('REPDTE').dt.year() * 4 + ((pl.col('REPDTE').dt.month()-1)//3)).alias('_qid')
    ).sort(['CERT','REPDTE'])
    lf = lf.with_columns(
        pl.col('ASSET').shift(1).over('CERT').alias('_a1'),
        pl.col('ASSET').shift(4).over('CERT').alias('_a4'),
        pl.col('_qid').shift(1).over('CERT').alias('_q1'),
        pl.col('_qid').shift(3).over('CERT').alias('_q3'),
        pl.col('_qid').shift(4).over('CERT').alias('_q4'),
        pl.col('ROA').rolling_std(window_size=4, min_periods=4, ddof=1).over('CERT').alias('_roa_std'),
    )
    lf = lf.with_columns(
        pl.when(pl.col('ASSET')>0).then(pl.col('EQ')/pl.col('ASSET')).alias('capital_ratio'),
        pl.when(pl.col('ASSET')>0).then(pl.col('LNLSNET')/pl.col('ASSET')).alias('loan_asset_ratio'),
        pl.when(pl.col('DEP')>0).then((pl.col('CHBAL')+pl.col('SC'))/pl.col('DEP')).alias('liquidity_ratio'),
        pl.when((pl.col('_qid')-pl.col('_q1')==1)&(pl.col('_a1')>0)).then(pl.col('ASSET')/pl.col('_a1')-1).alias('asset_growth_qoq'),
        pl.when((pl.col('_qid')-pl.col('_q4')==4)&(pl.col('_a4')>0)).then(pl.col('ASSET')/pl.col('_a4')-1).alias('asset_growth_yoy'),
        pl.when(pl.col('_qid')-pl.col('_q3')==3).then(pl.col('_roa_std')).alias('roa_std_4q'),
    )
    lf = lf.with_columns(
        pl.col('capital_ratio').mean().over('REPDTE').alias('_mu'),
        pl.col('capital_ratio').std(ddof=1).over('REPDTE').alias('_sd'),
    ).with_columns(
        pl.when(pl.col('_sd')>0).then((pl.col('capital_ratio')-pl.col('_mu'))/pl.col('_sd')).alias('cap_zscore_pit')
    )
    return lf.select(OUTPUT)


def spark_workload(spark, path: str):
    from pyspark.sql import functions as F, Window
    df = spark.read.parquet(path).select(*COLS)
    df = df.select(F.col('CERT').cast('long').alias('CERT'),
                   F.to_date(F.regexp_replace(F.col('REPDTE').cast('string'),'-',''),'yyyyMMdd').alias('REPDTE'),
                   *[F.col(c).cast('double').alias(c) for c in COLS[2:]])
    qid = F.year('REPDTE')*F.lit(4) + F.floor((F.month('REPDTE')-1)/F.lit(3))
    df = df.withColumn('_qid', qid)
    w = Window.partitionBy('CERT').orderBy('REPDTE')
    w4 = w.rowsBetween(-3,0)
    peer = Window.partitionBy('REPDTE')
    df = (df.withColumn('_a1', F.lag('ASSET',1).over(w))
          .withColumn('_a4', F.lag('ASSET',4).over(w))
          .withColumn('_q1', F.lag('_qid',1).over(w))
          .withColumn('_q3', F.lag('_qid',3).over(w))
          .withColumn('_q4', F.lag('_qid',4).over(w))
          .withColumn('_roa_std', F.stddev_samp('ROA').over(w4))
          .withColumn('_roa_n', F.count('ROA').over(w4)))
    df = (df.withColumn('capital_ratio',F.when(F.col('ASSET')>0,F.col('EQ')/F.col('ASSET')))
          .withColumn('loan_asset_ratio',F.when(F.col('ASSET')>0,F.col('LNLSNET')/F.col('ASSET')))
          .withColumn('liquidity_ratio',F.when(F.col('DEP')>0,(F.col('CHBAL')+F.col('SC'))/F.col('DEP')))
          .withColumn('asset_growth_qoq',F.when((F.col('_qid')-F.col('_q1')==1)&(F.col('_a1')>0),F.col('ASSET')/F.col('_a1')-1))
          .withColumn('asset_growth_yoy',F.when((F.col('_qid')-F.col('_q4')==4)&(F.col('_a4')>0),F.col('ASSET')/F.col('_a4')-1))
          .withColumn('roa_std_4q',F.when((F.col('_qid')-F.col('_q3')==3)&(F.col('_roa_n')==4),F.col('_roa_std')))
          .withColumn('_mu',F.avg('capital_ratio').over(peer))
          .withColumn('_sd',F.stddev_samp('capital_ratio').over(peer)))
    df = df.withColumn('cap_zscore_pit',F.when(F.col('_sd')>0,(F.col('capital_ratio')-F.col('_mu'))/F.col('_sd')))
    return df.select(*OUTPUT)


def assert_equivalent(polars_df, spark_df, *, atol=1e-6, rtol=1e-8):
    """Materialization excluded from speed test. Spark toPandas requires finite comparison output."""
    import numpy as np
    import pandas as pd
    a = polars_df.to_pandas().sort_values(['CERT','REPDTE']).reset_index(drop=True)
    b = spark_df.toPandas().sort_values(['CERT','REPDTE']).reset_index(drop=True)
    a['REPDTE'] = pd.to_datetime(a['REPDTE']); b['REPDTE'] = pd.to_datetime(b['REPDTE'])
    assert len(a)==len(b), f'Row count mismatch: {len(a)} vs {len(b)}'
    pd.testing.assert_frame_equal(a[['CERT','REPDTE']],b[['CERT','REPDTE']],check_dtype=False)
    diffs={}
    for c in OUTPUT[2:]:
        av=pd.to_numeric(a[c],errors='coerce').to_numpy(dtype=float)
        bv=pd.to_numeric(b[c],errors='coerce').to_numpy(dtype=float)
        assert np.array_equal(np.isnan(av),np.isnan(bv)),f'Null mismatch: {c}'
        assert np.isfinite(av[~np.isnan(av)]).all() and np.isfinite(bv[~np.isnan(bv)]).all(),f'Inf: {c}'
        diffs[c]=float(np.max(np.abs(av-bv)[~np.isnan(av)])) if (~np.isnan(av)).any() else 0.
        np.testing.assert_allclose(av,bv,atol=atol,rtol=rtol,equal_nan=True,err_msg=c)
    return diffs


def pandas_workload(path: str):
    """Same calendar-strict workload. Identical null and ddof=1 conventions."""
    import numpy as np
    import pandas as pd
    df=pd.read_parquet(path,columns=list(COLS))
    df['CERT']=pd.to_numeric(df.CERT,errors='raise').astype('int64')
    df['REPDTE']=pd.to_datetime(df.REPDTE.astype(str).str.replace('-','',regex=False).str.replace(r'\.0$', '',regex=True),format='%Y%m%d')
    for c in COLS[2:]:df[c]=pd.to_numeric(df[c],errors='coerce').astype(float)
    df=df.sort_values(['CERT','REPDTE']).reset_index(drop=True)
    df['_qid']=df.REPDTE.dt.year*4+df.REPDTE.dt.quarter-1
    g=df.groupby('CERT',sort=False)
    a1=g.ASSET.shift(1); a4=g.ASSET.shift(4)
    gap1=(df['_qid']-g['_qid'].shift(1)).eq(1)
    gap4=(df['_qid']-g['_qid'].shift(4)).eq(4)
    gap3=(df['_qid']-g['_qid'].shift(3)).eq(3)
    def div(a,b):return (a/b.where(b>0)).replace([np.inf,-np.inf],np.nan)
    df['capital_ratio']=div(df.EQ,df.ASSET)
    df['loan_asset_ratio']=div(df.LNLSNET,df.ASSET)
    df['liquidity_ratio']=div(df.CHBAL+df.SC,df.DEP)
    df['asset_growth_qoq']=div(df.ASSET,a1).sub(1).where(gap1)
    df['asset_growth_yoy']=div(df.ASSET,a4).sub(1).where(gap4)
    df['roa_std_4q']=g.ROA.transform(lambda s:s.rolling(4,min_periods=4).std(ddof=1)).where(gap3)
    gp=df.groupby('REPDTE')['capital_ratio']
    mu=gp.transform('mean'); sd=gp.transform('std')
    df['cap_zscore_pit']=div(df.capital_ratio-mu,sd)
    return df[list(OUTPUT)]
