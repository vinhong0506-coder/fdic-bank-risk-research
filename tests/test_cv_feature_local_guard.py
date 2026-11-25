"""Fold-local feature-selection guard: Validation data cannot select features."""
import pandas as pd
from fdic_pipeline.model import select_fold_available_features


def test_fold_local_ignores_validation_future_availability():
    train = pd.DataFrame({
        "cap_ratio": [0.08, 0.09, 0.12],
        "nonperf_asset_ratio": [float("nan")] * 3,
    })
    valid = pd.DataFrame({
        "cap_ratio": [0.1, 0.08],
        "nonperf_asset_ratio": [0.23, 0.04],
    })
    candidates = ["cap_ratio", "nonperf_asset_ratio"]
    first = select_fold_available_features(train, candidates)
    valid.loc[:, "nonperf_asset_ratio"] = [0.9, 0.9]
    second = select_fold_available_features(train, candidates)
    assert first == second == ["cap_ratio"]
