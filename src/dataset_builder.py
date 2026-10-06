"""Reproducible processed dataset builder for Financial Market Prediction.

Loads raw OHLCV datasets, applies leakage-free feature engineering, attaches next-day
direction target labels, and outputs cleaned, reproducible panel datasets.
"""

from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

from src.feature_engineering import create_features, build_feature_groups, create_ablation_feature_sets
from src.ml_dataset import create_next_day_direction_target


DATA_DIR = Path("c:/Users/tedha/financial-market-prediction/data")
PROCESSED_CSV_PATH = DATA_DIR / "processed_dataset.csv"


def prepare_stock_df(df: pd.DataFrame, ticker: str = "") -> pd.DataFrame:
    """Process a single stock DataFrame: clean columns, compute features, attach target."""
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]

    if "Date" not in df.columns or "Close" not in df.columns:
        raise ValueError("DataFrame must contain 'Date' and 'Close' columns")

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).sort_values("Date", kind="stable").reset_index(drop=True)

    # 1. Feature Engineering (without bfill)
    feat_df = create_features(df)

    # 2. Next-day direction target creation (shifts close -1 and drops final row)
    final_df = create_next_day_direction_target(feat_df, close_col="Close", target_col="Target")

    if ticker:
        final_df["Ticker"] = ticker

    return final_df


def build_and_save_panel_dataset(data_dir: str | Path = DATA_DIR, output_path: str | Path = PROCESSED_CSV_PATH) -> pd.DataFrame:
    """Process all acquired CSV files in data_dir and save unified panel dataset."""
    data_dir = Path(data_dir)
    csv_files = sorted(list(data_dir.glob("*.csv")))
    
    # Filter out processed_dataset.csv if it already exists
    stock_csvs = [f for f in csv_files if f.name != "processed_dataset.csv"]

    if not stock_csvs:
        raise FileNotFoundError(f"No stock CSV files found in {data_dir}")

    processed_frames = []

    for csv_path in stock_csvs:
        ticker = csv_path.stem
        try:
            df = pd.read_csv(csv_path)
            proc_df = prepare_stock_df(df, ticker=ticker)
            processed_frames.append(proc_df)
        except Exception as e:
            print(f"Warning: Failed to process {ticker}: {e}")

    if not processed_frames:
        raise RuntimeError("Failed to process any stock CSV files")

    panel_df = pd.concat(processed_frames, axis=0, ignore_index=True)
    
    # --- PHASE 4: Add Market Context Features (Zero Lookahead) ---
    # Calculate equal-weighted market return for each day
    market_returns = panel_df.groupby("Date")["Return_1d"].mean().rename("Market_Return_1d")
    panel_df = panel_df.merge(market_returns, on="Date", how="left")
    
    # Previous-day market direction (since we predict t+1, day t's direction is the "previous" known market direction)
    panel_df["Market_Dir_1d"] = (panel_df["Market_Return_1d"] > 0).astype(float)
    
    # Stock return relative to Market
    panel_df["Relative_Return_1d"] = panel_df["Return_1d"] - panel_df["Market_Return_1d"]
    
    # Ensure correct column ordering
    base_cols = ["Ticker", "Date", "Open", "High", "Low", "Close", "Volume", "Target", "Next_Return"]
    other_cols = [c for c in panel_df.columns if c not in base_cols]
    panel_df = panel_df[base_cols + other_cols]

    output_path = Path(output_path)
    panel_df.to_csv(output_path, index=False)
    print(f"Processed panel dataset saved to {output_path} ({len(panel_df):,} rows, {len(panel_df.columns)} columns)")
    return panel_df


if __name__ == "__main__":
    build_and_save_panel_dataset()
