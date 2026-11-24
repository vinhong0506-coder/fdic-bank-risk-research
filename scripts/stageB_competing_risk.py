"""Create an isolated censored-merger sensitivity panel (never overwrite original).

Requires adjudicated VALID_NON_FAILURE_EXIT rows from baseline audit.
This is a binary classification censoring sensitivity, NOT a competing-risk hazard model.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import polars as pl


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',default='data_processed/panel_pit.parquet')
    p.add_argument('--out',default='artifacts/stageB/censored_sensitivity/panel_pit_censor_nonfailure.parquet')
    args=p.parse_args()
    inp=Path(args.source);out=Path(args.out)
    if not inp.is_file():raise FileNotFoundError(inp)
    if out.exists():raise FileExistsError(f'Will not overwrite existing sensitivity panel: {out}')
    out.parent.mkdir(parents=True,exist_ok=True)
    base=pl.scan_parquet(str(inp))
    sch=set(base.collect_schema().names())
    required={'target_4q','label_reason','split','CERT','REPDTE'}
    if not required.issubset(sch):raise ValueError(f'Missing fields: {required-sch}')
    zero=pl.col('label_reason')=='VALID_NON_FAILURE_EXIT'
    bad=base.filter(zero & ((pl.col('target_4q')!=0).fill_null(True))).select(pl.len()).collect().item()
    if bad:raise AssertionError(f'{bad} mapped non-failure rows do not have expected 0 label')
    n=base.filter(zero).select(pl.len()).collect().item()
    if n==0:
        print('NO_MAPPED_NONFAILURE_LABELS: sensitivity would be a no-op. No file written.')
        return 3
    changed=(base.with_columns(
        pl.when(zero).then(pl.lit(None,dtype=pl.Int8)).otherwise(pl.col('target_4q')).alias('target_4q'),
        pl.when(zero).then(pl.lit('CENSORED_NON_FAILURE_EXIT')).otherwise(pl.col('label_reason')).alias('label_reason')
    ))
    # Write to temporary target; atomic replace only after successful write.
    temp=out.with_suffix('.tmp.parquet')
    if temp.exists():raise FileExistsError(f'Remove stale temporary file after inspection: {temp}')
    try:
        changed.sink_parquet(temp,compression='zstd')
        temp.replace(out)
    except Exception:
        temp.unlink(missing_ok=True)
        raise
    summary=changed.group_by('split','label_reason').agg(pl.len().alias('rows'),pl.col('target_4q').is_not_null().sum().alias('valid')).collect().sort(['split','label_reason'])
    summary.write_csv(out.parent/'censored_policy_summary.csv')
    (out.parent/'label_policy.json').write_text(json.dumps({'policy':'censor_mapped_nonfailure_within_4q','baseline_path':str(inp),'sensitivity_path':str(out),'modified_bank_quarters':int(n),'note':'Sensitivity panel only; not automatically adopted as primary model target. No feature/model outputs were changed.'},indent=2),encoding='utf-8')
    print(f'SENSITIVITY_PANEL_PASS: recoded {n} mapped nonfailure bank-quarters to null')
    print('Output:',out)
    return 0

if __name__=='__main__':raise SystemExit(main())
