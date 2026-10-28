# Dataset Documentation & Source Provenance

**Course:** AUCML Semester V ESE  
**Project:** Market ML — Financial Market Direction Prediction & Risk Simulation Platform  
**Target:** Next-Day Direction Classification ($Y_t \in \{0, 1\}$)  

---

## 1. Provenance & Collection Metadata

- **Acquisition Timestamp:** 2026-10-01
- **Primary Source:** National Stock Exchange of India (NSE) via Yahoo Finance API (`yfinance`)
- **Universe Definition:** NIFTY 50 constituent equities (45 liquid equities with continuous 5-year history)
- **Excluded Constituents:** `MM.NS` (Mahindra & Mahindra) and `TATAMOTORS.NS` were excluded due to missing history during the acquisition window.
- **Period Covered:** 2021-10-04 to 2026-10-01 (1,240 trading sessions per symbol)
- **Local Storage Path:** `data/*.csv`
- **Total Raw Records:** 55,800
- **Total Supervised Classification Samples:** 55,755 (after removing the final unobserved session per symbol)

---

## 2. Raw Schema Specification

Each stock CSV contains the standard daily OHLCV attributes:

| Column Name | SQL / Pandas Type | Description | Unit / Constraint |
|---|---|---|---|
| `Date` | `TIMESTAMP / object` | Trading date (YYYY-MM-DD) | Unique per stock, strictly monotonic |
| `Open` | `FLOAT64` | Opening auction price | INR (₹), strictly positive |
| `High` | `FLOAT64` | Session peak price | INR (₹), $\ge \max(Open, Close)$ |
| `Low` | `FLOAT64` | Session trough price | INR (₹), $\le \min(Open, Close)$ |
| `Close` | `FLOAT64` | Official closing settlement price | INR (₹), strictly positive |
| `Volume` | `INT64` | Aggregate shares transacted | Non-negative integer |

---

## 3. Supervised Classification Schema

Constructed via `src/ml_dataset.py`:

| Feature Name | Description | Formula / Derivation |
|---|---|---|
| `Return_1d` | 1-day lagged return | $(C_t / C_{t-1}) - 1$ |
| `Return_2d` | 2-day lagged return | $(C_t / C_{t-2}) - 1$ |
| `Return_3d` | 3-day lagged return | $(C_t / C_{t-3}) - 1$ |
| `Return_5d` | 5-day lagged return | $(C_t / C_{t-5}) - 1$ |
| `Return_10d` | 10-day lagged return | $(C_t / C_{t-10}) - 1$ |
| `Return_20d` | 20-day lagged return | $(C_t / C_{t-20}) - 1$ |
| `Price_vs_SMA20` | Normalized distance to 20 SMA | $(C_t / \text{SMA}_{20}) - 1$ |
| `Price_vs_SMA50` | Normalized distance to 50 SMA | $(C_t / \text{SMA}_{50}) - 1$ |
| `SMA_Ratio_20_50`| Moving average convergence | $(\text{SMA}_{20} / \text{SMA}_{50}) - 1$ |
| `RSI_14` | Relative Strength Index (14) | Momentum oscillator $\in [0, 100]$ |
| `WILLR_14` | Williams %R (14) | Channel position oscillator $\in [-100, 0]$ |
| `ATR_Pct` | Average True Range as % of Close | $\text{ATR}_{14} / C_t$ |
| `BB_Width_20` | Bollinger Band width | $(\text{BBU} - \text{BBL}) / \text{BBM}$ |
| `BB_Pct_20` | Bollinger %B | $(C_t - \text{BBL}) / (\text{BBU} - \text{BBL})$ |
| `Rolling_Vol_10` | 10-day annualized volatility | $\text{Std}(R_{1d, 10}) \times \sqrt{252}$ |
| `Rolling_Vol_20` | 20-day annualized volatility | $\text{Std}(R_{1d, 20}) \times \sqrt{252}$ |
| `Volume_Change_1d` | 1-day relative volume change | $(V_t / V_{t-1}) - 1$ |
| `Relative_Volume_20`| Volume relative to 20-day mean | $V_t / \text{SMA}_{20}(V)$ |
| `Target` (Label) | Next-day direction | $\mathbb{I}(C_{t+1} > C_t) \in \{0, 1\}$ |

---

## 4. Leakage-Prevention Architecture

```
Raw CSV (data/TICKER.csv)
   │
   ▼
Feature Engineering (src/feature_engineering.py)
   - Computes indicators strictly forward in time
   - Drops NaN warm-up rows (NO backward-fill)
   │
   ▼
Scale-Free Transformation (src/ml_dataset.py)
   - Discards raw price levels (Open, High, Low, Close, Volume)
   - Keeps only stationary ratios, returns, oscillators
   │
   ▼
Next-Day Target Alignment (src/ml_dataset.py)
   - Shifts Close by -1: Target_t = (Close_{t+1} > Close_t)
   - Drops terminal row (unobserved future)
   │
   ▼
Chronological 3-Way Partition (src/pipeline.py)
   - Train (70%)  -> Fit Scaler & Walk-Forward CV
   - Val   (15%)  -> Hyperparameter Selection
   - Test  (15%)  -> Final Holdout Scored Exactly Once
```

