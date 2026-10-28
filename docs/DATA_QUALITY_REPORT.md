# Data Quality Audit Report

**Dataset:** National Stock Exchange (NSE) Daily OHLCV Panel  
**Audit Executed:** 2026-10-28  
**Audit Script:** `scripts/run_experiments.py eda`  
**Artifacts Generated:** `results/data_quality.json`, `results/figures/*.png`  

---

## 1. Audit Scope & Executive Summary

A comprehensive automated integrity audit was executed across the full historical universe of 45 NSE equity CSV files stored in `data/`. The data covers the 5-year chronological window from **2021-10-04 to 2026-10-01**.

### 1.1 Integrity Scorecard

| Quality Dimension | Test Specification | Audit Finding | Status |
|---|---|---:|---|
| **Completeness** | Null / NaN count across Open, High, Low, Close, Volume | 0 / 279,000 cells | **100% Complete** |
| **Temporal Consistency** | Duplicate calendar dates within any single ticker | 0 duplicated rows | **Zero Duplication** |
| **Date Parsing** | ISO-8601 YYYY-MM-DD parseability and monotonic sorting | 55,800 / 55,800 valid | **Monotonic & Valid** |
| **Positivity Invariant** | Verification that Open, High, Low, Close > 0 | 0 non-positive prices | **All Prices > 0** |
| **Domain Bound Invariants** | $High \ge Low$, $High \ge Close$, $Low \le Close$ | 0 geometric violations | **All OHLC Bounds Preserved** |
| **Calendar Structure** | Handling of NSE weekends & statutory market holidays | Natural gaps preserved, no interpolation | **Preserved Without Lookahead** |
| **Warm-up Pruning** | Handling of rolling indicator NaN prefixes | Dropped via `.dropna()` | **No `bfill()` Leakage** |

---

## 2. Statistical Distribution of the Panel

Across all 45 equities and 55,800 observation records:
- **Mean Daily Return:** $+0.052\%$ per trading session
- **Mean Annualized Volatility:** $25.4\%$
- **Minimum Annualized Volatility:** $15.8\%$ (`HINDUNILVR`)
- **Maximum Annualized Volatility:** $36.7\%$ (`ADANIPORTS`)
- **Average UP Day Frequency:** $50.68\%$
- **Class Balance Range:** $47.62\%$ UP (`ZEEL`) to $53.67\%$ UP (`HINDALCO`)

The class distribution is remarkably balanced near 50/50 across the panel, confirming that a naive constant classifier yields $\approx 50.7\%$ baseline accuracy.

---

## 3. Explanatory Figures Generated

1. `results/figures/eda_reliance.png`: Closing price, daily returns, and 20-day rolling annualized volatility for benchmark equity RELIANCE.
2. `results/figures/eda_tcs.png`: Multi-panel timeseries analysis for IT benchmark TCS.
3. `results/figures/eda_infy.png`: Multi-panel timeseries analysis for INFY.
4. `results/figures/eda_correlation_panel.png`: Full $45 \times 45$ Pearson correlation matrix of daily percentage returns across the Indian market universe.
5. `results/figures/eda_target_balance_reliance.png`: Binary target balance histogram and `Return_1d` distribution verifying symmetry and absence of severe outliers.

---

## 4. Verification Check: Data Leakage Elimination

1. **No Forward or Backward Fill of Future Information:** The standard `bfill()` method is completely prohibited in indicator calculations. Initial rows that do not have 50 historical sessions for `SMA_50` are dropped.
2. **Standardization Fit Exclusively on Train:** The `StandardScaler` is fitted strictly on the chronological training partition $[1 \dots t_{train}]$, and the transform is applied to validation and holdout sets.
3. **No Target Contamination:** Target creation uses strictly $Close_{t+1} > Close_t$ with row alignment ensuring index $t$ holds features $\mathcal{F}_t$ and label $Y_t$. The terminal row is dropped.

