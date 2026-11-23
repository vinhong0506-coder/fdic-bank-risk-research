"""Full-panel format benchmark. Outputs are newly measured; never hard-code findings."""
from __future__ import annotations
import argparse, gc, time
from pathlib import Path
import pandas as pd
from .audit import read_quarters

def timed(fn):
    t=time.perf_counter(); result=fn(); return result,time.perf_counter()-t

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--raw',default='data_raw/fdic')
    ap.add_argument('--out',default='artifacts/benchmark/storage_full')
    args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    df,_=read_quarters(Path(args.raw));n=len(df)
    methods=[('CSV',out/'panel.csv',None),('Parquet-snappy',out/'panel_snappy.parquet','snappy'),
             ('Parquet-zstd',out/'panel_zstd.parquet','zstd'),('Parquet-gzip',out/'panel_gzip.parquet','gzip')]
    rows=[]
    for name,p,codec in methods:
        if codec is None:
            _,write=timed(lambda:df.to_csv(p,index=False))
            gc.collect();read_df,read=timed(lambda:pd.read_csv(p))
        else:
            _,write=timed(lambda:df.to_parquet(p,index=False,compression=codec,engine='pyarrow'))
            gc.collect();read_df,read=timed(lambda:pd.read_parquet(p,engine='pyarrow'))
        if len(read_df)!=n:raise AssertionError(f'Row count changed for {name}')
        rows.append({'format':name,'rows':n,'bytes':p.stat().st_size,'write_s':write,'read_s':read})
        del read_df;gc.collect()
    tab=pd.DataFrame(rows)
    tab['compression_ratio_vs_csv']=tab['bytes'].iloc[0]/tab['bytes']
    tab.to_csv(out/'storage_benchmark.csv',index=False)
    print(tab.to_markdown(index=False,floatfmt='.3f'))
    print('Measured warm/cold status and hardware must be documented in report; one run is descriptive, not statistical confidence.')
if __name__=='__main__':main()
