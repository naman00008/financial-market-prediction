# Data Leakage Audit & Prevention Checklist

**Project:** Financial Market Prediction — Next-Day Direction Classification  
**Audit Date:** 2026-10-01  

---

## 1. Information Availability Boundary

At prediction time $t$ (end of trading day $t$):
- **Available Inputs:** Historical OHLCV values $t, t-1, t-2, \dots$, derived rolling technical indicators calculated using only historical values up to $t$, and news published on or before market close on day $t$.
- **Target Variable:** $y_t = 1$ if $(Close_{t+1} / Close_t) - 1 > 0$ else $0$.
- **Forbidden Inputs:** Any data, return, high/low price, volume, or news timestamp occurring on or after $t+1$.

---

## 2. Leakage Prevention Audit Matrix

| Leakage Category | Potential Vulnerability | Implemented Prevention | Verification Status |
|---|---|---|---|
| **Target Leakage** | Including same-row next-day return in feature matrix | Target $y_t$ created by shifting close forward by 1 step. Final row per ticker dropped. | ✅ Verified (`src/ml_dataset.py`) |
| **Backfill Leakage** | `bfill()` copying future indicator values into earlier rows | `bfill()` completely removed. Initial NaN rows from rolling windows dropped via `.dropna()`. | ✅ Verified (`src/feature_engineering.py`) |
| **Scaling Leakage** | Fitting `StandardScaler` on entire dataset before train/test split | `StandardScaler.fit()` called strictly on `train_df` only; `transform()` applied to `test_df`. | ✅ Verified (`src/model_training.py`) |
| **Split Leakage** | Random shuffling of time series rows during train/test split | Strict chronological ordering preserved; `shuffle=False` enforced. | ✅ Verified (`src/validation.py`) |
| **Validation Leakage** | Hyperparameter tuning or feature selection on final test period | Multi-window Walk-Forward Validation used for validation; test set reserved. | ✅ Verified (`src/validation.py`) |
| **Timestamp Leakage** | Incorporating news released after trading day close into day $t$ signal | News items filtered by timestamp; articles after 15:30 IST mapped to day $t+1$. | ✅ Verified (`src/sentiment_analysis.py`) |

---

## 3. Strict Pipeline Compliance Rules

1. **Never call `.bfill()` on time-series feature matrices.**
2. **Never invoke `train_test_split(..., shuffle=True)` for time-series evaluation.**
3. **Always fit scalers, encoders, or imputers on `X_train` inside fold execution.**
4. **Always verify that `Date_{train.max()} < Date_{test.min()}`.**
