"""Opt-in rebuild of feature parquet in an isolated stage B directory, not primary artifacts."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import pyarrow.parquet as pq
from fdic_pipeline.features import build_feature_dataset

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--panel',required=True)
    p.add_argument('--out',required=True)
    p.add_argument('--art-dir',required=True)
    args=p.parse_args()
    input_file=Path(args.panel);output_file=Path(args.out);art_dir=Path(args.art_dir)
    if not input_file.is_file():raise FileNotFoundError(input_file)
    if output_file.exists():raise FileExistsError(f'Will not overwrite feature store: {output_file}')
    if art_dir.exists() and any(art_dir.iterdir()):raise FileExistsError(f'Artifact directory not empty: {art_dir}')
    build_feature_dataset(input_file,output_file,art_dir)
    schema=pq.ParquetFile(output_file).schema_arrow
    bad=[field.name for field in schema if str(field.type).startswith('timestamp[ns')]
    if bad:raise AssertionError(f'Spark-incompatible timestamp[ns] present: {bad}')
    params=json.loads((art_dir/'preprocessor_dev_params.json').read_text(encoding='utf-8'))
    names=set(schema.names)
    missing=[c for feature in params for c in (feature,feature+'_isna') if c not in names]
    if missing:raise AssertionError(f'Feature contract missing processed columns: {missing}')
    print(f'FEATURE_STORE_PASS: {len(params)} base features; {len(params)*2} processed features; no timestamp[ns]')
    print('Output:',output_file)

if __name__=='__main__':main()
