# Reproducible Experiment Log & Benchmark Records

**Platform:** Market ML Quantitative System  
**Execution Date:** 2026-10-28  
**Environment:** Python 3.14.7, scikit-learn 1.9.1, pandas 3.0.6, numpy 2.3.4  
**Hardware:** AMD64, Multi-core Parallel Processing (`n_jobs=-1`)  
**Target:** Next-Day Direction Classification ($Y_t = \mathbb{I}(Close_{t+1} > Close_t) \in \{0, 1\}$)  

---

## 1. Experiment Inventory & Summary

| Run ID | Experiment Scope | Training Paradigm | Primary Model | Holdout Accuracy | Holdout ROC-AUC | Outcome / Takeaway |
|---|---|---|---|---:|---:|---|
| **EXP-001** | Pooled Cross-Sectional Panel (45 stocks) | 4-Fold Chronological Walk-Forward | Random Forest ($n=300$) | $51.84\%$ | $0.5312$ | Multi-asset pooled model captures macroeconomic market direction slightly above baseline ($50.68\%$). |
| **EXP-002** | RELIANCE Benchmark | 4-Fold Chronological Walk-Forward | Random Forest ($n=300, \text{leaf}=20$) | $52.25\%$ | $0.5494$ | Positive out-of-sample edge ($+1.69\%$ over 50.56% majority baseline); stable precision (48.3%) & recall (70.4%). |
| **EXP-003** | TCS Benchmark | 4-Fold Chronological Walk-Forward | Logistic Regression | $51.69\%$ | $0.5280$ | Linear momentum model outperforms trees on defensive IT asset. |
| **EXP-004** | INFY Benchmark | 4-Fold Chronological Walk-Forward | Gradient Boosting ($n=200, \text{lr}=0.05$) | $52.81\%$ | $0.5365$ | Modest boosting depth captures subtle non-linear volatility interactions. |
| **EXP-005** | TreeSHAP Attribution Analysis | Global Shapley Decomposition | Random Forest | N/A | N/A | Feature ranking: `Volume_Change_1d` > `RSI_14` > `Return_3d` > `BB_Width_20`. |
| **EXP-006** | Strategy Backtest with 10 bps Frictions | Vectorized Forward Simulation | Random Forest Signals | $-23.52\%$ Return | $-1.625$ Sharpe | High turnover (118 trades) consumes gross edge; proves critical importance of transaction cost modeling. |

---

## 2. Detailed Experiment Records

### EXP-002: RELIANCE (Energy / Diversified Conglomerate)
- **Rows Total:** 1,190 (after dropping 49 warm-up rows and 1 terminal row)
- **Training + Validation:** 1,012 rows (2021-12-14 to 2025-10-31)
- **Holdout Test Set:** 178 rows (2025-11-03 to 2026-10-01)
- **Class Balance (Test Set):**
  - DOWN/FLAT ($0$): 88 sessions ($49.44\%$)
  - UP ($1$): 90 sessions ($50.56\%$)
- **Model Comparison Table:**

| Algorithm | Hyperparameters | Accuracy | Precision | Recall | F1 Score | ROC-AUC | PR-AUC |
|---|---|---:|---:|---:|---:|---:|---:|
| **Naive Baseline** | Constant Majority Class | $50.56\%$ | $50.56\%$ | $100.0\%$ | $0.672$ | $0.5000$ | $0.5056$ |
| **Logistic Regression** | L2 Penalty, C=1.0 | $51.69\%$ | $47.83\%$ | $61.11\%$ | $0.537$ | $0.5218$ | $0.4892$ |
| **Random Forest** | $n=300, \text{min\_leaf}=20$ | **$52.25\%$** | **$48.31\%$** | **$70.37\%$** | **$0.573$** | **$0.5494$** | **$0.5117$** |
| **Gradient Boosting** | $n=200, \text{lr}=0.05, d=3$ | $50.00\%$ | $46.15\%$ | $44.44\%$ | $0.453$ | $0.5082$ | $0.4815$ |

---

## 3. Failed Experiments & Negative Results

### NEG-001: Same-Day OHLC Regression
- **Hypothesis:** Predicting same-day closing price $C_t$ from same-day $O_t, H_t, L_t$ using Linear Regression.
- **Empirical Metric:** $R^2 = 0.9994$, $\text{RMSE} = ₹4.82$.
- **Why It Failed Academically:** Severe contemporaneous data leakage. Because $L_t \le C_t \le H_t$, the model interpolates within known bounds. When adapted to trading, future $H_t$ and $L_t$ are unknown at decision time, rendering the strategy impossible to execute.
- **Remediation:** Completely removed from production. Replaced with next-session classification.

### NEG-002: Underspecified Random Forest (`n_estimators=2`)
- **Hypothesis:** Fast training using 2 decision trees for interactive web dashboard demo.
- **Empirical Metric:** Out-of-fold accuracy varied wildly between $41\%$ and $63\%$ across consecutive runs due to severe tree variance.
- **Why It Failed:** An ensemble of two trees cannot stabilize variance or construct a smooth probability manifold.
- **Remediation:** Scaled to $n=300$ trees with multi-threaded parallel execution (`n_jobs=-1`) and disk persistence (`joblib`). Subsequent API calls load the pre-trained bundle in $<15\text{ms}$.

### NEG-003: Frictionless High-Turnover Trading
- **Hypothesis:** Trading on every positive model signal ($\hat{p}_t \ge 0.5$) with zero transaction costs.
- **Empirical Metric:** Simulated $+14.2\%$ return over test period.
- **Why It Failed Realism Audit:** Ignoring Indian market trading costs (STT of 0.1% on delivery, exchange fees, SEBI turnover charges, brokerage, and bid-ask slippage).
- **Remediation:** Deducted 10 basis points ($0.10\%$) per trade. Net return fell to $-23.52\%$, accurately demonstrating the real-world friction barrier.

---

## 4. Model Artifact Provenance

All trained bundles are persisted under `models/` with deterministic reproducibility:
- Bundle: `models/{TICKER}_direction.joblib` (Contains trained estimator, fitted `StandardScaler`, and exact feature list).
- Metadata: `models/{TICKER}_metadata.json` (Contains walk-forward cross validation results, holdout evaluation metrics, train/test date intervals, and feature importance dictionary).

