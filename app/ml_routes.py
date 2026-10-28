"""Honest ML API routes backed by the leakage-safe pipeline.

Endpoints:
- GET /api/ml/features            -> feature definitions and exclusion rationale
- GET /api/ml/models              -> persisted model inventory
- GET /api/ml/evaluate/{ticker}   -> walk-forward selection + holdout metrics
- GET /api/ml/predict/{ticker}    -> next-session direction prediction

A model bundle persisted by scripts/run_experiments.py is used when present;
otherwise the pipeline trains one on first request and caches it in-process.
"""

from __future__ import annotations

import json
import threading
import traceback
from functools import lru_cache

from fastapi import APIRouter, HTTPException

from src.ml_dataset import MODEL_FEATURES, EXCLUDED_FROM_MODEL
from src.pipeline import (
    MODELS_DIR,
    build_latest_feature_row,
    build_ticker_dataset,
    load_model_bundle,
    predict_next_session,
    train_and_persist,
)

router = APIRouter(prefix="/api/ml")

_lock = threading.Lock()


@lru_cache(maxsize=64)
def _ensure_bundle(ticker: str) -> dict:
    """Return the persisted bundle for a ticker, training one if absent."""
    bundle = load_model_bundle(ticker)
    if bundle is not None:
        return bundle
    with _lock:
        bundle = load_model_bundle(ticker)
        if bundle is not None:
            return bundle
        train_and_persist(build_ticker_dataset(ticker), identifier=ticker)
    bundle = load_model_bundle(ticker)
    if bundle is None:
        raise HTTPException(status_code=500, detail="Model training failed")
    return bundle


@lru_cache(maxsize=64)
def _metadata(ticker: str) -> dict:
    path = MODELS_DIR / f"{ticker}_metadata.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    _ensure_bundle(ticker)
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/features")
async def get_features():
    return {
        "target_definition": "1 if Close(t+1) > Close(t) else 0",
        "features": MODEL_FEATURES,
        "excluded_and_why": {
            col: "Raw price level: same-day values leak the target and levels are "
            "non-stationary across years"
            for col in EXCLUDED_FROM_MODEL
        },
    }


@router.get("/models")
async def list_models():
    items = []
    if MODELS_DIR.is_dir():
        for path in sorted(MODELS_DIR.glob("*_metadata.json")):
            try:
                meta = json.loads(path.read_text(encoding="utf-8"))
                items.append(
                    {
                        "identifier": meta["identifier"],
                        "algorithm": meta["algorithm"],
                        "trained_at": meta["trained_at"],
                        "train_period": meta.get("train_period"),
                        "test_period": meta.get("test_period"),
                        "holdout_accuracy": meta["holdout_metrics"]
                        .get(meta["algorithm"], {})
                        .get("accuracy"),
                    }
                )
            except Exception:
                continue
    return {"models": items}


@router.get("/evaluate/{ticker}")
async def evaluate_ticker(ticker: str):
    try:
        meta = _metadata(ticker.upper())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No model or data for '{ticker}'")
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Evaluation lookup failed")
    return {"status": "success", "evaluation": meta}


@router.get("/predict/{ticker}")
async def predict_ticker(ticker: str):
    try:
        t = ticker.upper()
        bundle = _ensure_bundle(t)
        latest = build_latest_feature_row(t)
        pred = predict_next_session(latest, bundle)

        meta = _metadata(t)
        best = meta["algorithm"]
        holdout = meta["holdout_metrics"].get(best, {})

        return {
            "status": "success",
            "ticker": t,
            "model": {
                "identifier": meta["identifier"],
                "algorithm": best,
                "trained_at": meta["trained_at"],
                "holdout_accuracy": holdout.get("accuracy"),
                "holdout_roc_auc": holdout.get("roc_auc"),
                "test_period": meta.get("test_period"),
                "target_definition": meta["target_definition"],
            },
            "prediction": pred,
            "limitations": [
                "A direction prediction is not a price forecast and not investment advice.",
                "The probability is an uncalibrated model score.",
                "Historical holdout accuracy was close to the class baseline; treat the "
                "output as a research demonstration.",
            ],
        }
    except HTTPException:
        raise
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Prediction failed")
