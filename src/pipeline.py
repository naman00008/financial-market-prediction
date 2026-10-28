"""End-to-end leakage-safe classification pipeline.

Design (documented in docs/PROBLEM_STATEMENT.md and docs/MODEL_EVALUATION.md):
- Dataset: per-ticker scale-free features (src/ml_dataset.MODEL_FEATURES) and a
  fixed next-day direction target.
- Split: chronological 70% train / 15% validation / 15% test per dataset.
- Model selection: walk-forward validation on the train+validation segment only.
- Final holdout: the test segment is evaluated exactly once per model, and is
  never used for hyperparameter or model selection.
- Persistence: joblib bundle (model + scaler + feature order) and a JSON
  metadata record for traceability.
"""

from __future__ import annotations

import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn

from src.data_preprocessing import load_stock_data
from src.feature_engineering import create_features
from src.ml_dataset import (
    MODEL_FEATURES,
    build_model_features,
    create_next_day_direction_target,
)
from src.model_training import train_classification_models, evaluate_classification
from src.validation import generate_walk_forward_splits

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = PROJECT_ROOT / "models"
RESULTS_DIR = PROJECT_ROOT / "results"


def _clean_for_json(obj):
    """Recursively convert numpy types to native Python types for clean JSON serialization."""
    if isinstance(obj, (np.floating, float)):
        return float(obj)
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {str(k): _clean_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean_for_json(v) for v in obj]
    return obj


def build_ticker_dataset(ticker: str) -> pd.DataFrame:
    """Raw CSV -> indicators -> scale-free features -> next-day target."""
    raw = load_stock_data(ticker)
    feat = create_features(raw)                # sorts by Date, drops warm-up NaNs
    feat = build_model_features(feat)          # adds ATR_Pct, validates columns
    feat = create_next_day_direction_target(feat)  # adds Target + Next_Return
    feat["Ticker"] = ticker
    return feat


def build_latest_feature_row(ticker: str) -> pd.DataFrame:
    """Same feature construction, but keeps the final raw session (whose target
    is unknown) so the persisted model can predict the next session from the
    most recent completed data."""
    raw = load_stock_data(ticker)
    feat = create_features(raw)
    feat = build_model_features(feat)
    feat["Ticker"] = ticker
    return feat


def split_chronological_three_way(
    df: pd.DataFrame, train_frac: float = 0.70, val_frac: float = 0.15
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    n = len(df)
    train_end = int(n * train_frac)
    val_end = int(n * (train_frac + val_frac))
    return (
        df.iloc[:train_end].reset_index(drop=True),
        df.iloc[train_end:val_end].reset_index(drop=True),
        df.iloc[val_end:].reset_index(drop=True),
    )


def walk_forward_model_selection(
    df: pd.DataFrame, n_splits: int = 4, random_state: int = 42
) -> dict:
    """Walk-forward CV across models on df (must be the train+val segment).

    Returns per-model mean/std accuracy and ROC-AUC across folds.
    """
    folds = generate_walk_forward_splits(
        n_samples=len(df), n_splits=n_splits, min_train_ratio=0.6
    )
    per_model: dict[str, list[dict]] = {}
    for train_idx, val_idx in folds:
        tr = df.iloc[train_idx].reset_index(drop=True)
        va = df.iloc[val_idx].reset_index(drop=True)
        res = train_classification_models(
            tr, va, MODEL_FEATURES, random_state=random_state
        )
        for name, info in res.items():
            per_model.setdefault(name, []).append(info["metrics"])

    summary = {}
    for name, metric_list in per_model.items():
        summary[name] = {
            "accuracy_mean": float(np.mean([m["accuracy"] for m in metric_list])),
            "accuracy_std": float(np.std([m["accuracy"] for m in metric_list])),
            "roc_auc_mean": float(np.mean([m["roc_auc"] for m in metric_list])),
            "roc_auc_std": float(np.std([m["roc_auc"] for m in metric_list])),
        }
    return {"n_splits": n_splits, "summary": summary}


def select_best_model(walk_forward_summary: dict) -> str:
    """Pick the model with the highest mean walk-forward ROC-AUC (accuracy as
    tie-breaker). Selection never uses the final test segment."""
    scored = {
        name: (stats["roc_auc_mean"], stats["accuracy_mean"])
        for name, stats in walk_forward_summary["summary"].items()
        if name != "baseline"
    }
    return max(scored, key=lambda k: scored[k])


def train_and_persist(
    dataset: pd.DataFrame,
    identifier: str,
    random_state: int = 42,
) -> dict:
    """Full train -> select -> holdout-evaluate -> persist run for one dataset."""
    train_df, val_df, test_df = split_chronological_three_way(dataset)
    fit_df = pd.concat([train_df, val_df], ignore_index=True)

    wf = walk_forward_model_selection(fit_df, random_state=random_state)
    best_name = select_best_model(wf)

    # Final models are trained on train+val only; test is scored once.
    results = train_classification_models(
        fit_df, test_df, MODEL_FEATURES, random_state=random_state
    )

    MODELS_DIR.mkdir(exist_ok=True)
    best_info = results[best_name]

    bundle = {
        "model": best_info["model"],
        "scaler": best_info.get("scaler"),
        "feature_cols": list(MODEL_FEATURES),
        "target_definition": "1 if Close(t+1) > Close(t) else 0",
        "identifier": identifier,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "random_state": random_state,
    }
    bundle_path = MODELS_DIR / f"{identifier}_direction.joblib"
    joblib.dump(bundle, bundle_path)

    metadata = {
        "identifier": identifier,
        "algorithm": best_name,
        "bundle_path": str(bundle_path.relative_to(PROJECT_ROOT)),
        "trained_at": bundle["trained_at"],
        "target_definition": bundle["target_definition"],
        "feature_cols": list(MODEL_FEATURES),
        "random_state": random_state,
        "rows_total": int(len(dataset)),
        "train_rows": int(len(fit_df)),
        "test_rows": int(len(test_df)),
        "train_period": [str(fit_df["Date"].min().date()), str(fit_df["Date"].max().date())]
        if "Date" in fit_df.columns
        else None,
        "test_period": [str(test_df["Date"].min().date()), str(test_df["Date"].max().date())]
        if "Date" in test_df.columns
        else None,
        "walk_forward_selection": wf,
        "holdout_metrics": {name: info["metrics"] for name, info in results.items()},
        "feature_importances": best_info.get("feature_importances"),
        "software": {
            "python": platform.python_version(),
            "scikit_learn": sklearn.__version__,
        },
    }
    meta_path = MODELS_DIR / f"{identifier}_metadata.json"
    meta_path.write_text(json.dumps(_clean_for_json(metadata), indent=2), encoding="utf-8")

    return {
        "identifier": identifier,
        "best_model": best_name,
        "walk_forward": wf,
        "holdout": {name: info["metrics"] for name, info in results.items()},
        "metadata_path": str(meta_path.relative_to(PROJECT_ROOT)),
        "bundle_path": str(bundle_path.relative_to(PROJECT_ROOT)),
    }


def load_model_bundle(identifier: str) -> dict | None:
    """Load a persisted model bundle; returns None when missing or unloadable."""
    path = MODELS_DIR / f"{identifier}_direction.joblib"
    if not path.is_file():
        return None
    try:
        return joblib.load(path)
    except Exception:
        return None


def predict_next_session(dataset: pd.DataFrame, bundle: dict) -> dict:
    """Produce the direction prediction for the most recent session in `dataset`.

    `dataset` must be a fully featured frame (build_ticker_dataset) whose last
    row is the latest completed session. Returns class, probability and the
    probability interpretation caveat.
    """
    if bundle is None:
        raise ValueError("No model bundle provided")
    row = dataset.iloc[[-1]]
    X = row[list(bundle["feature_cols"])]
    if bundle.get("scaler") is not None:
        X = bundle["scaler"].transform(X)
    prob_up = float(bundle["model"].predict_proba(X)[0, 1])
    return {
        "prediction": int(prob_up >= 0.5),
        "probability_up": prob_up,
        "as_of_date": str(row["Date"].iloc[0].date()) if "Date" in row.columns else None,
        "note": "Probability is an uncalibrated classifier score, not a true market probability.",
    }
