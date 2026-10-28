# Mathematical Problem Statement & Formulation

**Course:** AUCML Semester V ESE — Machine Learning for Financial Markets  
**Project:** Market ML: Cloud-Native Market Prediction & Algorithmic Risk Intelligence Platform  
**Target Variable:** Next-Trading-Day Direction ($Y_t \in \{0, 1\}$)  

---

## 1. Formal Problem Definition

Let $S_t = (O_t, H_t, L_t, C_t, V_t)$ represent the vector of observable market metrics for a given equity on trading day $t \in \{1, 2, \dots, T\}$, consisting of the Open, High, Low, Close prices in Indian Rupees (₹) and the trading Volume (share count) on the National Stock Exchange of India (NSE).

### 1.1 The Target Variable
The prediction task is framed strictly as a **binary direction classification** problem for session $t+1$ conditioned only upon information available at or before the end of session $t$:

$$
Y_t = \begin{cases}
1, & \text{if } C_{t+1} > C_t \\
0, & \text{if } C_{t+1} \le C_t
\end{cases}
$$

The corresponding unobserved percentage return is:
$$
R_{t+1} = \frac{C_{t+1} - C_t}{C_t}
$$

The model outputs a probability estimate $\hat{p}_t = P(Y_t = 1 \mid \mathcal{F}_t)$, where $\mathcal{F}_t = \sigma(S_1, S_2, \dots, S_t)$ denotes the filtration (information set) available at the close of trading session $t$.

The terminal row $T$ of any historical observation window has an unobserved future session $T+1$; it cannot be labeled without fabrication and is dropped from all training and validation sets.

---

## 2. Statistical Leakage vs. Honest Formulation

### 2.1 The Same-Day Lookahead Fallacy
A common defect in naive financial ML implementations is setting the target to the same session's closing price $C_t$ while retaining $O_t, H_t, L_t$ as input features:

$$
\hat{C}_t = f(O_t, H_t, L_t, V_t)
$$

Because the intra-day bounds satisfy $L_t \le C_t \le H_t$ by definition, the regression model simply interpolates between same-day boundaries. This yields an artificially inflated $R^2 \approx 0.999$, zero real-world forecasting capability, and catastrophic failure when deployed in live trading.

### 2.2 Leakage-Safe Feature Engineering
To eliminate lookahead bias, all candidate features $X_t \in \mathbb{R}^d$ must satisfy:
1. **Scale Independence:** No raw rupee price levels ($C_t, O_t, H_t, L_t$) or non-stationary moving averages ($\text{SMA}_{20}, \text{EMA}_{50}$) enter the feature matrix.
2. **Strict Pre-Conditioning:** Every indicator value $X_{t, j}$ is computable strictly from $\{S_\tau\}_{\tau=1}^t$.
3. **No Backward Filling:** Initial window gaps caused by rolling operations (e.g., 50-day moving averages) must be pruned from the head of the series; `bfill()` is strictly forbidden because it leaks future averages into past timestamps.

---

## 3. Scale-Free Feature Vector $\mathbf{X}_t$

The feature vector $\mathbf{X}_t \in \mathbb{R}^{18}$ encompasses 5 distinct technical dimensions:

| Category | Feature Identifier | Mathematical Definition | Financial Rationale |
|---|---|---|---|
| **Lagged Returns** | `Return_1d` | $(C_t / C_{t-1}) - 1$ | Short-term momentum & reversal |
| | `Return_2d`, `Return_3d` | $(C_t / C_{t-k}) - 1$ | Multi-day persistence |
| | `Return_5d`, `Return_10d`, `Return_20d` | $(C_t / C_{t-k}) - 1$ | Medium-term trend momentum |
| **Trend Distances** | `Price_vs_SMA20` | $(C_t / \text{SMA}_{20}(C)_t) - 1$ | Short-term trend deviation |
| | `Price_vs_SMA50` | $(C_t / \text{SMA}_{50}(C)_t) - 1$ | Medium-term trend deviation |
| | `SMA_Ratio_20_50` | $(\text{SMA}_{20}(C)_t / \text{SMA}_{50}(C)_t) - 1$ | Golden / Death cross signal |
| **Oscillators** | `RSI_14` | $100 - \frac{100}{1 + \text{RS}_t}$ | Overbought / oversold indicator |
| | `WILLR_14` | $\frac{H_{14} - C_t}{H_{14} - L_{14}} \times (-100)$ | Intra-channel position |
| **Volatility** | `ATR_Pct` | $\text{ATR}_{14}(t) / C_t$ | Normalized price dispersion |
| | `BB_Width_20` | $(\text{BBU}_t - \text{BBL}_t) / \text{BBM}_t$ | Bollinger squeeze / expansion |
| | `BB_Pct_20` | $(C_t - \text{BBL}_t) / (\text{BBU}_t - \text{BBL}_t)$ | Relative position in band |
| | `Rolling_Vol_10`, `Rolling_Vol_20` | $\text{Std}(R_{t-k+1 \dots t}) \times \sqrt{252}$ | Annualized return volatility |
| **Volume Dynamics** | `Volume_Change_1d` | $(V_t / V_{t-1}) - 1$ | Volume shock |
| | `Relative_Volume_20` | $V_t / \text{SMA}_{20}(V)_t$ | Abnormal liquidity expansion |

---

## 4. Chronological Splitting & Validation Methodology

Financial time-series violate the Independent and Identically Distributed (i.i.d.) assumption due to autocorrelation, regime shifts, and non-stationarity. Standard $k$-fold cross-validation with random shuffling creates severe temporal lookahead leakage.

### 4.1 Chronological Three-Way Partition
Each stock's series of length $N$ is divided along the time axis:
- **Training Set (70%):** $t \in [1, \lfloor 0.70 N \rfloor]$
- **Validation Set (15%):** $t \in [\lfloor 0.70 N \rfloor + 1, \lfloor 0.85 N \rfloor]$
- **Holdout Test Set (15%):** $t \in [\lfloor 0.85 N \rfloor + 1, N]$

Invariants:
$$
\max(\text{Date}_{\text{train}}) < \min(\text{Date}_{\text{val}}) < \min(\text{Date}_{\text{test}})
$$

### 4.2 Walk-Forward Cross Validation
Model selection (hyperparameter tuning and algorithm choice) is performed **exclusively** on the Train + Validation block using expanding-window walk-forward splits:

```
Fold 1: [--- Train 60% ---] [ Val 10% ]
Fold 2: [------ Train 70% ------] [ Val 10% ]
Fold 3: [--------- Train 80% ---------] [ Val 10% ]
Fold 4: [------------ Train 90% ------------] [ Val 10% ]
```

The model achieving the highest mean out-of-fold ROC-AUC across walk-forward splits is selected. The **final 15% holdout set is evaluated exactly once** and is never consulted during model selection.

---

## 5. Realistic Baseline & Performance Expectations

According to the Weak-Form Efficient Market Hypothesis (EMH), asset prices reflect all past trading information. In liquid daily equity markets:
- The unconditional probability of an UP day is approximately $50.5\% - 52.0\%$.
- A zero-intelligence majority-class baseline achieves $\approx 51\%$ accuracy.
- Genuine predictive models typically achieve directional accuracies between $52.0\%$ and $54.5\%$ out-of-sample, with ROC-AUC values between $0.52$ and $0.56$.
- Any model claiming $>65\%$ directional accuracy on daily liquid equities without alternative non-public data indicates data leakage or overfitting.

---

## 6. Financial Evaluation: Backtesting with Transaction Costs

A classification model with $53\%$ accuracy does not necessarily yield a profitable strategy after execution costs. Market ML incorporates an integrated event-driven / vectorized backtester:
- **Trading Signal:** $S_t = \mathbb{I}(\hat{p}_t \ge 0.5)$
- **Execution Cost:** 10 bps ($0.1\%$) per trade to account for brokerage, STT (Securities Transaction Tax), exchange turnover fees, and bid-ask slippage.
- **Benchmark:** Passive Buy & Hold over the identical holdout test interval.

