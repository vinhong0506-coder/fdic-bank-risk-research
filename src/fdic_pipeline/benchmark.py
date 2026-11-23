"""Independent-process benchmark: python -m fdic_pipeline.benchmark --help."""
from __future__ import annotations
import argparse, csv, json, os, subprocess, sys, time, threading
from pathlib import Path
import psutil


def monitor(cmd, env):
    start=time.perf_counter()
    proc=subprocess.Popen(cmd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    max_rss=0; stop=threading.Event()
    def poll():
        nonlocal max_rss
        while not stop.wait(.025):
            try:
                p=psutil.Process(proc.pid)
                rss=p.memory_info().rss
                for c in p.children(recursive=True):
                    try: rss+=c.memory_info().rss
                    except psutil.Error: pass
                max_rss=max(max_rss,rss)
            except psutil.Error: break
    th=threading.Thread(target=poll,daemon=True); th.start()
    stdout,stderr=proc.communicate()
    stop.set();th.join()
    if proc.returncode:
        raise RuntimeError(f'Benchmark failure {cmd}:\n{stderr[-5000:]}')
    return time.perf_counter()-start,max_rss/1024**2,stdout,stderr


def worker(args):
    if args.engine=='polars':
        from .workload import polars_workload
        import polars as pl
        t=time.perf_counter(); lf=polars_workload(args.input)
        if args.plan: Path(args.plan).write_text(lf.explain(optimized=True),encoding='utf-8')
        from polars import col, lit
        digest_row=lf.select([pl.len().alias('_rows')]+[col(c).fill_null(0).sum().alias(c) for c in ('capital_ratio','loan_asset_ratio','liquidity_ratio','asset_growth_qoq','asset_growth_yoy','roa_std_4q','cap_zscore_pit')]).collect().to_dicts()[0]
        rows=int(digest_row.pop('_rows')); digest=digest_row
        elapsed=time.perf_counter()-t
    elif args.engine=='pandas':
        from .workload import pandas_workload
        t=time.perf_counter()
        frame=pandas_workload(args.input)
        digest={c:float(frame[c].fillna(0).sum()) for c in ('capital_ratio','loan_asset_ratio','liquidity_ratio','asset_growth_qoq','asset_growth_yoy','roa_std_4q','cap_zscore_pit')}
        rows=len(frame); elapsed=time.perf_counter()-t
    else:
        from pyspark.sql import SparkSession
        from .workload import spark_workload
        spark=SparkSession.builder.master(args.master).appName('BFT65B_FDIC_Benchmark').config('spark.sql.shuffle.partitions',str(args.partitions)).getOrCreate()
        spark.sparkContext.setLogLevel('ERROR')
        t=time.perf_counter(); df=spark_workload(spark,args.input)
        if args.plan:
            # JVM query execution: includes actual optimized logical and physical plans.
            Path(args.plan).write_text(df._jdf.queryExecution().toString(),encoding='utf-8')
        rows=None # computed from materialized aggregate below
        from pyspark.sql import functions as F
        digest=df.agg(F.count(F.lit(1)).alias('_rows'), *[F.sum(F.coalesce(F.col(c),F.lit(0.0))).alias(c) for c in ('capital_ratio','loan_asset_ratio','liquidity_ratio','asset_growth_qoq','asset_growth_yoy','roa_std_4q','cap_zscore_pit')]).collect()[0].asDict()
        rows=int(digest.pop('_rows'))
        elapsed=time.perf_counter()-t
        spark.stop()
    print(json.dumps({'engine':args.engine,'rows':rows,'compute_seconds':elapsed,'digest':digest}))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',default='data_processed/panel_pit.parquet')
    ap.add_argument('--out',default='artifacts/benchmark/spark_stage3')
    ap.add_argument('--engine',choices=['polars','pandas','spark'])
    ap.add_argument('--worker',action='store_true')
    ap.add_argument('--master',default='local[*]')
    ap.add_argument('--partitions',type=int,default=8)
    ap.add_argument('--repeats',type=int,default=3)
    ap.add_argument('--scales',default='1,2,5,10')
    ap.add_argument('--plan')
    args=ap.parse_args()
    if args.worker: return worker(args)
    import polars as pl
    from .workload import polars_workload,spark_workload,assert_equivalent,pandas_workload
    from pyspark.sql import SparkSession
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    # Validate full base output, once, never include in benchmark times.
    spark=SparkSession.builder.master(args.master).appName('BFT65B_FDIC_Verification').config('spark.sql.shuffle.partitions',str(args.partitions)).getOrCreate()
    spark.sparkContext.setLogLevel('ERROR')
    plout=polars_workload(args.input).collect()
    # Pandas equivalence at full scale (null masks and numerical values).
    import numpy as np
    import pandas as pd
    pdout=pandas_workload(args.input).sort_values(['CERT','REPDTE']).reset_index(drop=True)
    plpdf=plout.to_pandas().sort_values(['CERT','REPDTE']).reset_index(drop=True)
    pd.testing.assert_frame_equal(pdout[['CERT','REPDTE']],plpdf[['CERT','REPDTE']],check_dtype=False)
    for c in pdout.columns.difference(['CERT','REPDTE']):
        np.testing.assert_allclose(pdout[c].to_numpy(dtype=float),plpdf[c].to_numpy(dtype=float),atol=1e-6,rtol=1e-8,equal_nan=True,err_msg=c)
    maxdiff=assert_equivalent(plout,spark_workload(spark,args.input))
    spark.stop()
    (out/'numeric_equivalence.json').write_text(json.dumps({'status':'PASS','max_abs_diff_by_feature':maxdiff},indent=2))
    rows=[]; base=pl.read_parquet(args.input)
    # Each replica gets a NEW, non-overlapping pseudo-bank ID.
    certmax=int(base['CERT'].max())+1
    for k in map(int,args.scales.split(',')):
        if k<1:raise ValueError('Scale must be >= 1')
        path=out/f'synthetic_{k}x.parquet'
        if k==1: path=Path(args.input)
        else:
            frames=[]
            for j in range(k):frames.append(base.with_columns((pl.col('CERT').cast(pl.Int64)+j*certmax).alias('CERT')))
            pl.concat(frames).write_parquet(path,compression='zstd')
        for engine in ('pandas','polars','spark'):
            for run in range(1,args.repeats+1):
                plan=str(out/f'{engine}_{k}x_plan.txt') if run==1 else None
                cmd=[sys.executable,'-m','fdic_pipeline.benchmark','--worker','--engine',engine,
                     '--input',str(path),'--master',args.master,'--partitions',str(args.partitions)]
                if plan:cmd+=['--plan',plan]
                wall,ram,stdout,stderr=monitor(cmd,os.environ.copy())
                data = None
                for line in reversed(stdout.splitlines()):
                    line = line.strip()
                    if not line.startswith('{'):
                        continue
                    try:
                        candidate = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(candidate, dict) and all(k in candidate for k in ('engine','rows','compute_seconds','digest')):
                        data = candidate
                        break
                if data is None:
                    debug_file = out / f'worker_{engine}_{k}x_run{run}_debug.txt'
                    debug_file.write_text('STDOUT:\n'+stdout+'\nSTDERR:\n'+stderr,encoding='utf-8')
                    raise RuntimeError(f'No valid worker JSON. See {debug_file}')
                rows.append(dict(engine=engine,scale=k,run=run,wall_seconds=wall,compute_seconds=data['compute_seconds'],peak_process_tree_rss_mb=ram,rows=data['rows']))
                print(f'{engine:7} {k}x run={run}: {wall:.3f}s, {ram:.0f}MiB, rows={data["rows"]}')
        if k!=1:path.unlink(missing_ok=True)
    import pandas as pd
    d=pd.DataFrame(rows);d.to_csv(out/'benchmark_runs.csv',index=False)
    s=d.groupby(['engine','scale'],as_index=False).agg(median_wall_seconds=('wall_seconds','median'),median_peak_rss_mb=('peak_process_tree_rss_mb','median'),rows=('rows','first'))
    s.to_csv(out/'benchmark_summary.csv',index=False)
    print('\n'+s.to_markdown(index=False,floatfmt='.3f'))
    print('WARNING: process-tree RSS is sampling-based, not OS-global RAM nor an out-of-memory threshold.')

if __name__=='__main__': main()
