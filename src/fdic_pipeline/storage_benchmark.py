"""Compare CSV and Parquet encodings on one downloaded quarter; reports bytes and write/read times."""
import argparse, time
from pathlib import Path
import pandas as pd

def timed(fn):
    t=time.perf_counter(); result=fn(); return result,time.perf_counter()-t

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input',required=True); ap.add_argument('--out',default='artifacts/storage'); a=ap.parse_args()
    source=Path(a.input); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    df=pd.read_parquet(source); rows=len(df)
    variants=[]
    csv_path=out/'sample.csv'; _,wt=timed(lambda:df.to_csv(csv_path,index=False)); _,rt=timed(lambda:pd.read_csv(csv_path))
    variants.append({'format':'CSV','rows':rows,'bytes':csv_path.stat().st_size,'write_s':wt,'read_s':rt})
    for codec in ['snappy','zstd','gzip']:
        p=out/f'sample_{codec}.parquet'; _,wt=timed(lambda:df.to_parquet(p,index=False,compression=codec)); _,rt=timed(lambda:pd.read_parquet(p))
        variants.append({'format':f'Parquet-{codec}','rows':rows,'bytes':p.stat().st_size,'write_s':wt,'read_s':rt})
    result=pd.DataFrame(variants); result['compression_ratio_vs_csv']=result.bytes.iloc[0]/result.bytes
    result.to_csv(out/'storage_benchmark.csv',index=False); print(result.to_markdown(index=False))
if __name__=='__main__': main()
