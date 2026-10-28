"""Reproducible experiment runner for the Market ML case study.

Usage:
    python scripts/run_experiments.py eda       # data quality + EDA artifacts
    python scripts/run_experiments.py run       # train/evaluate all models
    python scripts/run_experiments.py all

Outputs:
    results/eda_summary.json, results/figures/*.png
    results/experiment_results.json
    results/data_quality.json
Models and metadata are persisted under models/ (gitignored).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_preprocessing import load_stock_data, list_nifty50_companies
from src.ml_dataset import MODEL_FEATURES
from src.pipeline import (
    RESULTS_DIR,
    build_ticker_dataset,
    train_and_persist,
    _clean_for_json,
)

FIGURES_DIR = RESULTS_DIR / "figures"

OHLCV = ["Open", "High", "Low", "Close", "Volume"]


def run_eda(tickers: list[str]) -> dict:
    RESULTS_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(exist_ok=True)

    per_ticker = {}
    quality = {
        "missing_ohlcv": 0,
        "duplicate_dates": 0,
        "invalid_dates": 0,
        "nonpositive_prices": 0,
        "ohlc_violations": 0,
        "total_rows": 0,
    }

    close_frames = []
    for t in tickers:
        df = load_stock_data(t)
        quality["total_rows"] += len(df)

        miss = int(df[OHLCV].isna().sum().sum())
        quality["missing_ohlcv"] += miss
        dup = int(df["Date"].duplicated().sum())
        quality["duplicate_dates"] += dup
        bad_dates = int(pd.to_datetime(df["Date"], errors="coerce").isna().sum())
        quality["invalid_dates"] += bad_dates
        nonpos = int((df[OHLCV[:-1]] <= 0).sum().sum())
        quality["nonpositive_prices"] += nonpos
        viol = int(
            ((df["High"] < df["Low"]) | (df["High"] < df["Close"]) | (df["Low"] > df["Close"])).sum()
        )
        quality["ohlc_violations"] += viol

        close = df.set_index("Date")["Close"]
        ret = close.pct_change().dropna()
        up = (ret > 0).mean()

        per_ticker[t] = {
            "rows": int(len(df)),
            "start": str(df["Date"].min().date()),
            "end": str(df["Date"].max().date()),
            "missing_ohlcv": miss,
            "duplicate_dates": dup,
            "daily_return_mean": float(ret.mean()),
            "daily_return_std": float(ret.std()),
            "annualized_vol": float(ret.std() * np.sqrt(252)),
            "total_return_pct": float((close.iloc[-1] / close.iloc[0] - 1) * 100),
            "up_day_fraction": float(up),
        }
        close_frames.append(close.rename(t))

        if t in ("RELIANCE", "TCS", "INFY"):
            fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
            axes[0].plot(close.index, close.values, lw=0.9)
            axes[0].set_title(f"{t} — closing price (Yahoo Finance, adjusted close)")
            axes[1].plot(ret.index, ret.values, lw=0.5)
            axes[1].set_title("Daily returns")
            rv = ret.rolling(20).std() * np.sqrt(252)
            axes[2].plot(rv.index, rv.values, lw=0.9)
            axes[2].set_title("20-day rolling annualised volatility")
            fig.tight_layout()
            fig.savefig(FIGURES_DIR / f"eda_{t.lower()}.png", dpi=120)
            plt.close(fig)

    panel_close = pd.concat(close_frames, axis=1).sort_index()
    corr = panel_close.pct_change().dropna().corr()
    fig, ax = plt.subplots(figsize=(9, 8))
    im = ax.imshow(corr.values, vmin=0, vmax=1, cmap="viridis")
    ax.set_xticks(range(len(corr)), corr.columns, rotation=90, fontsize=5)
    ax.set_yticks(range(len(corr)), corr.index, fontsize=5)
    ax.set_title("Pearson correlation of daily returns across the 45-ticker panel")
    fig.colorbar(im, shrink=0.8)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "eda_correlation_panel.png", dpi=120)
    plt.close(fig)

    # Build one training dataset to show target balance and feature distributions
    sample = build_ticker_dataset("RELIANCE")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].bar(["Down/Flat (0)", "Up (1)"], sample["Target"].value_counts().sort_index().values)
    axes[0].set_title("RELIANCE next-day direction class balance")
    axes[1].hist(sample["Return_1d"].dropna(), bins=60)
    axes[1].set_title("RELIANCE Return_1d distribution")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "eda_target_balance_reliance.png", dpi=120)
    plt.close(fig)

    summary = {
        "n_tickers": len(tickers),
        "target_definition": "1 if Close(t+1) > Close(t) else 0",
        "quality": quality,
        "per_ticker": per_ticker,
    }
    (RESULTS_DIR / "data_quality.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def run_experiments(tickers: list[str]) -> dict:
    RESULTS_DIR.mkdir(exist_ok=True)

    # 1) Pooled panel experiment: one chronological split across all tickers.
    #    The pooled train/val/test periods are identical for every ticker, so
    #    cross-sectional comparisons are on the same holdout window.
    print("Building pooled panel dataset ...")
    frames = [build_ticker_dataset(t) for t in tickers]
    panel = pd.concat(frames, ignore_index=True).sort_values("Date").reset_index(drop=True)
    n = len(panel)
    train_end, val_end = int(n * 0.70), int(n * 0.85)

    from src.model_training import train_classification_models
    from src.validation import generate_walk_forward_splits

    fit_df = panel.iloc[:val_end].reset_index(drop=True)
    test_df = panel.iloc[val_end:].reset_index(drop=True)

    print("Pooled walk-forward selection ...")
    folds = generate_walk_forward_splits(len(fit_df), n_splits=4, min_train_ratio=0.6)
    wf_per_model: dict[str, list[dict]] = {}
    for tr_idx, va_idx in folds:
        res = train_classification_models(
            fit_df.iloc[tr_idx].reset_index(drop=True),
            fit_df.iloc[va_idx].reset_index(drop=True),
            MODEL_FEATURES,
        )
        for name, info in res.items():
            wf_per_model.setdefault(name, []).append(info["metrics"])

    print("Pooled final holdout evaluation ...")
    holdout = train_classification_models(fit_df, test_df, MODEL_FEATURES)

    pooled = {
        "rows": int(n),
        "train_rows": int(len(fit_df)),
        "test_rows": int(len(test_df)),
        "train_period": [str(fit_df["Date"].min().date()), str(fit_df["Date"].max().date())],
        "test_period": [str(test_df["Date"].min().date()), str(test_df["Date"].max().date())],
        "walk_forward": {
            name: {
                "accuracy_mean": float(np.mean([m["accuracy"] for m in ms])),
                "accuracy_std": float(np.std([m["accuracy"] for m in ms])),
                "roc_auc_mean": float(np.mean([m["roc_auc"] for m in ms])),
                "roc_auc_std": float(np.std([m["roc_auc"] for m in ms])),
            }
            for name, ms in wf_per_model.items()
        },
        "holdout": {name: info["metrics"] for name, info in holdout.items()},
        "feature_importances": {
            name: info.get("feature_importances")
            for name, info in holdout.items()
            if info.get("feature_importances")
        },
    }

    # Per-ticker breakdown of the pooled test period
    per_ticker_test = {}
    ticker_col = test_df["Ticker"].values
    for name, info in holdout.items():
        if name == "baseline":
            continue
        accs = []
        for t in tickers:
            mask = ticker_col == t
            if mask.sum() < 20:
                continue
            y_t = test_df.loc[mask, "Target"].values
            p_t = info["y_pred_prob"][mask]
            pred_t = (p_t >= 0.5).astype(int)
            acc = float(np.mean(y_t == pred_t))
            accs.append((t, acc))
        per_ticker_test[name] = dict(accs)

    # 2) Per-ticker experiments with persistence (uses validation segment for
    #    model selection; holdout scored once).
    per_ticker_runs = {}
    for t in tickers:
        t0 = time.time()
        ds = build_ticker_dataset(t)
        run = train_and_persist(ds, identifier=t)
        per_ticker_runs[t] = run
        acc = run["holdout"][run["best_model"]]["accuracy"]
        print(f"  {t}: best={run['best_model']} holdout_acc={acc:.3f} ({time.time()-t0:.1f}s)")

    output = {
        "target_definition": "1 if Close(t+1) > Close(t) else 0",
        "feature_cols": MODEL_FEATURES,
        "pooled": pooled,
        "pooled_per_ticker_accuracy": per_ticker_test,
        "per_ticker_runs": {
            t: {
                "best_model": r["best_model"],
                "walk_forward": r["walk_forward"],
                "holdout": r["holdout"],
            }
            for t, r in per_ticker_runs.items()
        },
    }
    (RESULTS_DIR / "experiment_results.json").write_text(
        json.dumps(_clean_for_json(output), indent=2), encoding="utf-8"
    )
    return output


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    tickers = list_nifty50_companies()
    print(f"Universe: {len(tickers)} tickers")
    if cmd in ("eda", "all"):
        run_eda(tickers)
        print("EDA artifacts written to results/")
    if cmd in ("run", "all"):
        run_experiments(tickers)
        print("Experiment artifacts written to results/")


if __name__ == "__main__":
    main()
