"""Honest ML dataset construction for next-trading-day direction prediction.

Target definition (fixed for all experiments, never changed silently):
    Target(t) = 1 if Close(t+1) > Close(t), else 0
    Next_Return(t) = Close(t+1) / Close(t) - 1

Only information available at the end of session t may be used to predict
Target(t). The final row of every series has an unknown next day and is dropped.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def create_next_day_direction_target(
    df: pd.DataFrame,
    close_col: str = "Close",
    target_col: str = "Target",
) -> pd.DataFrame:
    """Attach next-day direction label and next-day return, then drop the last row.

    The shift is applied on a chronologically sorted frame; rows are aligned so
    that Target at row t encodes movement of session t+1 relative to session t.
    """
    df = df.copy()
    if close_col not in df.columns:
        raise ValueError(f"DataFrame must contain '{close_col}'")

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"]).sort_values("Date", kind="stable").reset_index(drop=True)

    close = pd.to_numeric(df[close_col], errors="coerce")

    next_close = close.shift(-1)
    df["Next_Return"] = (next_close / close) - 1.0
    df[target_col] = (next_close > close).astype(int)

    # The final row has no next session: its label would be fabricated.
    df = df.iloc[:-1].reset_index(drop=True)
    return df


# Model features are deliberately scale-free (no raw price levels, no same-day
# OHLC). Every value is computable from data at or before the end of session t.
MODEL_FEATURES: list[str] = [
    # Lagged returns
    "Return_1d", "Return_2d", "Return_3d", "Return_5d", "Return_10d", "Return_20d",
    # Trend (relative to moving averages, not price levels)
    "Price_vs_SMA20", "Price_vs_SMA50", "SMA_Ratio_20_50",
    # Momentum oscillators
    "RSI_14", "WILLR_14",
    # Volatility (scale-free forms)
    "ATR_Pct", "BB_Width_20", "BB_Pct_20", "Rolling_Vol_10", "Rolling_Vol_20",
    # Volume dynamics
    "Volume_Change_1d", "Relative_Volume_20",
]

EXCLUDED_FROM_MODEL = [
    # Raw same-day price levels: leakage risk for same-day targets and
    # non-stationary for cross-period generalisation.
    "Open", "High", "Low", "Close", "Volume",
    "SMA_20", "SMA_50", "EMA_20", "EMA_50",
    "ATR_14", "BBM_20_2.0", "BBU_20_2.0", "BBL_20_2.0",
    "MACD_12_26_9", "MACDs_12_26_9", "MACDh_12_26_9",
    "Volume_SMA_20",
]


def build_model_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add scale-free derivatives of the indicator block (ATR_Pct) and return
    the frame with all MODEL_FEATURES present and finite."""
    df = df.copy()
    if "ATR_14" in df.columns and "Close" in df.columns:
        df["ATR_Pct"] = df["ATR_14"] / (pd.to_numeric(df["Close"], errors="coerce") + 1e-9)
    else:
        df["ATR_Pct"] = np.nan

    missing = [c for c in MODEL_FEATURES if c not in df.columns]
    if missing:
        raise ValueError(f"Feature engineering incomplete; missing columns: {missing}")

    df[MODEL_FEATURES] = df[MODEL_FEATURES].replace([np.inf, -np.inf], np.nan)
    return df


def verify_no_lookahead(features: pd.DataFrame, target_col: str = "Target") -> None:
    """Leakage guard: the model feature matrix must contain only pre-defined
    scale-free columns and must not include any same-day OHLC or target-derived
    column. Raises on violation."""
    forbidden = set(EXCLUDED_FROM_MODEL) | {target_col, "Next_Return", "Date", "Ticker"}
    violations = [c for c in features.columns if c in forbidden]
    if violations:
        raise ValueError(f"Leakage: forbidden columns entered the feature set: {violations}")
