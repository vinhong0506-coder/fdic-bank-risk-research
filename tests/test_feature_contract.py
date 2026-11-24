"""The versioned 30-feature specification is shared by all pipelines."""
from fdic_pipeline.features import SELECTED_CAMELS_FEATURES
from fdic_pipeline.model import BASE_FEATURES


def test_identical_feature_contract():
    assert len(SELECTED_CAMELS_FEATURES) == 30
    assert len(set(SELECTED_CAMELS_FEATURES)) == 30
    assert "eff_ratio" not in SELECTED_CAMELS_FEATURES
    assert BASE_FEATURES == list(SELECTED_CAMELS_FEATURES)
    assert len([c for f in SELECTED_CAMELS_FEATURES for c in (f, f + "_isna")]) == 60
