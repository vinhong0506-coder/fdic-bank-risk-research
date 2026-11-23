"""Fail-closed QA. Existing artifact files are NOT proof of a valid computation."""
from pathlib import Path
import json
import pandas as pd

def main():
    checks=[]
    def check(name,ok,reason):
        checks.append(dict(Check=name,Status='PASS' if ok else 'FAIL',Detail=reason))
    root=Path('data_raw/fdic')
    manifest=root/'manifest_financials.json'
    if manifest.exists():
        m=json.loads(manifest.read_text())
        check('170 verified quarters',len(m)==170 and all(v.get('complete') and v.get('sha256') for v in m.values()),f'entries={len(m)}; checksum revalidation needs separate step')
    else:check('170 verified quarters',False,'Missing manifest')
    panel=Path('data_processed/panel_pit.parquet')
    if panel.exists():
        try:
            import pyarrow.parquet as pq
            df=pd.read_parquet(panel,columns=['CERT','REPDTE','target_4q','split','label_reason','q_idx'])
            check('PIT panel integrity',not df.duplicated(['CERT','REPDTE']).any() and set(df.split.unique()).issubset({'DEV','EMBARGO','TEST','CENSORED'}),f'rows={len(df)}')
        except Exception as exc:check('PIT panel integrity',False,str(exc))
    else:check('PIT panel integrity',False,'Missing panel')
    eq=Path('artifacts/benchmark/engine/numeric_equivalence.json')
    if not eq.exists():eq=Path('artifacts/benchmark/spark_stage3/numeric_equivalence.json')
    if eq.exists():
        d=json.loads(eq.read_text());check('Spark/Polars equivalence',d.get('status')=='PASS',str(d))
    else:check('Spark/Polars equivalence',False,'Not run yet')
    files=['artifacts/model/dev_timeseries_cv.csv','artifacts/model/frozen_development_decisions.json',
           'artifacts/model/final_test_metrics.csv']
    for f in files:check(f,Path(f).exists(),'present' if Path(f).exists() else 'missing')
    mllib=Path('artifacts/model/spark_mllib_demo.csv')
    if mllib.exists():
        ml=pd.read_csv(mllib)
        check('MLlib actually executed','Status' not in ml.columns and 'Test_PR_AUC' in ml.columns,'SKIPPED is not a PASS')
    else:check('MLlib actually executed',False,'Missing Spark demo metrics')
    result=pd.DataFrame(checks)
    out=Path('artifacts/qa');out.mkdir(parents=True,exist_ok=True)
    result.to_csv(out/'qa_checklist.csv',index=False)
    print(result.to_markdown(index=False))
    if not result.Status.eq('PASS').all():raise SystemExit(1)
if __name__=='__main__':main()
