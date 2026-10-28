# Comprehensive Viva Voce Preparation Guide (45 Questions & Answers)

**Course:** AUCML Semester V ESE — Machine Learning in Financial Engineering  
**Project:** Market ML: Cloud-Native Market Prediction & Risk Simulation Platform  
**Repository:** `financial-market-prediction`  

---

## Section I: Problem Formulation & Data Leakage Prevention (Q1 – Q8)

### Q1: What is the exact mathematical prediction target of the Market ML model?
**Answer:** The target is next-trading-day direction classification, defined in `src/ml_dataset.py:create_next_day_direction_target`:
$$
Y_t = \begin{cases} 1, & \text{if } Close_{t+1} > Close_t \\ 0, & \text{if } Close_{t+1} \le Close_t \end{cases}
$$
The feature vector $X_t$ contains only metrics computable at or before the close of trading session $t$. The final row of the dataset has an unknown future session and is dropped to prevent target fabrication.

### Q2: Why is predicting same-day $Close_t$ from same-day $Open_t, High_t, Low_t$ statistically invalid?
**Answer:** In intraday trading, the session bounds satisfy $Low_t \le Close_t \le High_t$ by definition. If a regression model is trained with same-day OHLC features to predict same-day Close, it simply interpolates between these deterministic bounds, generating an artificial $R^2 \approx 0.999$. This is a severe form of contemporaneous lookahead leakage that fails completely in real-world forward trading.

### Q3: How does Market ML guarantee that no raw price levels leak into the feature matrix?
**Answer:** In `src/ml_dataset.py`, `EXCLUDED_FROM_MODEL` explicitly bans all raw price levels (`Open`, `High`, `Low`, `Close`, `Volume`) and moving average price levels (`SMA_20`, `EMA_50`, `BBU_20`, `BBL_20`). The model features in `MODEL_FEATURES` are strictly stationary, scale-free percentage returns, normalized ratios (e.g., `Price_vs_SMA20 = Close / SMA_20 - 1`), and bounded oscillators (`RSI_14`, `WILLR_14`). The guard function `verify_no_lookahead` raises an exception if any forbidden column enters the feature matrix.

### Q4: Why is `bfill()` prohibited in the feature engineering pipeline?
**Answer:** Backward filling (`bfill()`) replaces missing values at earlier timestamps with observations from later timestamps. In rolling window indicators (e.g., a 50-day moving average), `bfill()` propagates future price information backwards into historical timestamps, creating lookahead leakage. In `src/feature_engineering.py:add_technical_indicators`, only forward filling (`ffill()`) is allowed, and initial warm-up rows containing NaNs are dropped.

### Q5: When is the feature scaler fitted, and why?
**Answer:** In `src/model_training.py:train_classification_models` and `src/pipeline.py:train_and_persist`, `StandardScaler` is fitted **exclusively on the training partition** (`X_train_scaled = scaler.fit_transform(X_train)`). The validation and holdout sets are transformed using the pre-fitted training scaler (`scaler.transform(X_test)`). Fitting the scaler across the entire dataset prior to splitting leaks distributional parameters (mean $\mu$ and standard deviation $\sigma$) from the future test set into the training phase.

### Q6: Why is standard K-Fold Cross Validation with random shuffling inappropriate for financial time series?
**Answer:** Financial market data violates the Independent and Identically Distributed (i.i.d.) assumption due to serial autocorrelation and volatility clustering. Randomly shuffling observations trains the model on future sessions ($t+1, t+5$) to predict past sessions ($t$), causing lookahead bias. Market ML enforces strict chronological splitting where all training data strictly precedes validation and holdout data.

### Q7: How does walk-forward cross validation work in `src/validation.py`?
**Answer:** `generate_walk_forward_splits` generates expanding-window chronological splits. For $k=4$ folds, Fold 1 trains on the initial 60% of past data and validates on the subsequent 10%; Fold 2 trains on 70% and validates on the next 10%; and so forth. Every fold validates strictly forward in time on unseen future observations.

### Q8: What role does the final holdout test set play in model selection?
**Answer:** The final 15% chronological partition (covering late 2025 to October 2026) is never consulted during feature selection, model selection, or hyperparameter tuning. Model selection is performed strictly on the Train + Validation segment using walk-forward validation. The final holdout set is scored exactly once to assess genuine out-of-sample generalization.

---

## Section II: Data Preprocessing & Stationarity (Q9 – Q14)

### Q9: What dataset was acquired, and what are its dimensions?
**Answer:** 55,800 daily OHLCV records across 45 liquid NIFTY 50 equities spanning 5 continuous years (2021-10-04 to 2026-10-01), with exactly 1,240 trading sessions per equity. Two symbols (`MM` and `TATAMOTORS`) were excluded due to incomplete historical records at collection time.

### Q10: Why are raw financial asset prices non-stationary?
**Answer:** Raw equity prices typically exhibit stochastic trends and unit roots (integrated of order 1, $I(1)$), meaning their mean and variance change over time. Models trained on raw price levels fail when the asset enters new price regimes. Percentage returns ($R_t = C_t / C_{t-1} - 1$) and normalized distance metrics are covariance stationary ($I(0)$), enabling models to learn regime-invariant relationships.

### Q11: How does Market ML handle NSE trading holidays and weekend gaps?
**Answer:** In `src/data_preprocessing.py:clean_stock_data`, calendar days where the exchange was closed are naturally absent. The pipeline does not interpolate fictitious prices for holidays because no trading occurred; doing so would distort return and volatility calculations. Monotonic chronological order is preserved.

### Q12: What data quality checks were executed on the raw CSV files?
**Answer:** As recorded in `results/data_quality.json` and `docs/DATA_QUALITY_REPORT.md`:
1. Completeness: 0 missing values across 279,000 OHLCV cells.
2. Temporal consistency: 0 duplicate dates.
3. Domain geometry: 0 occurrences of $High < Low$, $High < Close$, or $Low > Close$.
4. Price positivity: 0 zero or negative prices.

### Q13: What is the NIFTY proxy in `src/data_preprocessing.py`, and what was its original academic defect?
**Answer:** `load_nifty_index` computed a synthetic market index by averaging raw prices across all 45 stocks. The original implementation used `bfill()` across missing dates and an unweighted arithmetic mean rather than NIFTY 50's free-float market-capitalization weighting. In the remediated pipeline, models train directly on genuine equity panel data, and documentation explicitly notes the proxy's properties.

### Q14: How are warm-up periods handled for 50-day moving averages?
**Answer:** Calculating `SMA_50` requires 50 historical trading sessions, leaving the first 49 rows with NaNs. In `src/feature_engineering.py:create_features`, these initial 49 rows are dropped via `.dropna()`. Across 1,240 raw rows, exactly 1,190 rows remain per stock with completely finite feature vectors.

---

## Section III: Technical Indicators & Feature Engineering (Q15 – Q20)

### Q15: How is the Relative Strength Index (RSI) calculated without lookahead bias?
**Answer:** In `src/feature_engineering.py:_rsi`, price changes $\Delta C_t = C_t - C_{t-1}$ are separated into positive gains $U_t$ and negative losses $D_t$. Wilder's exponential smoothing is computed strictly forwards:
$$
\text{RS}_t = \frac{\text{EMA}_{14}(U)_t}{\text{EMA}_{14}(D)_t + 10^{-9}}, \quad \text{RSI}_t = 100 - \frac{100}{1 + \text{RS}_t}
$$
All operations depend exclusively on past price differences.

### Q16: What is Bollinger Band %B (`BB_Pct_20`), and why is it preferred over raw band levels?
**Answer:** Raw Upper and Lower Bollinger Bands ($BBU_t, BBL_t$) are denominated in rupees and drift with the stock price. Bollinger %B normalizes the closing price within the bands:
$$
\text{BB\_Pct\_20}_t = \frac{C_t - \text{BBL}_t}{\text{BBU}_t - \text{BBL}_t + 10^{-9}}
$$
Values above 1.0 indicate trading above the upper band (overbought); values below 0.0 indicate trading below the lower band (oversold). It is scale-free and stationary across decades.

### Q17: What is Average True Range Percent (`ATR_Pct`)?
**Answer:** True Range represents the maximum of $(H_t - L_t)$, $|H_t - C_{t-1}|$, and $|L_t - C_{t-1}|$. In `src/ml_dataset.py:build_model_features`, `ATR_Pct` divides 14-day ATR by $C_t$:
$$
\text{ATR\_Pct}_t = \frac{\text{ATR}_{14}(t)}{C_t + 10^{-9}}
$$
This represents normalized daily price volatility as a percentage of current price, enabling cross-asset volatility comparison regardless of stock price level.

### Q18: What does `Price_vs_SMA20` capture?
**Answer:** It measures the percentage deviation of the current closing price from its 20-day Simple Moving Average:
$$
\text{Price\_vs\_SMA20}_t = \frac{C_t}{\text{SMA}_{20}(C)_t + 10^{-9}} - 1.0
$$
It quantifies mean-reversion stretch: when the price deviates significantly from its short-term mean, mean-reversion pressure increases.

### Q19: How are volume features normalized?
**Answer:** Raw trading volume varies from millions of shares (RELIANCE) to hundreds of thousands (SHREECEM). Two normalized features are constructed:
1. `Volume_Change_1d`: $(V_t / V_{t-1}) - 1$, capturing single-day liquidity shocks.
2. `Relative_Volume_20`: $V_t / \text{SMA}_{20}(V)_t$, comparing current volume to its 20-day trailing baseline.

### Q20: How are news headlines processed in `src/sentiment_analysis.py`?
**Answer:** News headlines are analyzed using VADER (Valence Aware Dictionary and sEntiment Reasoner) supplemented by a financial adjustment lexicon (`FINANCIAL_ADJUSTMENT_RULES`). Phrases such as "record profit" (+0.18) and "penalty/slump" (-0.15) calibrate general sentiment scores to financial market contexts.

---

## Section IV: Validation Strategy & Model Ensembles (Q21 – Q28)

### Q21: What are the four core models compared in the classification benchmark?
**Answer:**
1. **Naive Baseline:** Majority class from training data ($\approx 50.7\%$ accuracy).
2. **Logistic Regression:** Linear classifier with L2 regularization on standardized features.
3. **Random Forest:** Non-linear bagged ensemble of 300 decision trees (`min_samples_leaf=20`).
4. **Gradient Boosting:** Sequential boosting of 200 shallow trees (`learning_rate=0.05, max_depth=3`).
5. **XGBoost:** Regularized gradient boosted decision trees with column subsampling.

### Q22: Why was the original Random Forest configuration (`n_estimators=2`) defective?
**Answer:** In the legacy codebase, Random Forest and XGBoost were instantiated with `n_estimators=2`. An ensemble of only two shallow trees possesses severe variance, high instability, and cannot produce reliable probability estimates. The remediated pipeline uses `n_estimators=300` with `min_samples_leaf=20` to guarantee statistical stability.

### Q23: Why do we use ROC-AUC rather than accuracy for walk-forward model selection?
**Answer:** Accuracy is sensitive to the 0.5 decision threshold and can be skewed by minor class imbalances. ROC-AUC evaluates the model's ability to rank positive instances above negative instances across all possible probability thresholds ($0.0 \dots 1.0$), providing a threshold-independent measure of discriminative power.

### Q24: What is the Weak-Form Efficient Market Hypothesis, and how does it relate to our holdout results?
**Answer:** Fama's Weak-Form EMH states that past price and volume data cannot be used to achieve excess risk-adjusted returns because historical information is already reflected in current prices. Our empirical holdout accuracy of $\approx 52.3\%$ and ROC-AUC of $\approx 0.549$ align with academic literature: liquid equities behave closely to martingales on daily frequencies, where small statistical edges require strict risk controls to exploit.

### Q25: What is the Brier score, and why does probability calibration matter?
**Answer:** The Brier score measures the mean squared error between predicted probabilities $\hat{p}_t$ and binary outcomes $Y_t$:
$$
\text{Brier} = \frac{1}{N} \sum_{t=1}^N (\hat{p}_t - Y_t)^2
$$
A model that predicts uncalibrated probabilities (e.g., claiming 90% confidence on inherently noisy 52% edges) will misallocate position sizes when Kelly criterion or risk budgeting is applied.

### Q26: What does TreeSHAP reveal about the Random Forest model?
**Answer:** TreeSHAP (`src/explainability.py:get_global_feature_importance`) calculates the exact Shapley attribution for each feature. For RELIANCE, the highest Shapley importance features are `Volume_Change_1d`, `RSI_14`, and `Return_3d`. This demonstrates that the model primarily exploits short-term liquidity shocks and momentum exhaustions rather than long-term trend following.

### Q27: How does model persistence work in `src/pipeline.py`?
**Answer:** Each trained model is serialized into `models/{identifier}_direction.joblib` containing:
1. The trained scikit-learn model object.
2. The pre-fitted `StandardScaler`.
3. The exact feature column order (`feature_cols`).
4. Training timestamp, random seed, and target definition.
A companion JSON file `models/{identifier}_metadata.json` records walk-forward selection metrics and holdout evaluation scores.

### Q28: How does `predict_next_session` generate forward predictions without retraining?
**Answer:** In `src/pipeline.py:predict_next_session`, the persisted bundle is loaded via `load_model_bundle`. Feature engineering is applied to the latest available historical data row ($T$), features are standardized using the persisted scaler, and `model.predict_proba()` produces the forward probability $\hat{p}_{T+1}$ in under 15 milliseconds.

---

## Section V: Financial Backtesting & Frictions (Q29 – Q34)

### Q29: How does the vectorized backtester in `src/backtest.py` execute trades?
**Answer:** On each session $t$ of the holdout set, the model generates signal $S_t \in \{0, 1\}$.
- If $S_t = 1$ (predicted UP), the strategy holds the stock from session $t$ close to session $t+1$ close, capturing return $R_{t+1}$.
- If $S_t = 0$ (predicted DOWN/FLAT), the strategy holds cash ($0\%$ return).
- The equity curve compounds over time:
$$
\text{Equity}_T = \prod_{t=1}^T (1 + S_t \cdot R_{t+1} - \text{Cost}_t)
$$

### Q30: Why are transaction costs critical in backtesting?
**Answer:** Daily trading strategies generate high portfolio turnover. A strategy executing 120 round-trip trades with a 10 bps (0.10%) cost per trade incurs $2 \times 0.001 \times 120 = 24\%$ in cumulative frictional drag. Without friction modeling, a strategy with 52% directional accuracy appears artificially profitable when in reality trading costs eliminate the gross edge.

### Q31: How is the Sharpe Ratio defined in `src/backtest.py`?
**Answer:**
$$
\text{Sharpe} = \frac{\bar{R}_{\text{strategy}} \times 252}{\sigma_{\text{strategy}} \times \sqrt{252}}
$$
where $\bar{R}_{\text{strategy}}$ is the mean daily return and $\sigma_{\text{strategy}}$ is the standard deviation of daily returns. A risk-free rate of 0% is assumed as conservative baseline.

### Q32: What is Maximum Drawdown (MDD), and how is it calculated?
**Answer:** Maximum Drawdown measures the maximum observed peak-to-trough decline of the strategy equity curve:
$$
\text{Drawdown}_t = \frac{\text{Equity}_t - \max_{\tau \le t} \text{Equity}_\tau}{\max_{\tau \le t} \text{Equity}_\tau}, \quad \text{MDD} = \min_{t} \text{Drawdown}_t
$$
It quantifies the worst-case capital loss experienced by an investor during the test period.

### Q33: Why did the original backtester in `app/api_routes.py` exhibit severe lookahead bias?
**Answer:** In the legacy route, the backtesting signal was constructed as `signals = (y_pred > df['Open'])` where `y_pred` was generated by a model trained to predict same-day Close using same-day High and Low. Because `y_pred` had already observed the future same-day prices, the strategy generated near-infinite simulated profits. In the remediated route, signals are derived strictly from forward-looking holdout models.

### Q34: What is the Win Rate of the backtest strategy?
**Answer:** The Win Rate is the fraction of executed trades ($S_t = 1$) that resulted in positive net return after transaction costs:
$$
\text{Win Rate} = \frac{\sum_{t} \mathbb{I}(S_t = 1 \text{ and } R_{t+1} > \text{Cost}_t)}{\sum_t \mathbb{I}(S_t = 1)}
$$

---

## Section VI: Portfolio Optimization & Risk Modeling (Q35 – Q40)

### Q35: How does the portfolio optimizer in `app/portfolio_routes.py` construct the efficient frontier?
**Answer:** It employs a vectorized Monte Carlo simulation over the simplex. It samples $K=10,000$ random weight vectors $w \sim \text{Dirichlet}(\alpha)$ where $\sum_{i=1}^M w_i = 1$ and $w_i \ge 0$ (long-only). For each weight vector, portfolio expected return $\mu_p = w^T \mu$ and annualized variance $\sigma_p^2 = w^T \Sigma w \times 252$ are computed, yielding the empirical efficient frontier.

### Q36: What is the difference between Value-at-Risk (VaR) and Expected Shortfall (CVaR)?
**Answer:**
- **Value-at-Risk ($\text{VaR}_\alpha$):** The maximum expected loss at a given confidence level $1-\alpha$ (e.g., 95%) over a 1-day horizon:
$$
\text{VaR}_{0.95} = z_{0.95} \cdot \sigma_p \approx 1.645 \cdot \sigma_p
$$
- **Expected Shortfall ($\text{ES}_\alpha$ or CVaR):** The expected loss given that the loss exceeds $\text{VaR}_\alpha$:
$$
\text{ES}_{0.95} = \mathbb{E}[L \mid L > \text{VaR}_{0.95}] = \frac{\phi(z_{0.95})}{\alpha} \cdot \sigma_p \approx 2.063 \cdot \sigma_p
$$
CVaR is a coherent risk measure because it satisfies subadditivity, whereas VaR does not.

### Q37: How are discrete share quantities calculated from continuous portfolio weights?
**Answer:** In `app/portfolio_routes.py`, given total capital $C$ (e.g., ₹10,00,000) and target weights $w_i$, the exact integer share count $n_i$ is determined via discrete floor allocation:
$$
n_i = \left\lfloor \frac{w_i \cdot C}{\text{Price}_i} \right\rfloor
$$
The unallocated residual cash is held in the portfolio cash buffer, ensuring realistic trading execution.

### Q38: What are the stress-testing scenarios in `app/portfolio_routes.py`, and how should they be interpreted?
**Answer:** The application simulates three macroeconomic shocks:
1. "Tech Selloff / High Rate Regime"
2. "Oil Shock & Energy Inflation"
3. "Banking Liquidity Squeeze"
These apply synthetic sector shock multipliers and simulate portfolio drawdown and recovery horizons. Documentation explicitly clarifies that these are heuristic stress simulations, not historical econometric forecasts.

### Q39: What is the covariance shrinkage rationale in portfolio risk estimation?
**Answer:** When the number of assets $M$ is large relative to the sample size $T$, the sample covariance matrix $\hat{\Sigma}$ has high estimation error and extreme eigenvalues, leading to unstable portfolio weights. Ledoit-Wolf shrinkage pulls $\hat{\Sigma}$ towards a structured target (such as constant correlation), reducing estimation variance and improving out-of-sample risk control.

### Q40: How does the platform compute annualized portfolio volatility?
**Answer:**
$$
\sigma_{\text{ann}} = \sqrt{252 \times w^T \Sigma_{\text{daily}} w}
$$
assuming 252 trading days per calendar year.

---

## Section VII: Software Architecture, Security & Production Engineering (Q41 – Q45)

### Q41: How was the `/api/auth/me` security vulnerability remediated?
**Answer:** The original endpoint permitted unauthenticated user enumeration: passing `?username=admin` returned the user profile without requiring any credentials. In `app/auth_routes.py:get_current_user`, this query parameter bypass was eliminated. Profile retrieval requires a verified cryptographic Bearer token validated against `_get_session_user()`.

### Q42: How are passwords stored and verified in `src/auth.py`?
**Answer:** Passwords are never stored in plaintext. They are hashed using PBKDF2-HMAC-SHA256 with 100,000 iterations and a cryptographically random 16-byte salt (`secrets.token_hex(16)`):
```python
hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode(), salt_bytes, 100000)
```
Verification uses `hmac.compare_digest` to prevent timing side-channel attacks.

### Q43: What credential exposure defect was removed from user registration and login?
**Answer:** In the legacy implementation, `track_activity()` logged the password hash and cryptographic salt directly into JSONL activity audit files, and wrote a human-readable `credentials.txt` dossier into `data/users/<username>/`. Both behaviors were removed in `src/auth.py`: credentials are never logged to audit trails, and `credentials.txt` is not created.

### Q44: What session management mechanism is implemented?
**Answer:** Active sessions are tracked in-memory using 48-character cryptographically secure tokens (`secrets.token_hex(24)`). Each session record contains creation timestamps and is enforced with a 24-hour Time-to-Live (`SESSION_TTL_SECONDS = 86400`). Expired tokens are purged upon lookup, and user logout explicitly deletes the token from active memory.

### Q45: How was CORS configured to prevent credential leakages?
**Answer:** In `main.py`, CORS middleware uses `allow_credentials=False` in conjunction with `allow_origins=["*"]`. Under W3C security standards, browsers prohibit credentialed requests (cookies/authorization headers) against wildcard origins, preventing unauthorized cross-origin credential harvesting.

