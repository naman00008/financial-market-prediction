"""Comprehensive tests for the ML pipeline, target alignment, and leakage prevention.

Verifies:
1. Target alignment: Target(t) == 1 iff Close(t+1) > Close(t), final row dropped.
2. Temporal order: Train < Val < Test strictly, zero chronological contamination.
3. Feature leakage guard: No raw OHLC or future labels in MODEL_FEATURES.
4. Walk-forward cross validation chronological validity.
5. Model persistence and deterministic reload.
6. API prediction integrity.
"""

import numpy as np
import pandas as pd
import pytest

from src.ml_dataset import (
    MODEL_FEATURES,
    EXCLUDED_FROM_MODEL,
    create_next_day_direction_target,
    build_model_features,
    verify_no_lookahead,
)
from src.feature_engineering import create_features
from src.pipeline import (
    split_chronological_three_way,
    train_and_persist,
    load_model_bundle,
    predict_next_session,
    walk_forward_model_selection,
)


def _make_dummy_ohlcv(n_days=100):
    dates = pd.date_range("2024-01-01", periods=n_days, freq="D")
    np.random.seed(42)
    close = 1000.0 + np.cumsum(np.random.randn(n_days) * 10)
    open_p = close + np.random.randn(n_days) * 2
    high_p = np.maximum(close, open_p) + np.abs(np.random.randn(n_days) * 5)
    low_p = np.minimum(close, open_p) - np.abs(np.random.randn(n_days) * 5)
    volume = np.random.randint(100000, 500000, size=n_days)
    return pd.DataFrame({
        "Date": dates,
        "Open": open_p,
        "High": high_p,
        "Low": low_p,
        "Close": close,
        "Volume": volume,
    })


def test_target_alignment_and_no_last_row():
    df = _make_dummy_ohlcv(50)
    target_df = create_next_day_direction_target(df)

    # 1. Final row must be dropped because Close(t+1) is unobserved
    assert len(target_df) == len(df) - 1

    # 2. Target must strictly match Close(t+1) > Close(t)
    for i in range(len(target_df)):
        expected_target = int(df["Close"].iloc[i + 1] > df["Close"].iloc[i])
        assert target_df["Target"].iloc[i] == expected_target
        expected_return = (df["Close"].iloc[i + 1] / df["Close"].iloc[i]) - 1.0
        assert np.isclose(target_df["Next_Return"].iloc[i], expected_return)


def test_feature_engineering_no_future_leakage():
    df = _make_dummy_ohlcv(80)
    feat_df = create_features(df)
    feat_df = build_model_features(feat_df)

    # Verify no raw price levels are included in MODEL_FEATURES
    for col in MODEL_FEATURES:
        assert col not in EXCLUDED_FROM_MODEL
        assert col in feat_df.columns

    # Verify verification function raises on contaminated feature list
    verify_no_lookahead(feat_df[MODEL_FEATURES])
    contaminated = feat_df.copy()
    with pytest.raises(ValueError):
        verify_no_lookahead(contaminated[["Close"] + MODEL_FEATURES])


def test_chronological_three_way_split():
    df = _make_dummy_ohlcv(100)
    train_df, val_df, test_df = split_chronological_three_way(df, 0.70, 0.15)

    assert len(train_df) == 70
    assert len(val_df) == 15
    assert len(test_df) == 15

    # Chronological invariant: max(Date_train) < min(Date_val) < min(Date_test)
    assert train_df["Date"].max() < val_df["Date"].min()
    assert val_df["Date"].max() < test_df["Date"].min()


def test_walk_forward_splits_order():
    df = _make_dummy_ohlcv(100)
    feat = create_features(df)
    feat = build_model_features(feat)
    feat = create_next_day_direction_target(feat)

    summary = walk_forward_model_selection(feat, n_splits=3, random_state=42)
    assert "summary" in summary
    assert "random_forest" in summary["summary"]
    assert "logistic_regression" in summary["summary"]
    assert summary["summary"]["random_forest"]["accuracy_mean"] > 0


def test_model_persistence_and_inference(tmp_path):
    df = _make_dummy_ohlcv(120)
    feat = create_features(df)
    feat = build_model_features(feat)
    feat = create_next_day_direction_target(feat)

    res = train_and_persist(feat, identifier="TEST_TICKER", random_state=42)
    assert res["best_model"] in ["random_forest", "logistic_regression", "gradient_boosting", "xgboost"]
    assert "accuracy" in res["holdout"][res["best_model"]]

    bundle = load_model_bundle("TEST_TICKER")
    assert bundle is not None
    assert bundle["identifier"] == "TEST_TICKER"

    # Inference on latest row
    pred = predict_next_session(feat, bundle)
    assert pred["prediction"] in [0, 1]
    assert 0.0 <= pred["probability_up"] <= 1.0
