"""Leakage-safe dataset preparation for the primary direction task."""

from __future__ import annotations

import math

import pandas as pd


def create_next_day_direction_target(
    df: pd.DataFrame,
    close_col: str = "Close",
    target_col: str = "Target",
) -> pd.DataFrame:
    """Create a next-trading-day direction label from end-of-day prices.

    Features for row ``t`` remain unchanged; only the label uses the next
    available close. The final row is removed because its label is unknown.
    """
    if close_col not in df.columns:
        raise ValueError(f"DataFrame must contain a '{close_col}' column")

    result = df.copy()
    if "Date" in result.columns:
        result["Date"] = pd.to_datetime(result["Date"], errors="raise")
        result = result.sort_values("Date", kind="stable").reset_index(drop=True)
        if result["Date"].duplicated().any():
            raise ValueError("DataFrame contains duplicate dates")

    close = pd.to_numeric(result[close_col], errors="coerce")
    next_return = result[close_col].shift(-1).astype(float) / close - 1.0
    result[target_col] = (next_return > 0).astype("Int64")
    result["Next_Return"] = next_return

    result = result.loc[close.notna() & next_return.notna()].reset_index(drop=True)
    result[target_col] = result[target_col].astype("int64")
    return result


def split_chronologically(
    df: pd.DataFrame,
    test_size: float | int = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split rows in time order without shuffling or overlapping periods."""
    if len(df) < 2:
        raise ValueError("At least two rows are required for a chronological split")

    if isinstance(test_size, float):
        if not 0 < test_size < 1:
            raise ValueError("Float test_size must be between 0 and 1")
        test_rows = math.ceil(len(df) * test_size)
    elif isinstance(test_size, int) and test_size > 0:
        test_rows = test_size
    else:
        raise ValueError("test_size must be a positive integer or a fraction")

    if test_rows >= len(df):
        raise ValueError("test_size must leave at least one training row")

    split_at = len(df) - test_rows
    train = df.iloc[:split_at].copy()
    test = df.iloc[split_at:].copy()
    return train, test