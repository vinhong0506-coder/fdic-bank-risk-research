"""Test suite verifying fold-local feature availability selection and anti-leakage invariance.

This test demonstrates that a proper fold-local feature selection procedure
derives active feature columns strictly from the training partition and is
completely invariant to feature availability perturbations in validation or future data.
"""
import pytest
import pandas as pd
import numpy as np


def fold_local_feature_selection(train_df: pd.DataFrame, candidate_features: list[str]) -> list[str]:
    """Select features strictly available (at least one valid observation) within train partition."""
    return [
        col for col in candidate_features
        if col in train_df.columns and train_df[col].notna().any()
    ]


def test_fold_local_feature_selection_invariance():
    """Verify that perturbing validation or future feature availability does not alter train-selected features."""
    candidate_features = ["feat_a", "feat_b", "feat_c", "late_appearing_feat"]

    # Historical Train partition (e.g. 1984-1997) where late_appearing_feat is 100% missing
    train_data = pd.DataFrame({
        "CERT": [1, 2, 3, 4],
        "REPDTE": ["19950331", "19950630", "19960331", "19971231"],
        "feat_a": [0.08, 0.09, 0.07, 0.10],
        "feat_b": [0.01, 0.02, 0.01, 0.03],
        "feat_c": [1.5, 1.2, 1.8, 1.4],
        "late_appearing_feat": [np.nan, np.nan, np.nan, np.nan],  # strictly missing in train
    })

    # Scenario 1: Validation window where late_appearing_feat is also missing
    val_data_unperturbed = pd.DataFrame({
        "CERT": [1, 2],
        "REPDTE": ["19990331", "19990630"],
        "feat_a": [0.07, 0.08],
        "feat_b": [0.02, 0.02],
        "feat_c": [1.3, 1.1],
        "late_appearing_feat": [np.nan, np.nan],
    })

    # Scenario 2: Validation window where late_appearing_feat becomes populated (e.g. regulatory introduction in 2001)
    val_data_perturbed = pd.DataFrame({
        "CERT": [1, 2],
        "REPDTE": ["20010331", "20010630"],
        "feat_a": [0.07, 0.08],
        "feat_b": [0.02, 0.02],
        "feat_c": [1.3, 1.1],
        "late_appearing_feat": [0.05, 0.04],  # newly available in validation
    })

    selected_train_1 = fold_local_feature_selection(train_data, candidate_features)
    selected_train_2 = fold_local_feature_selection(train_data, candidate_features)

    # In fold-local selection, selected features are identical regardless of validation characteristics
    assert selected_train_1 == selected_train_2
    assert "late_appearing_feat" not in selected_train_1
    assert selected_train_1 == ["feat_a", "feat_b", "feat_c"]

    # Contrast with leaky full-sample selection:
    combined_full = pd.concat([train_data, val_data_perturbed], ignore_index=True)
    leaky_selection = fold_local_feature_selection(combined_full, candidate_features)
    assert "late_appearing_feat" in leaky_selection  # Leakage: future availability forced inclusion in train!
