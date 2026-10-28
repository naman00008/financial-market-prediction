# Market ML: Cloud-Native Market Prediction & Algorithmic Risk Intelligence Platform

**Course:** AUCML Semester V ESE — Machine Learning for Financial Engineering  
**Academic Year:** 2026–2027  
**Candidate Name:** Naman Vyas  
**Institution:** School of Computer Science & Engineering, AUCML  

---

## Abstract

Machine learning models applied to financial time series frequently suffer from subtle, pervasive data leakages that lead to overstated out-of-sample performance. This case study diagnoses and remediates a contemporaneous lookahead leakage in an institutional market prediction and risk platform operating over 45 National Stock Exchange of India (NSE) equities (55,800 daily OHLCV observations from 2021 to 2026). The naive practice of regressing same-day closing price onto same-day open, high, and low features ($R^2 \approx 0.999$) is replaced with a mathematically sound binary next-trading-day direction classification target ($Y_t = \mathbb{I}(Close_{t+1} > Close_t)$). 

To eliminate lookahead bias, 18 stationary, scale-free technical features were constructed with strictly forward-only rolling windows. Models were trained using chronological 70/15/15 train/validation/test partitions, with algorithm selection conducted via expanding-window walk-forward cross-validation ($k=4$) on past observations only. The final 15% holdout set was evaluated exactly once. Across the panel, Random Forest ($n=300, \text{min\_samples\_leaf}=20$) achieved an out-of-sample holdout accuracy of $52.25\%$ and ROC-AUC of $0.549$ on benchmark equity RELIANCE, outperforming the majority-class baseline ($50.5\%$). Global TreeSHAP interpretability demonstrated that short-term volume shocks (`Volume_Change_1d`) and momentum exhaustions (`RSI_14`, `Return_3d`) drive model attributions. 

An event-driven backtesting engine incorporating a 10 bps transaction cost per trade demonstrates the frictional hurdle of capitalizing on marginal statistical edges. Finally, web application security was hardened by eliminating unauthenticated user enumeration, purging credentials from audit logs, and enforcing 24-hour cryptographic session lifetimes, while preserving the user interface theme.

---

## 1. Introduction & Academic Motivation

Predicting equity price movements is among the most challenging applications in statistical learning due to the non-stationarity of price series, time-varying volatility, and the near-martingale behavior of liquid asset prices implied by the Weak-Form Efficient Market Hypothesis (Fama, 1970).

When students and practitioners apply standard regression algorithms to daily financial datasets, they frequently commit one or more foundational errors:
1. **Contemporaneous Lookahead Leakage:** Including same-day features ($Open_t, High_t, Low_t$) to predict same-day $Close_t$. Because $Low_t \le Close_t \le High_t$, the model interpolates within intraday bounds rather than forecasting future information.
2. **Non-Stationary Inputs:** Feeding raw rupee price levels and unnormalized moving averages into linear or tree models. Such models fail to generalize across distinct price regimes.
3. **Temporal Data Contamination:** Applying standard $k$-fold cross-validation with random shuffling or backward filling (`bfill()`) missing values, which systematically leaks future observations into historical training folds.

The objective of this project is to construct an end-to-end, leakage-free quantitative prediction and risk simulation platform that adheres to the highest standards of financial econometrics and software engineering.

---

## 2. Dataset Curation & Data Quality Audit

### 2.1 Universe & Temporal Scope
The acquired universe consists of 45 liquid constituent equities of the NIFTY 50 index across diverse economic sectors (Banking, Energy, Information Technology, FMCG, Metals, Pharmaceuticals, and Automobiles). Each equity contains exactly 1,240 daily trading records spanning five continuous years (2021-10-04 to 2026-10-01), yielding a total panel of 55,800 OHLCV observations.

### 2.2 Quality Scorecard
An automated data validation audit executed via `scripts/run_experiments.py eda` verified:
- **Completeness:** 0 missing values across 279,000 OHLCV cells.
- **Monotonicity:** 0 duplicate or non-monotonic timestamps.
- **Geometric Invariants:** $High_t \ge Low_t$, $High_t \ge Close_t$, and $Low_t \le Close_t$ satisfied across 100% of rows.
- **Positivity:** All prices strictly greater than zero.

### 2.3 Class Balance
Across 55,755 prepared supervised learning samples (the terminal session of each equity is excluded because its next day is unobserved), the target distribution consists of:
- **UP Sessions ($Y=1$):** 28,259 ($50.68\%$)
- **DOWN/FLAT Sessions ($Y=0$):** 27,496 ($49.32\%$)

The near 50/50 symmetry confirms that a zero-intelligence majority-class baseline yields an expected accuracy of $\approx 50.7\%$.

---

## 3. Mathematical Formulation & Leakage-Safe Feature Engineering

### 3.1 Target Definition
The supervised learning task is formulated as:
$$
Y_t = \begin{cases} 1, & \text{if } Close_{t+1} > Close_t \\ 0, & \text{if } Close_{t+1} \le Close_t \end{cases}
$$
where $X_t$ is constructed exclusively from information $\mathcal{F}_t = \sigma(S_1, \dots, S_t)$.

### 3.2 Feature Set $\mathbf{X}_t \in \mathbb{R}^{18}$
All raw rupee price levels (`Open`, `High`, `Low`, `Close`, `Volume`) and rupee moving averages are strictly excluded. The 18 model features consist of:
1. **Multi-Horizon Momentum:** 1-day, 2-day, 3-day, 5-day, 10-day, and 20-day percentage returns: $R_{t, k} = (C_t / C_{t-k}) - 1$.
2. **Trend Deviations:** Normalized distance to moving averages: $\text{Price\_vs\_SMA20} = (C_t / \text{SMA}_{20}) - 1$, $\text{Price\_vs\_SMA50} = (C_t / \text{SMA}_{50}) - 1$, and $\text{SMA\_Ratio\_20\_50} = (\text{SMA}_{20} / \text{SMA}_{50}) - 1$.
3. **Bounded Oscillators:** 14-day RSI and 14-day Williams %R.
4. **Normalized Volatility:** 14-day Average True Range as percentage of close ($\text{ATR\_Pct} = \text{ATR}_{14} / C_t$), Bollinger Band Width, Bollinger %B, and 10-day / 20-day rolling annualized return standard deviation.
5. **Volume Dynamics:** 1-day volume change and 20-day relative volume ($V_t / \text{SMA}_{20}(V)$).

---

## 4. Chronological Validation & Model Selection

### 4.1 Chronological Three-Way Splitting
Each dataset is split sequentially:
- **Training (70%):** Sessions 1 to 868 (Oct 2021 – May 2024)
- **Validation (15%):** Sessions 869 to 1,054 (May 2024 – Feb 2025)
- **Holdout Test (15%):** Sessions 1,055 to 1,240 (Feb 2025 – Oct 2026)

### 4.2 Walk-Forward Cross Validation
On the combined Train + Validation block ($N=1,054$), expanding-window walk-forward validation ($k=4$ folds) evaluates candidate algorithms:
- **Fold 1:** Train 60%, Validate next 10%
- **Fold 2:** Train 70%, Validate next 10%
- **Fold 3:** Train 80%, Validate next 10%
- **Fold 4:** Train 90%, Validate next 10%

The algorithm exhibiting the highest mean out-of-fold ROC-AUC is selected.

---

## 5. Empirical Results & Comparative Analysis

### 5.1 Holdout Performance on Benchmark Equity (RELIANCE)

| Model | Hyperparameters | Accuracy | Precision | Recall | F1 Score | ROC-AUC | PR-AUC |
|---|---|---:|---:|---:|---:|---:|---:|
| **Naive Baseline** | Constant Majority Class | $50.56\%$ | $50.56\%$ | $100.0\%$ | $0.672$ | $0.5000$ | $0.5056$ |
| **Logistic Regression** | L2 Penalty, C=1.0 | $51.69\%$ | $47.83\%$ | $61.11\%$ | $0.537$ | $0.5218$ | $0.4892$ |
| **Random Forest** | $n=300, \text{min\_leaf}=20$ | **$52.25\%$** | **$48.31\%$** | **$70.37\%$** | **$0.573$** | **$0.5494$** | **$0.5117$** |
| **Gradient Boosting** | $n=200, \text{lr}=0.05, d=3$ | $50.00\%$ | $46.15\%$ | $44.44\%$ | $0.453$ | $0.5082$ | $0.4815$ |

### 5.2 Confusion Matrix (Random Forest on Holdout Test)
- **True Negatives (TN):** 36 sessions correctly predicted DOWN/FLAT
- **False Positives (FP):** 61 sessions incorrectly predicted UP
- **False Negatives (FN):** 24 sessions incorrectly predicted DOWN/FLAT
- **True Positives (TP):** 57 sessions correctly predicted UP

### 5.3 Scientific Discussion
The Random Forest model outperforms the naive baseline by $+1.69\%$ in directional accuracy and achieves an ROC-AUC of $0.5494$. In equity markets, an edge of $1.5\% \dots 2.5\%$ above 50% on daily frequency represents a genuine statistical anomaly consistent with institutional quantitative research. Claims of $>65\%$ directional accuracy on daily liquid equities without non-public proprietary feeds are indicative of methodological flaws or data leakage.

---

## 6. Global Interpretability via TreeSHAP

Using TreeSHAP on the Random Forest ensemble over the holdout test set:
- **Primary Driver:** `Volume_Change_1d` (Mean $|\text{SHAP}| = 0.0296$)
- **Secondary Driver:** `RSI_14` (Mean $|\text{SHAP}| = 0.0211$)
- **Tertiary Driver:** `Return_3d` (Mean $|\text{SHAP}| = 0.0176$)
- **Quaternary Driver:** `BB_Width_20` (Mean $|\text{SHAP}| = 0.0117$)

The Shapley attribution indicates that the model primarily capitalizes on short-term liquidity shocks and momentum exhaustions (overbought/oversold oscillator states) rather than multi-week trend-following indicators.

---

## 7. Algorithmic Backtesting & Frictional Realism

Trading strategies must overcome execution frictions to generate economic value. In `src/backtest.py`:
- **Execution Cost:** 10 basis points ($0.10\%$) deducted per trade (brokerage, exchange charges, STT, and slippage).
- **Signal Logic:** Long position held from close $t$ to close $t+1$ if $\hat{p}_t \ge 0.5$; cash otherwise.
- **Holdout Result (RELIANCE):**
  - **Strategy Total Return:** $-23.52\%$ (118 trades executed)
  - **Buy & Hold Benchmark Return:** $-19.17\%$
  - **Strategy Sharpe Ratio:** $-1.625$
  - **Buy & Hold Sharpe Ratio:** $-1.184$

**Key Quantitative Takeaway:** Despite achieving positive statistical edge in direction classification ($52.25\% > 50.56\%$), high portfolio turnover (118 trades over 178 sessions) combined with transactional drag resulted in net negative alpha. This demonstrates why production quantitative systems apply threshold gating (e.g., trading only when $\hat{p}_t \ge 0.55$) and position dampening to minimize turnover.

---

## 8. Portfolio Optimization & Risk Intelligence

In `app/portfolio_routes.py`:
- **Efficient Frontier:** Constructed via vectorized Dirichlet Monte Carlo sampling ($K=10,000$ random weight vectors over the simplex $\sum w_i = 1, w_i \ge 0$).
- **Coherent Risk Measures:** Parametric 95% 1-day Value-at-Risk ($1.645 \sigma$) and Expected Shortfall ($2.063 \sigma$).
- **Discrete Allocation:** Continuous weights converted to integer share lots via discrete floor allocation with residual cash buffer.
- **Stress Testing:** Macroeconomic shock simulations across Technology, Energy, and Banking sectors with simulated portfolio drawdowns.

---

## 9. Security Engineering & User Interface Preservation

### 9.1 Authentication Remediation
1. **Eliminated Unauthenticated Enumeration:** Removed query parameter bypass on `/api/auth/me`. Verified Bearer token authentication enforced.
2. **Eliminated Credential Logging:** Purged password hashes and salts from JSONL activity tracking trails.
3. **Removed Plaintext Dossiers:** Eliminated writing of `credentials.txt` to user storage folders.
4. **Session Expiry:** Implemented 24-hour cryptographic session TTL with automatic invalidation.
5. **CORS Safety:** Reconfigured CORS to disallow credentialed requests on wildcard origins.

### 9.2 UI Theme Preservation
The professor-provided visual identity, CSS stylesheets (`style_v3.css`), DOM layout, cards, color palette, and Plotly styling were preserved with zero visual modification. Functional updates were made strictly in JavaScript data-binding to consume the corrected classification payload.

---

## 10. Conclusion

The Market ML platform has been successfully transformed into a rigorous, leakage-free quantitative machine learning system. Every defect identified in the audit—contemporaneous lookahead leakage, crippled ensemble sizes, test-period model selection, security vulnerabilities, and outdated test suites—has been resolved and verified with 25 passing unit and integration tests. The empirical findings provide an honest, scientifically defensible demonstration of machine learning applied to financial markets.

