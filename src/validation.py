"""Chronological and Walk-Forward Validation pipeline for Time Series ML.

Provides zero-leakage time-series split routines (expanding & rolling window walk-forward validation)
and cross-validation evaluators.
"""

from __future__ import annotations

import math
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from src.model_training import train_classification_models, evaluate_classification


def split_chronologically(
    df: pd.DataFrame,
    test_size: float | int = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split rows in strict time order without shuffling or overlapping periods."""
    if len(df) < 2:
        raise ValueError("At least two rows are required for a chronological split")

    if isinstance(test_size, float):
        if not 0 < test_size < 1:
            raise ValueError("Float test_size must be between 0 and 1")
        test_rows = math.ceil(len(df) * test_size)
    elif isinstance(test_size, int) and test_size > 0:
        test_rows = test_size
    else:
        raise ValueError("test_size must be a positive integer or fraction")

    if test_rows >= len(df):
        raise ValueError("test_size must leave at least one training row")

    split_at = len(df) - test_rows
    train = df.iloc[:split_at].copy().reset_index(drop=True)
    test = df.iloc[split_at:].copy().reset_index(drop=True)
    return train, test


def generate_walk_forward_splits(
    n_samples: int,
    n_splits: int = 5,
    min_train_ratio: float = 0.5,
    window_type: str = "expanding",
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Generate chronological fold index pairs (train_idx, val_idx) for walk-forward validation.
    
    Args:
        n_samples: Total number of rows in dataset.
        n_splits: Number of walk-forward folds.
        min_train_ratio: Minimum fraction of dataset used in initial training window.
        window_type: 'expanding' (train starts at 0 and expands) or 'rolling' (fixed-size train window).
        
    Yields/Returns:
        List of (train_idx, val_idx) arrays.
    """
    if n_samples < 50:
        raise ValueError("At least 50 samples required for walk-forward validation")

    min_train_size = int(n_samples * min_train_ratio)
    val_pool_size = n_samples - min_train_size

    val_size = val_pool_size // n_splits
    if val_size < 5:
        raise ValueError(f"Fold validation size ({val_size}) too small for n_splits={n_splits}")

    folds = []
    for i in range(n_splits):
        val_start = min_train_size + i * val_size
        val_end = min_train_size + (i + 1) * val_size if i < n_splits - 1 else n_samples

        if window_type == "expanding":
            train_start = 0
        elif window_type == "rolling":
            train_start = i * val_size
        else:
            raise ValueError("window_type must be 'expanding' or 'rolling'")

        train_idx = np.arange(train_start, val_start)
        val_idx = np.arange(val_start, val_end)

        folds.append((train_idx, val_idx))

    return folds


def evaluate_walk_forward(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str = "Target",
    n_splits: int = 5,
    window_type: str = "expanding",
    random_state: int = 42,
) -> dict:
    """Evaluate classification models across multiple walk-forward chronological windows.
    
    Returns metrics per fold and aggregate statistics (mean and std) across folds.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' missing from DataFrame")

    splits = generate_walk_forward_splits(
        n_samples=len(df),
        n_splits=n_splits,
        min_train_ratio=0.5,
        window_type=window_type,
    )

    fold_results = []

    for fold_num, (train_idx, val_idx) in enumerate(splits, start=1):
        train_df = df.iloc[train_idx].reset_index(drop=True)
        val_df = df.iloc[val_idx].reset_index(drop=True)

        model_res = train_classification_models(
            train_df=train_df,
            test_df=val_df,
            feature_cols=feature_cols,
            target_col=target_col,
            random_state=random_state,
        )

        fold_record = {"fold": fold_num, "train_size": len(train_df), "val_size": len(val_df), "models": {}}

        for model_name, res in model_res.items():
            fold_record["models"][model_name] = res["metrics"]

        fold_results.append(fold_record)

    # Compute aggregate stats across folds for each model
    model_names = fold_results[0]["models"].keys()
    metric_names = ["accuracy", "precision", "recall", "f1_score", "roc_auc", "pr_auc"]

    summary = {}
    for m_name in model_names:
        summary[m_name] = {}
        for metric in metric_names:
            vals = [f["models"][m_name][metric] for f in fold_results]
            summary[m_name][f"{metric}_mean"] = float(np.mean(vals))
            summary[m_name][f"{metric}_std"] = float(np.std(vals))

    return {
        "n_splits": n_splits,
        "window_type": window_type,
        "fold_details": fold_results,
        "summary": summary,
    }
