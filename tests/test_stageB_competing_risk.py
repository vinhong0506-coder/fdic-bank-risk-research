import sys
import json
import pytest
pl=pytest.importorskip('polars')
from scripts import stageB_competing_risk


def test_censor_policy_preserves_original_and_does_not_overwrite(tmp_path,monkeypatch):
    original=tmp_path/'original.parquet'
    target=tmp_path/'new.parquet'
    pl.DataFrame({'CERT':[1,2,3], 'REPDTE':['20050331']*3,
                  'split':['DEV']*3,'target_4q':[0,0,1],
                  'label_reason':['VALID_NON_FAILURE_EXIT','VALID_SURVIVED_4Q','VALID_FAILURE']}).write_parquet(original)
    monkeypatch.setattr(sys,'argv',['stageB_competing_risk.py','--source',str(original),'--out',str(target)])
    assert stageB_competing_risk.main()==0
    a=pl.read_parquet(target)
    assert a['target_4q'][0] is None
    assert a['label_reason'][0]=='CENSORED_NON_FAILURE_EXIT'
    assert a['target_4q'][1]==0 and a['target_4q'][2]==1
    assert pl.read_parquet(original)['target_4q'][0]==0
    with pytest.raises(FileExistsError):stageB_competing_risk.main()
    m=json.loads((target.parent/'label_policy.json').read_text(encoding='utf-8'))
    assert m['modified_bank_quarters']==1
