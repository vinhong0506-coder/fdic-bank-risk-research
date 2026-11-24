import ast
import pytest
from scripts.stageB_safe_patch import change_features, change_model


def test_features_patch_is_valid_and_idempotent():
    before="def example():\n    pl.from_pandas(final_df).write_parquet(out_parquet, compression='zstd')\n"
    after,status=change_features(before)
    assert status=='PATCH_FEATURE_TIMESTAMP_US'
    assert "cast_time_unit('us')" in after
    ast.parse(after)
    assert change_features(after)==(after,'ALREADY_PATCHED_FEATURE_TIMESTAMP_US')


def test_model_patch_is_fail_closed_and_locks_test_before_writing():
    before='''def run_spark_mllib_demo():
    try:
        pass
    except Exception as exc:
        pd.DataFrame([{"Status": f"SKIPPED: {exc}"}]).to_csv(out_dir / "spark_mllib_demo.csv", index=False)

def run_modeling_pipeline(pit_path: Path, raw_dir: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
'''
    after,status=change_model(before)
    assert 'PATCH_MLLIB_FAIL_CLOSED' in status
    assert 'PATCH_EARLY_TEST_GUARD' in status
    assert 'raise RuntimeError' in after
    assert after.index('final_test_metrics.csv') > after.index('def run_modeling_pipeline')
    ast.parse(after)
    again,newstatus=change_model(after)
    assert again==after
    assert 'ALREADY_FAIL_CLOSED' in newstatus and 'ALREADY_EARLY_TEST_GUARD' in newstatus


def test_unknown_local_changes_are_not_overwritten():
    with pytest.raises(ValueError):
        change_features('def example():\n    pass\n')
    with pytest.raises(ValueError):
        change_model('def run_spark_mllib_demo():\n    pass\n')
