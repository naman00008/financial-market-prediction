"""Leakage-free Feature Engineering module for Financial Market Prediction.

Builds structured feature groups (Market, Returns/Lags, Trend, Momentum, Volatility,
Volume, Sentiment) with zero lookahead bias. Backfill (bfill) is explicitly excluded.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    ta = None
    PANDAS_TA_AVAILABLE = False


def _rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=length, min_periods=length).mean()
    avg_loss = loss.rolling(window=length, min_periods=length).mean()

    rs = avg_gain / (avg_loss + 1e-9)
    return 100.0 - (100.0 / (1.0 + rs))


def _macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()

    macd_line = ema_fast - ema_slow
    macd_signal = macd_line.ewm(span=signal, adjust=False).mean()
    macd_hist = macd_line - macd_signal

    return pd.DataFrame(
        {
            "MACD_12_26_9": macd_line,
            "MACDs_12_26_9": macd_signal,
            "MACDh_12_26_9": macd_hist,
        }
    )


def _bollinger_bands(series: pd.Series, length: int = 20, std: float = 2.0) -> pd.DataFrame:
    sma = series.rolling(window=length, min_periods=length).mean()
    rolling_std = series.rolling(window=length, min_periods=length).std()
    upper = sma + std * rolling_std
    lower = sma - std * rolling_std
    return pd.DataFrame(
        {
            f"BBM_{length}_{std}": sma,
            f"BBU_{length}_{std}": upper,
            f"BBL_{length}_{std}": lower,
        }
    )


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=length, min_periods=length).mean()


def add_technical_indicators(df: pd.DataFrame, fillna_ffill_only: bool = True) -> pd.DataFrame:
    """Compute technical indicators without lookahead data leakage.
    
    WARNING: bfill() is intentionally omitted to prevent copying future data into the past.
    Initial rows containing NaN due to rolling windows must be handled by dropping NaN rows.
    """
    if "Close" not in df.columns:
        raise ValueError("DataFrame must contain a 'Close' column")

    df = df.copy()

    # Sort chronologically to preserve strict temporal order
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.sort_values("Date", kind="stable").reset_index(drop=True)

    close = pd.to_numeric(df["Close"], errors="coerce")
    high = pd.to_numeric(df.get("High", close), errors="coerce")
    low = pd.to_numeric(df.get("Low", close), errors="coerce")
    volume = pd.to_numeric(df.get("Volume", 0), errors="coerce")

    # Group B — Returns / Lags
    df["Return_1d"] = close.pct_change(1)
    df["Return_2d"] = close.pct_change(2)
    df["Return_3d"] = close.pct_change(3)
    df["Return_5d"] = close.pct_change(5)
    df["Return_10d"] = close.pct_change(10)
    df["Return_20d"] = close.pct_change(20)

    # Group C — Trend Features
    df["SMA_20"] = close.rolling(window=20, min_periods=20).mean()
    df["SMA_50"] = close.rolling(window=50, min_periods=50).mean()
    df["EMA_20"] = close.ewm(span=20, adjust=False).mean()
    df["EMA_50"] = close.ewm(span=50, adjust=False).mean()
    
    df["Price_vs_SMA20"] = (close / (df["SMA_20"] + 1e-9)) - 1.0
    df["Price_vs_SMA50"] = (close / (df["SMA_50"] + 1e-9)) - 1.0
    df["SMA_Ratio_20_50"] = (df["SMA_20"] / (df["SMA_50"] + 1e-9)) - 1.0

    # Group D — Momentum Features
    rsi_vals = _rsi(close, length=14)
    df["RSI_14"] = rsi_vals

    macd_df = _macd(close, fast=12, slow=26, signal=9)
    df["MACD_12_26_9"] = macd_df["MACD_12_26_9"]
    df["MACDs_12_26_9"] = macd_df["MACDs_12_26_9"]
    df["MACDh_12_26_9"] = macd_df["MACDh_12_26_9"]

    # Williams %R
    highest_14 = high.rolling(window=14, min_periods=14).max()
    lowest_14 = low.rolling(window=14, min_periods=14).min()
    df["WILLR_14"] = -100.0 * (highest_14 - close) / (highest_14 - lowest_14 + 1e-9)

    # Group E — Volatility Features
    df["ATR_14"] = _atr(high, low, close, length=14)

    bb_df = _bollinger_bands(close, length=20, std=2.0)
    df["BBM_20_2.0"] = bb_df["BBM_20_2.0"]
    df["BBU_20_2.0"] = bb_df["BBU_20_2.0"]
    df["BBL_20_2.0"] = bb_df["BBL_20_2.0"]
    
    bb_denom = df["BBU_20_2.0"] - df["BBL_20_2.0"]
    df["BB_Width_20"] = bb_denom / (df["BBM_20_2.0"] + 1e-9)
    df["BB_Pct_20"] = (close - df["BBL_20_2.0"]) / (bb_denom + 1e-9)

    df["Rolling_Vol_10"] = df["Return_1d"].rolling(window=10, min_periods=10).std()
    df["Rolling_Vol_20"] = df["Return_1d"].rolling(window=20, min_periods=20).std()

    # Group F — Volume Features
    df["Volume_Change_1d"] = volume.pct_change(1)
    df["Volume_SMA_20"] = volume.rolling(window=20, min_periods=20).mean()
    df["Relative_Volume_20"] = volume / (df["Volume_SMA_20"] + 1e-9)

    # Use pandas-ta if available for extra indicators (Stochastic, CCI)
    if PANDAS_TA_AVAILABLE and ta is not None:
        try:
            stoch = ta.stoch(high, low, close)
            if stoch is not None:
                for col in stoch.columns:
                    if col not in df.columns:
                        df[col] = stoch[col]

            cci = ta.cci(high, low, close)
            if cci is not None and "CCI_14" not in df.columns:
                df["CCI_14"] = cci
        except Exception:
            pass

    # Group G — Sentiment Defaults (0.0 if not present)
    if "Sentiment_Score" not in df.columns:
        df["Sentiment_Score"] = 0.0
    if "News_Count" not in df.columns:
        df["News_Count"] = 0.0

    if fillna_ffill_only:
        # Only forward-fill missing values within series (NO bfill!)
        df = df.ffill()

    # Drop duplicate columns if any
    df = df.loc[:, ~df.columns.duplicated(keep="first")]
    return df


def build_feature_groups() -> dict[str, list[str]]:
    """Define dictionary mapping group names to list of feature names."""
    return {
        "OHLCV": ["Open", "High", "Low", "Close", "Volume"],
        "Lags": ["Return_1d", "Return_2d", "Return_3d", "Return_5d", "Return_10d", "Return_20d"],
        "Trend": ["SMA_20", "SMA_50", "EMA_20", "EMA_50", "Price_vs_SMA20", "Price_vs_SMA50", "SMA_Ratio_20_50"],
        "Momentum": ["RSI_14", "MACD_12_26_9", "MACDs_12_26_9", "MACDh_12_26_9", "WILLR_14"],
        "Volatility": ["ATR_14", "BB_Width_20", "BB_Pct_20", "Rolling_Vol_10", "Rolling_Vol_20"],
        "Volume": ["Volume_Change_1d", "Volume_SMA_20", "Relative_Volume_20"],
        "Sentiment": ["Sentiment_Score", "News_Count"],
    }


def create_ablation_feature_sets() -> dict[str, list[str]]:
    """Define incremental feature sets for feature ablation study."""
    groups = build_feature_groups()
    
    set1_ohlcv = groups["OHLCV"]
    set2_lags = set1_ohlcv + groups["Lags"]
    set3_technical = set2_lags + groups["Trend"] + groups["Momentum"] + groups["Volatility"] + groups["Volume"]
    set4_full = set3_technical + groups["Sentiment"]

    return {
        "E1_OHLCV_Only": set1_ohlcv,
        "E2_OHLCV_Plus_Lags": set2_lags,
        "E3_Technical_Indicators": set3_technical,
        "E4_Technical_Plus_Sentiment": set4_full,
    }


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """Generate complete feature set and drop initial NaN rows created by rolling windows."""
    df = add_technical_indicators(df, fillna_ffill_only=True)
    # Drop rows containing NaNs created by initial lookback windows (e.g. 50-period SMA)
    df = df.dropna().reset_index(drop=True)
    return df
