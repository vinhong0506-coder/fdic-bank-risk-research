"""Synthetic lifecycle regression tests. Requires polars and pyarrow in project venv."""
from pathlib import Path
import json
import pandas as pd
import pytest
pytest.importorskip('polars')
pytest.importorskip('pyarrow')
from fdic_pipeline import audit


def test_failure_merger_unknown_and_zombies(tmp_path,monkeypatch):
    raw=tmp_path/'raw';raw.mkdir()
    quarters=['20050331','20050630','20050930','20051231','20060331','20060630','20260331']
    fin=pd.DataFrame([{'CERT':cert,'REPDTE':date,'ASSET':100.0,'EQ':10.0}
                      for cert in [10,20,30,40] for date in quarters])
    # failure bank 10 at 2006Q2, merger 20 at 2006Q2, unknown end bank 30 in 2006Q2
    failures=pd.DataFrame([{'CERT':10,'FAILDATE':'20060615','COST':5,'QBFASSET':100}])
    institutions=pd.DataFrame([{'CERT':10,'ENDEFYMD':'20060615'},
                               {'CERT':20,'ENDEFYMD':'20060615'},
                               {'CERT':30,'ENDEFYMD':'20060615'},
                               {'CERT':40,'ENDEFYMD':None}])
    failures.to_parquet(raw/'failures.parquet');institutions.to_parquet(raw/'institutions.parquet')
    mp=tmp_path/'mapping.csv'
    pd.DataFrame([{'CERT':20,'event_date':'2006-06-15','event_type':'MERGER'}]).to_csv(mp,index=False)
    monkeypatch.setattr(audit,'read_quarters',lambda _: (fin,pd.DataFrame([{'file':'mock','rows':len(fin),'schema':'mock'}])))
    out=tmp_path/'panel.parquet'
    audit.create_panel(raw,out,mp,tmp_path/'artifacts')
    p=pd.read_parquet(out)
    def row(cert,date):return p[(p.CERT==cert)&(p.REPDTE==date)].iloc[0]
    assert row(10,'20050930').target_4q==1
    assert row(20,'20050930').target_4q==0
    assert row(20,'20050930').label_reason=='VALID_NON_FAILURE_EXIT'
    assert pd.isna(row(30,'20050930').target_4q)
    assert pd.isna(row(40,'20260331').target_4q)
    assert not ((p.CERT==10)&(p.REPDTE=='20060630')).any()
    assert p.q_idx.nunique()==len(quarters)


def test_no_duplicate_repeated_failure_join(tmp_path,monkeypatch):
    raw=tmp_path/'raw';raw.mkdir()
    fin=pd.DataFrame([{'CERT':3,'REPDTE':'20050331','ASSET':5},
                      {'CERT':3,'REPDTE':'20050630','ASSET':6}])
    pd.DataFrame([{'CERT':3,'FAILDATE':'20051231'},
                  {'CERT':3,'FAILDATE':'20051231'}]).to_parquet(raw/'failures.parquet')
    pd.DataFrame([{'CERT':3,'ENDEFYMD':'20051231'}]).to_parquet(raw/'institutions.parquet')
    monkeypatch.setattr(audit,'read_quarters',lambda _: (fin,pd.DataFrame([{'file':'mock','rows':2,'schema':'mock'}])))
    audit.create_panel(raw,tmp_path/'panel.parquet',audit_dir=tmp_path/'audit')
    assert len(pd.read_parquet(tmp_path/'panel.parquet'))==2
