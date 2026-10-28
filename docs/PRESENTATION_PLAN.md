# ESE Defense Presentation Plan & Demonstration Script

**Course:** AUCML Semester V ESE  
**Project:** Market ML — Financial Market Direction Prediction & Algorithmic Risk Intelligence Platform  
**Duration:** 12–15 Minutes Defense + 10 Minutes Technical Viva  

---

## 1. Slide-by-Slide Defense Structure

### Slide 1: Title & Executive Summary (1 min)
- **Title:** Market ML: Cloud-Native Market Prediction & Algorithmic Risk Intelligence Platform
- **Candidate:** Naman Vyas
- **Core Contribution:** Remediation of contemporaneous lookahead bias in algorithmic market prediction, implementation of a leakage-safe 5-year NSE equity panel pipeline, walk-forward model selection, transaction-cost aware backtesting, and production security hardening.

### Slide 2: The Core Machine Learning Dilemma in Finance (1.5 min)
- **The Classical Pitfall:** Regressing same-day $Close_t$ onto same-day $Open_t, High_t, Low_t$ produces $R^2 \approx 0.999$, creating an illusion of perfection while being completely useless in practice.
- **The Honest Formulation:** Predicting session $t+1$ direction ($Y_t = \mathbb{I}(C_{t+1} > C_t)$) conditioned strictly on information available at or before session $t$ close ($\mathcal{F}_t$).
- **Weak-Form EMH Reality:** Market direction exhibits low signal-to-noise ratio; true out-of-sample edge is subtle ($52\% \dots 55\%$).

### Slide 3: Dataset Architecture & Data Quality Audit (1 min)
- **Universe:** 45 liquid NIFTY 50 equities, 55,800 total OHLCV rows from 2021-10-04 to 2026-10-01.
- **Automated Quality Scorecard:** 0 missing values, 0 duplicate dates, 0 price violations ($High \ge Low$).
- **Class Balance:** Average UP day fraction is $50.68\%$ across the universe, providing an honest baseline.

### Slide 4: Leakage-Safe Feature Engineering (1.5 min)
- **Banned Columns:** Complete elimination of raw price levels ($Open, High, Low, Close, Volume$) and rupee-denominated moving averages.
- **18 Scale-Free Indicators:**
  - Momentum: Lagged percentage returns ($1d, 2d, 3d, 5d, 10d, 20d$).
  - Oscillators: $RSI_{14}$, $WILLR_{14}$, Bollinger $\%B$.
  - Volatility: $ATR\_Pct$, Bollinger Band Width, 10-day & 20-day rolling annualized volatility.
  - Liquidity: 1-day volume change, 20-day relative volume.
- **Zero Lookahead:** Warm-up rows dropped; `bfill()` strictly prohibited.

### Slide 5: Chronological Validation Architecture (1.5 min)
- **Strict 70/15/15 Temporal Split:**
  - Train: Oct 2021 – May 2024
  - Validation: May 2024 – Feb 2025
  - Test Holdout: Feb 2025 – Oct 2026
- **Walk-Forward Selection:** 4 expanding chronological folds over Train + Val. Model selection never touches the holdout.
- **Scaling:** `StandardScaler` fitted strictly on training data; applied forward to validation and test.

### Slide 6: Model Comparisons & Empirical Benchmarks (2 min)
- **Algorithms Compared:** Naive Baseline (50.7%), Logistic Regression (L2), Random Forest (300 trees), Gradient Boosting (200 trees), XGBoost.
- **Empirical Results (RELIANCE):**
  - Best Model: Random Forest ($n=300, \text{min\_samples\_leaf}=20$)
  - Holdout Directional Accuracy: $52.25\%$ (vs $50.5\%$ baseline)
  - Holdout ROC-AUC: $0.549$
  - Holdout Precision: $48.3\%$, Recall: $70.4\%$, F1: $0.573$
- **Academic Rigor:** Failure to achieve $>65\%$ is honest proof of no leakage.

### Slide 7: Global Explainability via TreeSHAP (1 min)
- **Methodology:** Exact TreeSHAP values computed across holdout test observations.
- **Key Findings:** Short-term volume shocks (`Volume_Change_1d`) and momentum exhaustions (`RSI_14`, `Return_3d`) dominate tree decisions.
- **Caveat:** Emphasized that feature importance is associative, not causal.

### Slide 8: Algorithmic Backtesting & Frictional Realism (1.5 min)
- **Signal Rule:** Trade on session close if predicted probability $\ge 0.5$.
- **Transaction Costs:** 10 basis points ($0.10\%$) per trade.
- **Finding:** A model with 52.3% gross accuracy can experience negative net alpha due to frictional drag, highlighting why quantitative funds require low-turnover execution.

### Slide 9: Portfolio Optimization & Risk Intelligence (1.5 min)
- **Efficient Frontier:** Vectorized Dirichlet Monte Carlo sampling over 10,000 weight vectors.
- **Risk Metrics:** Parametric 95% 1-day Value-at-Risk ($1.645 \sigma$) and Expected Shortfall ($2.063 \sigma$).
- **Allocation:** Discrete share quantities computed via floor allocation with cash buffer.

### Slide 10: Security Hardening & Zero UI Disruption (1.5 min)
- **Authentication Hardening:**
  - Removed unauthenticated `/api/auth/me` parameter bypass.
  - Eliminated password hash and salt logging in JSONL audit files.
  - Removed `credentials.txt` plaintext dossier files.
  - Implemented 24-hour session TTL with automatic invalidation.
- **Theme Preservation:** 100% preservation of the professor-provided UI theme, CSS, colors, fonts, and responsive layout.

---

## 2. Live Application Demonstration Script

### Step 1: System Health & Stock Selection (1 min)
- Open browser to `http://127.0.0.1:8000/`.
- Point out the active dashboard theme, system status indicator ("Market ML API is online"), and stock selector dropdown populated with 45 NSE equities.
- Select `RELIANCE` and observe the live company profile, market cap, and financial KPIs loading.

### Step 2: Model Evaluation Tab (2 min)
- Navigate to the **Model Eval** tab.
- Click **"Train Models Now"**.
- Explain the instantaneous response: instead of retrained on every click, the platform serves verified walk-forward metadata from the persisted model repository (`models/RELIANCE_metadata.json`).
- Walk through the Model Leaderboard table:
  - Explain the 5 columns: `MODEL`, `ACCURACY`, `PRECISION`, `ROC-AUC`, `F1 SCORE`.
  - Highlight the `BEST` badge on the walk-forward selected model (Random Forest).
  - Inspect the **Predicted vs Actual** time-series chart and the **Error Distribution Bell Curve**.
  - Show the **Global Feature Importance** SHAP chart showing top driving features (`Volume_Change_1d`, `RSI_14`).

### Step 3: Strategy Backtest Tab (2 min)
- Switch to the **Strategy Backtest** tab and click **"Run Backtest"**.
- Point to the equity curve comparison (Strategy vs Benchmark Buy & Hold).
- Point to the KPI cards: Total Return, Max Drawdown, Win Rate, and Sharpe Ratio.
- Explain the 10 bps transaction cost deduction and why realistic backtesting prevents curve-fitting delusions.

### Step 4: Portfolio Optimization & Risk Tab (2 min)
- Navigate to the **Portfolio Optimizer** tab.
- Add three stocks (e.g., `RELIANCE`, `TCS`, `HDFCBANK`) with capital ₹10,00,000.
- Click **"Optimize Portfolio"**.
- Display the Monte Carlo Efficient Frontier scatter plot, optimal Sharpe weights, discrete integer share allocations, and 95% VaR / CVaR risk bounds.

### Step 5: Authentication & Security Demonstration (1 min)
- Open DevTools Network tab.
- Demonstrate that `/api/auth/me` returns 401 Unauthorized unless accompanied by a valid session Bearer token.
- Demonstrate sign-up and sign-in with PBKDF2-100k password hashing.

