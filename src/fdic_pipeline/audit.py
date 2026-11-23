"""FDIC data quality and lifecycle-aware bank-quarter panel.
Raw data are kept immutable. Unknown exits are censored rather than guessed.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import json
import numpy as np
import pandas as pd
import polars as pl

QUARTERS_END = pd.Timestamp('2026-06-30')
LAST_LABELED = pd.Timestamp('2025-06-30')


def _dates(s: pd.Series) -> pd.Series:
    cleaned = s.astype('string').str.strip().str.replace(r'\.0$', '', regex=True)
    # Try YYYYMMDD first, then fallback to mixed/MM-DD-YYYY/ISO formats
    d1 = pd.to_datetime(cleaned, format='%Y%m%d', errors='coerce')
    d2 = pd.to_datetime(cleaned, format='mixed', errors='coerce')
    return d1.fillna(d2)


def read_quarters(raw_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    paths = sorted((raw_dir / 'financials').rglob('*.parquet'))
    if len(paths) != 170:
        raise ValueError(f'Expected 170 financials files; found {len(paths)}')
    frames, sigs = [], []
    for p in paths:
        df = pd.read_parquet(p)
        sigs.append({'file': str(p), 'rows': len(df), 'schema': json.dumps({k:str(v) for k,v in df.dtypes.items()})})
        frames.append(df)
    fin = pd.concat(frames, ignore_index=True)
    for c in fin.columns.difference(['CERT','REPDTE','STNAME']):
        fin[c] = pd.to_numeric(fin[c], errors='coerce')
    fin['CERT'] = pd.to_numeric(fin['CERT'], errors='coerce').astype('Int64')
    fin['REPDTE'] = fin['REPDTE'].astype('string').str.replace('-', '', regex=False).str.replace(r'\.0$', '', regex=True)
    if fin[['CERT','REPDTE']].isna().any().any():
        raise ValueError('Null panel primary keys')
    if fin.duplicated(['CERT','REPDTE']).any():
        raise ValueError('Duplicate CERT/REPDTE; inspect before proceeding')
    return fin, pd.DataFrame(sigs)


def create_panel(raw_dir: Path, output_path: Path, mapping_path: Path | None = None,
                 audit_dir: Path = Path('artifacts/audit')) -> None:
    """Failures override institution exit metadata; merger/liquidation counted as nonfailures.
    Other/unknown exits censored. Horizon uses calendar quarter ends and bank's observation date.
    NOTE: bank identities require review if CERT is reused across historical charters.
    """
    audit_dir.mkdir(parents=True, exist_ok=True)
    fin, schemas = read_quarters(raw_dir)
    schemas.to_csv(audit_dir / 'schema_by_quarter.csv', index=False)
    fin['quarter_date'] = _dates(fin['REPDTE'])
    if fin['quarter_date'].isna().any():
        raise ValueError('Unparseable REPDTE')
    fin['q_idx'] = fin.quarter_date.dt.year * 4 + fin.quarter_date.dt.quarter - 1
    fails = pd.read_parquet(raw_dir / 'failures.parquet')
    inst = pd.read_parquet(raw_dir / 'institutions.parquet')
    fails['CERT'] = pd.to_numeric(fails['CERT'], errors='coerce').astype('Int64')
    fails['failure_date'] = _dates(fails['FAILDATE'])
    f = (fails.dropna(subset=['CERT','failure_date'])
         .groupby('CERT', as_index=False, observed=True)['failure_date'].min())
    f['CERT'] = f['CERT'].astype('Int64')
    inst['CERT'] = pd.to_numeric(inst['CERT'], errors='coerce').astype('Int64')
    inst['inst_end_date'] = _dates(inst['ENDEFYMD'])
    inst = inst.dropna(subset=['CERT']).groupby('CERT', observed=True, as_index=False)['inst_end_date'].min()
    inst['CERT'] = inst['CERT'].astype('Int64')
    # The optional map is a documented, manually adjudicated mapping, not a guess from codes.
    if mapping_path is not None and mapping_path.exists():
        m = pd.read_csv(mapping_path)
        needed = {'CERT','event_date','event_type'}
        if not needed.issubset(m.columns):
            raise ValueError(f'Exit map requires {needed}')
        m['CERT'] = pd.to_numeric(m['CERT'],errors='coerce').astype('Int64')
        m['event_date'] = _dates(m['event_date'])
        m['event_type'] = m['event_type'].str.upper().str.strip()
        valid = {'FAILURE','MERGER','VOLUNTARY_LIQUIDATION','OTHER_EXIT','UNKNOWN'}
        if (~m['event_type'].isin(valid)).any():
            raise ValueError('Unsupported event_type in mapping')
        m = m[m['event_type'] != 'FAILURE']  # official Failures table is authoritative
        m = m.sort_values('event_date').drop_duplicates('CERT',keep='first')
        m = m[['CERT','event_date','event_type']]
    else:
        m = pd.DataFrame({'CERT':pd.Series(dtype='Int64'), 'event_date':pd.Series(dtype='datetime64[ns]'), 'event_type':pd.Series(dtype='str')})
    # Reconciliation is based on raw failure events, not missingness assumptions.
    observed = set(fin.CERT.dropna().astype(int).unique())
    matched = set(f.CERT.astype(int).unique()) & observed
    reconciliation = {
        'raw_failure_rows':len(fails),
        'null_CERT_rows':int(fails.CERT.isna().sum()),
        'distinct_failure_CERTs':int(fails.CERT.nunique()),
        'duplicate_CERT_records':int(fails.CERT.notna().sum()-fails.CERT.nunique()),
        'distinct_valid_dated_failure_CERTs':len(f),
        'matched_failure_CERTs_in_financials':len(matched),
        'unmatched_failure_CERTs':len(set(f.CERT.astype(int))-observed),
        'warning':'Do not infer the reason for missing CERT from these counts.'
    }
    (audit_dir/'failure_reconciliation.json').write_text(json.dumps(reconciliation,indent=2))
    panel = fin.merge(f,on='CERT',how='left',validate='many_to_one')
    panel = panel.merge(inst,on='CERT',how='left',validate='many_to_one')
    panel = panel.merge(m,on='CERT',how='left',validate='many_to_one')
    # First known exit bounds reporting (failure, institution end or adjudicated exit).
    panel['confirmed_exit_date'] = panel[['failure_date','inst_end_date','event_date']].min(axis=1)
    zombies = panel.confirmed_exit_date.notna() & (panel.quarter_date > panel.confirmed_exit_date)
    removed = int(zombies.sum())
    panel = panel.loc[~zombies].copy()
    # Never use exit type or resolved failure status as predictors.
    panel['exit_type'] = np.select(
        [panel.failure_date.notna(), panel.event_type.isin(['MERGER','VOLUNTARY_LIQUIDATION']),
         panel.confirmed_exit_date.notna()],
        ['FAILURE','NON_FAILURE_EXIT','UNKNOWN_EXIT'],default='ACTIVE_OR_NOT_RECORDED')
    horizon = panel.quarter_date + pd.offsets.QuarterEnd(4)
    panel['horizon_end_date'] = horizon
    positive = panel.failure_date.gt(panel.quarter_date) & panel.failure_date.le(horizon)
    complete = horizon.le(QUARTERS_END) & panel.quarter_date.le(LAST_LABELED)
    non_failure_exit = (panel.exit_type.eq('NON_FAILURE_EXIT') &
                        panel.event_date.gt(panel.quarter_date) & panel.event_date.le(horizon))
    unknown_censor = (panel.exit_type.eq('UNKNOWN_EXIT') &
                     panel.confirmed_exit_date.gt(panel.quarter_date) & panel.confirmed_exit_date.le(horizon))
    # Contradictory institution termination preceding mapped nonfailure exit is unresolved.
    unknown_censor |= (panel.exit_type.eq('NON_FAILURE_EXIT') & panel.inst_end_date.notna() &
                       panel.inst_end_date.lt(panel.event_date) &
                       panel.inst_end_date.gt(panel.quarter_date) & panel.inst_end_date.le(horizon))
    panel['target_4q'] = pd.Series(pd.NA,index=panel.index,dtype='Int8')
    panel.loc[complete & (~unknown_censor), 'target_4q'] = 0
    panel.loc[complete & positive,'target_4q'] = 1
    panel['label_reason'] = np.select(
        [complete & positive, complete & unknown_censor,
         complete & non_failure_exit & ~positive,complete & ~positive & ~unknown_censor],
        ['VALID_FAILURE','CENSORED_UNKNOWN_EXIT','VALID_NON_FAILURE_EXIT','VALID_SURVIVED_4Q'],
        default='CENSORED_END_OF_PANEL')
    q = panel.quarter_date
    panel['split'] = np.select([q.le('2007-12-31'),q.between('2008-01-01','2008-12-31'),
                                q.between('2009-01-01','2025-06-30')],
                               ['DEV','EMBARGO','TEST'], default='CENSORED')
    if panel.duplicated(['CERT','REPDTE']).any():
        raise AssertionError('Panel key duplication after joins')
    flow = {'raw_financials':len(fin),'post_exit_rows_removed':removed,'clean_panel':len(panel),
            'dev_valid':int(((panel.split=='DEV') & panel.target_4q.notna()).sum()),
            'test_valid':int(((panel.split=='TEST') & panel.target_4q.notna()).sum())}
    (audit_dir/'panel_flow.json').write_text(json.dumps(flow,indent=2))
    split = panel.loc[panel.target_4q.notna()].groupby('split').agg(
        Valid_Rows=('CERT','size'), Pos_BankQuarters=('target_4q','sum'))
    split.to_csv(audit_dir/'temporal_split_summary.csv')
    output_path.parent.mkdir(parents=True,exist_ok=True)
    panel.to_parquet(output_path,index=False,compression='zstd')
    print(json.dumps(flow,indent=2))
    print('WARNING: Recomputed results may differ from previously published counts; update report only after verifying.')


def audit(raw_dir: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    fin, schemas = read_quarters(raw_dir)
    schemas.to_csv(output_dir/'schema_by_quarter.csv',index=False)
    numeric = fin.select_dtypes(include='number')
    numeric.describe(percentiles=[.01,.5,.99]).transpose().to_csv(output_dir/'numeric_extremes.csv')
    fin.isna().mean().mul(100).rename('missing_pct').to_csv(output_dir/'missingness.csv')
    fin.groupby('REPDTE').size().rename('rows').to_csv(output_dir/'quarterly_counts.csv')


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--raw',default='data_raw/fdic')
    ap.add_argument('--out',default='artifacts/audit')
    ap.add_argument('--panel',default='data_processed/panel_pit.parquet')
    ap.add_argument('--exit-map',default='data_reference/exit_mapping.csv')
    a=ap.parse_args()
    audit(Path(a.raw),Path(a.out))
    create_panel(Path(a.raw),Path(a.panel),Path(a.exit_map),Path(a.out))
