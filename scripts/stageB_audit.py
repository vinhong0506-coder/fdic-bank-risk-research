"""Read-only stage B data contract audit with manifest SHA-256 verification.

Only reads financials, original PIT, optional exit map, current feature-store schema.
Writes compact audit JSON/CSV in artifacts/stageB, never touches source data.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import polars as pl


def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as fp:
        for block in iter(lambda:fp.read(4*1024*1024),b''):
            h.update(block)
    return h.hexdigest()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--panel',default='data_processed/panel_pit.parquet')
    ap.add_argument('--raw',default='data_raw/fdic')
    ap.add_argument('--exit-map',default='data_reference/exit_mapping.csv')
    ap.add_argument('--out',default='artifacts/stageB/audit')
    ap.add_argument('--verify-sha',action='store_true',help='Rehash all 170 Parquet files')
    args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    errors=[];warnings=[];facts={}
    def fail(code,detail):errors.append({'code':code,'detail':str(detail)})
    def warn(code,detail):warnings.append({'code':code,'detail':str(detail)})
    raw=Path(args.raw);pit=Path(args.panel);mp=Path(args.exit_map)
    manifest_path=raw/'manifest_financials.json'
    if not manifest_path.exists():fail('MISSING_MANIFEST',manifest_path)
    else:
        m=json.loads(manifest_path.read_text(encoding='utf-8-sig'))
        facts['manifest_quarters']=len(m)
        if len(m)!=170:fail('MANIFEST_QUARTERS',f'Expected 170, got {len(m)}')
        outcomes=[]
        for q,e in sorted(m.items()):
            try:
                year=q[:4];qtr=(int(q[4:6])-1)//3+1
                file=raw/'financials'/f'YEAR={year}'/f'QUARTER=Q{qtr}'/f'REPDTE={q}.parquet'
                exists=file.is_file()
                complete=e.get('complete') is True
                expected=e.get('sha256')
                equal=None
                if exists and args.verify_sha and expected:equal=sha256_file(file).lower()==str(expected).lower()
                outcomes.append({'quarter':q,'file_exists':exists,'complete':complete,'sha_match':equal,'rows_manifest':e.get('rows')})
            except Exception as exc:fail('MANIFEST_ENTRY',f'{q}: {exc}')
        pd.DataFrame(outcomes).to_csv(out/'manifest_verification.csv',index=False)
        missing=sum(not x['file_exists'] for x in outcomes)
        incomplete=sum(not x['complete'] for x in outcomes)
        wrong=sum(x['sha_match'] is False for x in outcomes)
        facts.update(manifest_missing_files=missing,manifest_incomplete=incomplete,manifest_sha_mismatches=wrong,sha_revalidated=args.verify_sha)
        if missing or incomplete or wrong:fail('MANIFEST_INTEGRITY',f'files_missing={missing}, incomplete={incomplete}, sha_mismatch={wrong}')
        if not args.verify_sha:warn('SHA_NOT_VERIFIED','Run once with --verify-sha before claiming 170 files independently verified')
    for name in ('failures.parquet','institutions.parquet'):
        if not (raw/name).exists():fail('MISSING_RAW',raw/name)
    if mp.is_file():
        mapping=pd.read_csv(mp)
        required={'CERT','event_date','event_type'}
        if not required.issubset(mapping.columns):fail('EXIT_MAPPING_SCHEMA',sorted(required-set(mapping.columns)))
        else:
            facts['mapped_events']=len(mapping)
            facts['mapped_event_type_counts']=mapping['event_type'].astype(str).str.upper().value_counts(dropna=False).to_dict()
            if mapping[['CERT','event_date']].isna().any().any():fail('EXIT_MAPPING_MISSING_KEYS','Missing CERT or event_date')
            if mapping['CERT'].duplicated().any():warn('EXIT_MAPPING_DUP_CERT','Review mapping multiple events for one CERT; audit.py keeps first event')
    else:
        facts['mapped_events']=0
        warn('MAPPING_NOT_FOUND',f'{mp}: no adjudicated exits; all otherwise unknown exits stay censored')
    if not pit.exists():fail('MISSING_PANEL',pit)
    else:
        lf=pl.scan_parquet(str(pit))
        schema=set(lf.collect_schema().names())
        required={'CERT','REPDTE','quarter_date','q_idx','target_4q','split','label_reason','exit_type','failure_date','confirmed_exit_date','horizon_end_date'}
        missing=required-schema
        if missing:fail('PANEL_SCHEMA',sorted(missing))
        else:
            # Aggregate in Polars; no full pandas materialization of the entire panel.
            f=lf.select([
                pl.len().alias('rows'),pl.col('CERT').n_unique().alias('banks'),
                pl.col('target_4q').is_not_null().sum().alias('valid_labeled'),
                (pl.col('target_4q')==1).sum().alias('positive_bank_quarters'),
                (pl.col('label_reason')=='VALID_NON_FAILURE_EXIT').sum().alias('nonfailure_zero_rows'),
                (pl.col('label_reason')=='CENSORED_NON_FAILURE_EXIT').sum().alias('nonfailure_censored_rows'),
                (pl.col('label_reason')=='CENSORED_UNKNOWN_EXIT').sum().alias('unknown_censored_rows'),
                ((pl.col('label_reason')=='CENSORED_UNKNOWN_EXIT') & pl.col('target_4q').is_not_null()).sum().alias('unknown_censor_invalid'),
                ((pl.col('label_reason')=='VALID_NON_FAILURE_EXIT') & (pl.col('target_4q')!=0).fill_null(True)).sum().alias('nonfailure_zero_invalid'),
                (pl.col('quarter_date')>pl.col('confirmed_exit_date')).sum().alias('post_exit_rows'),
            ]).collect().to_dicts()[0]
            facts.update({k:int(v) if isinstance(v,(int,float)) and v is not None else v for k,v in f.items()})
            duplicate_count=lf.group_by('CERT','REPDTE').agg(pl.len().alias('n')).filter(pl.col('n')>1).select(pl.len()).collect().item()
            facts['duplicate_bank_quarter_keys']=int(duplicate_count)
            if duplicate_count:fail('PANEL_DUPLICATES',duplicate_count)
            for key in ('unknown_censor_invalid','nonfailure_zero_invalid','post_exit_rows'):
                if f[key]:fail('PANEL_CONTRACT_'+key.upper(),f[key])
            # All positive bank-quarters must have a confirmed failure strictly inside forecast horizon.
            invalid_positive=lf.filter((pl.col('target_4q')==1) & ~((pl.col('failure_date')>pl.col('quarter_date')) & (pl.col('failure_date')<=pl.col('horizon_end_date')))).select(pl.len()).collect().item()
            facts['invalid_positive_date_rows']=int(invalid_positive)
            if invalid_positive:fail('POSITIVE_LABEL_DATE',invalid_positive)
            if 'event_date' in schema:
                collisions=lf.filter(pl.col('event_date').is_not_null() & pl.col('failure_date').is_not_null() & (pl.col('event_date') < pl.col('failure_date'))).select(['CERT','event_date','failure_date','exit_type']).unique().collect()
                collisions.write_csv(out/'event_before_failure_review.csv')
                facts['event_before_failure_certs']=int(collisions['CERT'].n_unique()) if collisions.height else 0
                if collisions.height:warn('EVENT_BEFORE_FAILURE','Review event_before_failure_review.csv before interpreting failures as the first terminal event')
            if 'inst_end_date' in schema:
                c=lf.filter(pl.col('inst_end_date').is_not_null() & pl.col('failure_date').is_not_null() & (pl.col('inst_end_date') < pl.col('failure_date'))).select(['CERT','inst_end_date','failure_date','exit_type']).unique().collect()
                c.write_csv(out/'institution_end_before_failure_review.csv')
                facts['institution_end_before_failure_certs']=int(c['CERT'].n_unique()) if c.height else 0
                if c.height:warn('INSTITUTION_END_BEFORE_FAILURE','Review institution_end_before_failure_review.csv; possible lifecycle conflicts')
            spl=lf.group_by('split','label_reason').agg(pl.len().alias('rows'),pl.col('target_4q').is_not_null().sum().alias('valid'),(pl.col('target_4q')==1).sum().alias('positives')).collect().sort(['split','label_reason'])
            spl.write_csv(out/'split_label_reason.csv')
            if f['nonfailure_zero_rows'] and not f['nonfailure_censored_rows']:
                warn('LABEL_POLICY_DIFFERENCE','Current panel treats mapped merger/liquidation within horizon as 0; report may define them as censored')
            sens=lf.filter(pl.col('split')=='TEST').select([
                pl.col('target_4q').is_not_null().sum().alias('test_labeled'),
                (pl.col('label_reason')=='VALID_NON_FAILURE_EXIT').sum().alias('test_nonfailure_zero')]).collect().to_dicts()[0]
            facts.update({k:int(v) for k,v in sens.items()})
            if sens['test_nonfailure_zero']==0:warn('SENSITIVITY_NOOP','Excluding VALID_NON_FAILURE_EXIT from Test does not change the Test sample; report this clearly')
    if (Path('data_processed/features_pit.parquet')).exists():
        import pyarrow.parquet as pq
        cols=pq.ParquetFile('data_processed/features_pit.parquet').schema_arrow
        nanos=[f.name for f in cols if str(f.type).startswith('timestamp[ns')]
        facts['existing_feature_store_timestamp_ns_columns']=nanos
        if nanos:warn('FEATURE_PARQUET_NS',f'Spark 3.5 may reject these timestamp columns: {nanos}; rebuild features after patch')
    report={'created_utc':datetime.now(timezone.utc).isoformat(),'sources':{'panel':str(pit),'raw':str(raw),'exit_map':str(mp)},'facts':facts,'errors':errors,'warnings':warnings}
    report_file=out/'stageB_audit.json'
    report_file.write_text(json.dumps(report,indent=2,ensure_ascii=False,default=str),encoding='utf-8')
    print('=== FDIC STAGE B AUDIT ===')
    for k,v in facts.items():print('FACT',k,':',v)
    for x in warnings:print('WARN',x['code'],x['detail'])
    for x in errors:print('FAIL',x['code'],x['detail'])
    print('AUDIT:',report_file)
    if errors:
        print('STAGE_B_AUDIT_FAIL: fix structural errors before feature rebuild')
        return 2
    print('STAGE_B_AUDIT_PASS: warnings require methodological review')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
