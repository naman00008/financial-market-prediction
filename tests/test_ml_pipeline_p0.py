"""Unit and Integration Tests for ML Pipeline (Sections 1 through 4).

Verifies target creation, feature engineering, absence of bfill lookahead leakage,
chronological splitting, walk-forward validation, and classification model training.
"""

import numpy as np
import pandas as pd
import pytest

from src.feature_engineering import (
    add_technical_indicators,
    create_features,
    build_feature_groups,
    create_ablation_feature_sets,
)
from src.ml_dataset import create_next_day_direction_target, split_chronologically
from src.model_training import train_classification_models, evaluate_classification
from src.validation import generate_walk_forward_splits, evaluate_walk_forward
from src.dataset_builder import prepare_stock_df


@pytest.fixture
def dummy_stock_df():
    """Generate 100 rows of synthetic stock OHLCV data."""
    dates = pd.date_range("2023-01-01", periods=100, freq="D")
    np.random.seed(42)
    close_prices = 100.0 + np.cumsum(np.random.randn(100) * 2.0)
    high_prices = close_prices + np.abs(np.random.randn(100))
    low_prices = close_prices - np.abs(np.random.randn(100))
    open_prices = low_prices + (high_prices - low_prices) * np.random.rand(100)
    volume = np.random.randint(1000, 50000, size=100)

    return pd.DataFrame(
        {
            "Date": dates,
            "Open": open_prices,
            "High": high_prices,
            "Low": low_prices,
            "Close": close_prices,
            "Volume": volume,
        }
    )


def test_next_day_direction_target(dummy_stock_df):
    target_df = create_next_day_direction_target(dummy_stock_df)
    
    # Final row should be dropped because target is unknown
    assert len(target_df) == len(dummy_stock_df) - 1
    assert "Target" in target_df.columns
    assert "Next_Return" in target_df.columns

    # Verify target calculation for row 0
    row0_close = dummy_stock_df.loc[0, "Close"]
    row1_close = dummy_stock_df.loc[1, "Close"]
    expected_return = (row1_close / row0_close) - 1.0
    expected_target = 1 if expected_return > 0 else 0

    assert target_df.loc[0, "Next_Return"] == pytest.approx(expected_return)
    assert target_df.loc[0, "Target"] == expected_target


def test_no_bfill_leakage(dummy_stock_df):
    """Ensure technical indicators do NOT use bfill to populate initial NaN values."""
    tech_df = add_technical_indicators(dummy_stock_df, fillna_ffill_only=True)
    
    # 50-period SMA for row 0 MUST be NaN (since window size is 20/50 and no bfill is used)
    assert pd.isna(tech_df.loc[0, "SMA_50"])
    assert pd.isna(tech_df.loc[0, "SMA_20"])


def test_feature_groups_and_ablation():
    groups = build_feature_groups()
    assert "OHLCV" in groups
    assert "Trend" in groups
    assert "Momentum" in groups

    ablation_sets = create_ablation_feature_sets()
    assert "E1_OHLCV_Only" in ablation_sets
    assert "E4_Technical_Plus_Sentiment" in ablation_sets
    assert len(ablation_sets["E1_OHLCV_Only"]) < len(ablation_sets["E4_Technical_Plus_Sentiment"])


def test_chronological_split(dummy_stock_df):
    train, test = split_chronologically(dummy_stock_df, test_size=0.2)
    assert len(train) == 80
    assert len(test) == 20
    assert train["Date"].max() < test["Date"].min()


def test_walk_forward_splits():
    splits = generate_walk_forward_splits(n_samples=100, n_splits=5, min_train_ratio=0.5, window_type="expanding")
    assert len(splits) == 5
    for train_idx, val_idx in splits:
        assert train_idx.max() < val_idx.min()


def test_classification_model_training(dummy_stock_df):
    proc_df = prepare_stock_df(dummy_stock_df, ticker="TEST")
    train_df, test_df = split_chronologically(proc_df, test_size=0.2)

    groups = build_feature_groups()
    feature_cols = groups["OHLCV"] + groups["Lags"]

    results = train_classification_models(
        train_df=train_df,
        test_df=test_df,
        feature_cols=feature_cols,
        target_col="Target",
    )

    assert "baseline" in results
    assert "logistic_regression" in results
    assert "random_forest" in results
    
    metrics = results["logistic_regression"]["metrics"]
    assert "accuracy" in metrics
    assert "f1_score" in metrics
    assert "roc_auc" in metrics
    assert "confusion_matrix" in metrics
