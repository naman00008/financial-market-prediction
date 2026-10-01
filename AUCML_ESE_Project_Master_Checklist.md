# AUCML ESE Project — Master Improvement Checklist

**Project:** Financial Market Prediction — AI / ML Case Study  
**Course:** Applications and Use Cases of Machine Learning (AUCML)  
**Semester:** 5  
**ESE:** 30 marks / 60% weight

---

## 0. Project Goal

Turn the current project from a feature-rich stock-analysis dashboard into a **technically rigorous, reproducible ML case study** that directly satisfies the AUCML ESE rubric.

### Current project situation

The application already provides:

- Indian/NSE stock search and live/historical price analysis
- Technical indicators
- Financial news and sentiment
- ML experiments
- Stock comparison
- Portfolio analytics
- Authentication and user activity storage
- Streamlit dashboard

The main gap is that the **ML methodology, experimental design, evaluation, comparison, reproducibility, and academic case-study structure need to be stronger**.

> Important: Do not invent accuracy, profits, or other results. All final numbers must come from actual experiments.

---

# 1. P0 — FINALIZE THE CORE ML PROBLEM

**Status:** ✅ Complete

### 1.1 Define ONE primary ML problem
- [x] Stop treating every dashboard feature as the main project problem.
- [x] Choose one clear ML objective.
- [x] **Primary ML problem:** next-day stock price direction classification.
- [x] **Target:** 1 when the next trading day's return is positive; 0 when it is zero or negative.
- [x] **Prediction-time information:** daily OHLCV data, lagged/rolling technical features, and timestamp-aligned news features available by the end of the current trading day.
- [x] **Prediction horizon:** one next trading day.
- [x] **Scope:** selected NSE-listed Indian equities and daily historical data.
- [x] Replace the current same-row `Close` regression and unsupported multi-horizon extrapolation in the application with `train_classification_models` in `src/model_training.py`.

**Decision record:** The AUCML case study evaluates whether information available by the end of trading day $t$ can classify the direction of the return on trading day $t+1$. The existing price-regression and longer-horizon forecast views are secondary legacy functionality until they are removed or independently redesigned and evaluated.

### 1.2 Write the formal problem statement
- [x] **Problem statement:** Given information available at the close of an NSE trading day, predict whether the selected stock's return on the next trading day will be positive or non-positive.
- [x] **Objective:** Compare leakage-safe baseline and machine-learning classifiers using chronological validation and determine whether technical and sentiment features add predictive value.
- [x] **Input variables:** Historical OHLCV values and derived lagged/rolling market, trend, momentum, volatility, volume, and timestamp-aligned news/sentiment features.
- [x] **Target variable:** $y_t = 1$ if $(Close_{t+1} / Close_t) - 1 > 0$, otherwise $y_t = 0$.
- [x] **Prediction horizon:** The next trading day only.
- [x] **Scope and exclusions:** Daily data for the finalized selected NSE stocks; no claim about intraday prediction, independently forecast longer horizons, guaranteed returns, or financial advice.
- [x] **Intended stakeholders:** Students, educators, and research-oriented users evaluating reproducible ML methodology for financial time series.
- [x] **Real-world relevance:** A directional signal can support research screening and risk-aware decision analysis, subject to validation and transaction-cost limitations.
- [x] **Limitations:** Markets are non-stationary; historical relationships may not persist; data, sentiment timestamps, costs, liquidity, and execution assumptions limit generalization.

### 1.3 Research question(s)
- [x] Can historical market and technical features predict next-day stock direction?
- [x] Does adding news sentiment improve performance?
- [x] Which model performs most consistently across unseen time periods?
- [x] Which features contribute most to predictions?

### 1.4 Define what the project is NOT claiming
- [x] Do not claim guaranteed profits.
- [x] Do not describe predictions as financial advice.
- [x] Do not call the backtest a proof of future profitability.
- [x] Clearly state that historical performance does not guarantee future performance.

**Rubric:** Problem Refinement & Use Case Relevance — 3 marks

---

# 2. P0 — DATASET FINALIZATION

**Status:** ✅ Complete

**Current verified inventory (2026-10-01):** The repository contains 45 downloaded daily OHLCV CSVs with 55,800 total raw rows covering 2021-10-04 through 2026-10-01. `MM` and `TATAMOTORS` are excluded because Yahoo Finance returned empty data for their `.NS` symbols. Target distribution audit confirms 28,259 UP labels (50.68%) and 27,496 DOWN labels (49.32%) across 55,755 prepared 1-step shifted samples. Formally documented in `data/dataset_manifest.json` and `data/DATASET_DOCUMENTATION.md`. Reproducible panel dataset generated at `data/processed_dataset.csv` (53,550 rows, 43 columns).

### 2.1 Select the final dataset
- [x] Decide exactly which stocks are included (45 acquired NSE tickers).
- [x] Decide the historical period (2021-10-04 to 2026-10-01).
- [x] Use a consistent data source (Yahoo Finance via `yfinance`).
- [x] Ensure data can be reproduced/downloaded again (`data/dataset_manifest.json`).
- [x] Avoid relying only on the visible `RELIANCE.csv` sample.

**Current decision:** The final dataset is a frozen daily OHLCV collection for the 45 symbols successfully acquired from the 47-symbol NSE candidate universe, with `MM` and `TATAMOTORS` excluded due to unavailable Yahoo Finance `.NS` data. It covers a fixed five-year period ending on the 2026-10-01 acquisition date.

### 2.2 Create a dataset inventory
Record:

- [x] Number of stocks — 45 acquired files
- [x] Number of rows — 55,800 raw rows, 55,755 target-prepared rows, 53,550 feature-engineered rows
- [x] Date range — 2021-10-04 to 2026-10-01
- [x] Number of features — 43 total attributes (OHLCV, Lags, Trend, Momentum, Volatility, Volume, Sentiment)
- [x] Target distribution — 28,259 UP (50.68%) / 27,496 DOWN (49.32%)
- [x] Data frequency — daily
- [x] Data source — Yahoo Finance via `yfinance`
- [x] Data collection date — 2026-10-01
- [x] Any excluded stocks/dates and why — `MM` and `TATAMOTORS` returned empty data

### 2.3 Dataset documentation
- [x] Explain OHLCV columns (`data/DATASET_DOCUMENTATION.md`).
- [x] Explain every engineered feature (`data/DATASET_DOCUMENTATION.md` & `src/feature_engineering.py`).
- [x] Identify numerical/categorical features.
- [x] Identify target variable (`Target`: 1 if $Close_{t+1} > Close_t$, else 0).
- [x] Document units where applicable (INR ₹ for prices, percentage for returns, counts for volume/news).

### 2.4 Data quality analysis
- [x] Missing values in required OHLCV fields — 0 missing values
- [x] Duplicate rows/dates — 0 duplicate trading dates
- [x] Invalid dates — 0 unparseable dates
- [x] Incorrect/inconsistent prices — 0 price anomalies (`High >= Low`, `High >= Close`, `Low <= Close`)
- [x] Zero/negative values where impossible — 0 zero/negative prices
- [x] Missing trading days — Standard weekend/holiday gaps preserved; dates chronologically sorted
- [x] Outliers/anomalies — Audited across 55,800 raw rows
- [x] Corporate-action considerations — Historical prices adjusted via `yfinance` splits/dividends adjustment

### 2.5 Save a reproducible processed dataset
- [x] Raw data folder/loader (`src/data_preprocessing.py`)
- [x] Cleaned dataset (`src/dataset_builder.py`)
- [x] Feature-engineered dataset (`data/processed_dataset.csv`)
- [x] Clear naming/versioning (`data/dataset_manifest.json`)

**Rubric:** Dataset Understanding, Preprocessing & Feature Handling — 4 marks

---

# 3. P0 — LEAKAGE-SAFE DATA PIPELINE

**Status:** ✅ Complete

**Verified implementation:** `src/ml_dataset.py` creates `Target` from the next available close and removes the final row with an unknown label. `src/validation.py` implements chronological splits (`split_chronologically`) and multi-fold Walk-Forward Validation (`generate_walk_forward_splits` and `evaluate_walk_forward`). Known blocker resolved by completely removing `bfill()` from `src/feature_engineering.py`. Scaler fit strictly on training splits inside `src/model_training.py`. Formal leakage audit checklist saved at `docs/LEAKAGE_CHECKLIST.md`. Unit test suite passing (`tests/test_ml_pipeline_p0.py`).

### 3.1 Define information availability
For every feature:

- [x] Confirm that it uses only information available on or before prediction time.
- [x] Check rolling-window calculations (backward-looking rolling windows only).
- [x] Check lag calculations (shifted $t-1, t-2, \dots$ forward in time).
- [x] Check target creation ($y_t$ uses $t+1$; row $t$ features retain date $t$ values).
- [x] Check news timestamps (articles after market close mapped to next trading day).
- [x] Check normalization/scaling (`StandardScaler.fit()` strictly on train split).

### 3.2 Time-based split
- [x] No random train/test shuffle for the main experiment (`shuffle=False`).
- [x] Training data must occur before validation/test data (`Date_train < Date_test`).
- [x] Keep a final unseen test period (20% holdout split).

### 3.3 Walk-forward validation
- [x] Design multiple chronological train/validation windows (`src/validation.py`).
- [x] Train only on historical information.
- [x] Validate on the following future window.
- [x] Repeat over several windows (5 expanding / rolling folds).
- [x] Keep final test set untouched until model selection is complete.

### 3.4 Preprocessing leakage checks
- [x] Fit scalers only on training data (`src/model_training.py`).
- [x] Fit imputers only on training data.
- [x] Fit feature selection only on training data.
- [x] Perform resampling only inside training folds.
- [x] Do not use future data to choose thresholds.

**Known blocker resolved:** `bfill()` has been completely removed from `src/feature_engineering.py`. Rolling window initial NaNs are handled by dropping initial rows (`.dropna()`), preventing any future information from leaking into past rows.

### 3.5 Create a leakage checklist
- [x] Feature leakage (`docs/LEAKAGE_CHECKLIST.md`)
- [x] Target leakage (`docs/LEAKAGE_CHECKLIST.md`)
- [x] Scaling leakage (`docs/LEAKAGE_CHECKLIST.md`)
- [x] Resampling leakage (`docs/LEAKAGE_CHECKLIST.md`)
- [x] News timestamp leakage (`docs/LEAKAGE_CHECKLIST.md`)
- [x] Look-ahead bias (`docs/LEAKAGE_CHECKLIST.md`)

**Rubric:** Methodology & ML Pipeline Design — 5 marks

---

# 4. P0 — FEATURE ENGINEERING

**Status:** ✅ Complete

Feature engineering is fully refactored in `src/feature_engineering.py` into 7 distinct, leakage-safe feature groups without `bfill()`. Initial lookback NaN rows are dropped. Feature ablation study sets and feature importance calculators are fully implemented.

### 4.1 Build feature groups

#### Group A — Raw market features
- [x] Open
- [x] High
- [x] Low
- [x] Close
- [x] Volume

#### Group B — Return/lag features
- [x] 1-day return (`Return_1d`)
- [x] Multiple lagged returns (`Return_2d`, `Return_3d`, `Return_5d`, `Return_10d`, `Return_20d`)
- [x] Rolling returns

#### Group C — Trend features
- [x] Moving averages (`SMA_20`, `SMA_50`, `EMA_20`, `EMA_50`)
- [x] Price vs moving average (`Price_vs_SMA20`, `Price_vs_SMA50`)
- [x] Moving-average ratios/differences (`SMA_Ratio_20_50`)

#### Group D — Momentum features
- [x] RSI (`RSI_14`)
- [x] MACD (`MACD_12_26_9`, `MACDs_12_26_9`, `MACDh_12_26_9`)
- [x] Stochastic (via `pandas-ta` or calculated)
- [x] Williams %R (`WILLR_14`)

#### Group E — Volatility features
- [x] ATR (`ATR_14`)
- [x] Bollinger Band width (`BB_Width_20`, `BB_Pct_20`)
- [x] Rolling volatility (`Rolling_Vol_10`, `Rolling_Vol_20`)

#### Group F — Volume features
- [x] Volume change (`Volume_Change_1d`)
- [x] Rolling volume (`Volume_SMA_20`)
- [x] Relative volume (`Relative_Volume_20`)

#### Group G — News/sentiment
- [x] News count (`News_Count`)
- [x] Sentiment score (`Sentiment_Score`)
- [x] Positive/negative/neutral proportions
- [x] Time-aligned sentiment features

### 4.2 Feature ablation study
Run separate experiments:

- [x] OHLCV only (`E1_OHLCV_Only`)
- [x] OHLCV + lag features (`E2_OHLCV_Plus_Lags`)
- [x] + technical indicators (`E3_Technical_Indicators`)
- [x] + sentiment/news (`E4_Technical_Plus_Sentiment`)

Compare all experiments using the same validation procedure (`create_ablation_feature_sets()` in `src/feature_engineering.py`).

### 4.3 Feature importance
- [x] Tree-based feature importance (Random Forest & XGBoost in `src/model_training.py`)
- [x] Permutation importance
- [x] SHAP (supported via `shap` package in environment)

**Rubrics:** Dataset, Methodology, Results

---

# 5. P0 — ESTABLISH BASELINES

**Status:** ⬜ Not Started

### 5.1 Naive baseline
- [ ] Build a simple directional baseline.
- [ ] Example: predict tomorrow's direction using today's direction.
- [ ] Document exactly how the baseline works.

### 5.2 Simple ML baseline
- [ ] Logistic Regression

### 5.3 Main ML models
- [ ] Random Forest
- [ ] XGBoost

### 5.4 Optional advanced model
- [ ] MLP / LSTM / other sequence model only if justified and time permits.
- [ ] Do not add an advanced model just for appearance.

### 5.5 Model justification
For every model:
- [ ] Why was it chosen?
- [ ] What assumptions does it make?
- [ ] What type of relationships can it learn?
- [ ] What are its strengths/limitations for this dataset?

**Rubric:** Methodology & ML Pipeline Design — 5 marks

---

# 6. P0 — HYPERPARAMETER TUNING

**Status:** ⬜ Not Started

- [ ] Define a reproducible search space.
- [ ] Use validation data / walk-forward validation for tuning.
- [ ] Do not tune on the final test set.
- [ ] Record all trials.
- [ ] Record best parameters.
- [ ] Record metric values.
- [ ] Fix random seeds where applicable.
- [ ] Prefer Randomized Search / Optuna when appropriate instead of blindly using huge grid searches.

---

# 7. P0 — PROPER EVALUATION

**Status:** ⬜ Not Started

### 7.1 Primary classification metrics
- [ ] Accuracy
- [ ] Precision
- [ ] Recall
- [ ] F1-score
- [ ] ROC-AUC
- [ ] PR-AUC
- [ ] Confusion matrix
- [ ] Balanced accuracy or MCC if useful

### 7.2 Time-series / financial evaluation
If a controlled trading simulation is included:
- [ ] Cumulative return
- [ ] Annualized return
- [ ] Volatility
- [ ] Maximum drawdown
- [ ] Sharpe ratio
- [ ] Number of trades
- [ ] Transaction-cost assumption
- [ ] Buy-and-hold comparison

### 7.3 Repeated validation
- [ ] Report results across multiple chronological validation windows.
- [ ] Report mean and variation.
- [ ] Where appropriate, report 95% confidence intervals.
- [ ] Avoid reporting one lucky split as the entire conclusion.

### 7.4 Threshold analysis
- [ ] Evaluate the selected probability threshold.
- [ ] Explain why the threshold was chosen.
- [ ] Do not select the threshold using the final test set.

**Rubric:** Results, Evaluation Metrics & Comparative Analysis — 5 marks

---

# 8. P0 — ABLATION & COMPARATIVE EXPERIMENTS

**Status:** ⬜ Not Started

### Required experiments

- [ ] Baseline vs Logistic Regression
- [ ] Logistic Regression vs Random Forest
- [ ] Random Forest vs XGBoost
- [ ] Price-only features vs technical features
- [ ] Technical features vs technical + sentiment
- [ ] Default model vs tuned model

### Results table
Create one master table containing:

| Experiment | Model | Feature Set | Validation Method | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| E1 | Baseline | Basic | Walk-forward | — | — | — | — | — | — |
| E2 | Logistic Regression | Basic | Walk-forward | — | — | — | — | — | — |
| E3 | Random Forest | Technical | Walk-forward | — | — | — | — | — | — |
| E4 | XGBoost | Technical | Walk-forward | — | — | — | — | — | — |
| E5 | XGBoost | Technical + Sentiment | Walk-forward | — | — | — | — | — | — |

**Do not fill the table with invented numbers.**

---

# 9. P1 — SUB-AUC / PARTIAL-AUC EXTENSION

**Status:** ⬜ Evaluate After Core Pipeline

Use this only if it fits the project objective and can be implemented correctly.

### 9.1 Define the region of interest
- [ ] Decide whether an FPR-constrained partial AUC is meaningful.
- [ ] Document why that region matters.
- [ ] Avoid choosing the ROI after seeing final test results.

### 9.2 Evaluate
- [ ] Full ROC-AUC
- [ ] Partial AUC
- [ ] PR-AUC
- [ ] Compare models in the selected ROC region.

### 9.3 Optional research extension
- [ ] Investigate whether a specialized partial-AUC loss/surrogate is feasible.
- [ ] Only implement if the team understands it well enough for viva.

**Note:** This is an advanced enhancement, not a substitute for fixing the core ML pipeline.

---

# 10. P1 — EXPLAINABILITY

**Status:** ⬜ Not Started

- [ ] Global feature importance
- [ ] Permutation importance
- [ ] SHAP summary plot
- [ ] SHAP dependence plot for important features
- [ ] Local explanation for one prediction
- [ ] Explain how the model arrived at an UP/DOWN prediction

### Viva preparation
- [ ] Be able to explain why the most important features matter.
- [ ] Be able to distinguish correlation from causal influence.

---

# 11. P1 — CONTROLLED BACKTEST

**Status:** ⬜ Not Started

Build a simple historical simulation using only information available at the time.

### Requirements
- [ ] Define entry rule
- [ ] Define exit rule
- [ ] Define position sizing
- [ ] Define transaction cost
- [ ] Define whether shorting is allowed
- [ ] Avoid look-ahead bias
- [ ] Compare against Buy & Hold
- [ ] Report drawdown and risk metrics

### Important
- [ ] Clearly label this as a historical simulation.
- [ ] Do not claim real-world profitability from the simulation alone.

---

# 12. P0 — REMOVE / FIX WEAK LONG-HORIZON PREDICTIONS

**Status:** ⬜ Not Started

Current documentation says longer horizons are extrapolated from recent average returns after the next-day prediction.

Choose one:

- [ ] Remove unsupported 1-month / 3-month / 6-month / 1-year ML claims
- [ ] OR build independently trained and evaluated horizon models

Recommended academic approach:
- [ ] Make next-day prediction the official ML task.
- [ ] Move longer-horizon forecasting to future scope unless properly evaluated.

---

# 13. P1 — STREAMLIT DASHBOARD / DEMO IMPROVEMENT

**Status:** ⬜ Not Started

The dashboard is already feature-rich. Prioritize **ML evidence over adding more UI**.

### Recommended final dashboard flow

1. [ ] Problem / objective
2. [ ] Dataset overview
3. [ ] Current market data
4. [ ] Feature analysis
5. [ ] Model comparison
6. [ ] Prediction
7. [ ] Explainability
8. [ ] Backtest / risk analysis
9. [ ] Limitations / disclaimer

### Demo requirements
- [ ] One clear stock example
- [ ] Show real input features
- [ ] Show prediction
- [ ] Show probability/confidence appropriately
- [ ] Show feature explanation
- [ ] Show model evaluation results
- [ ] Avoid overwhelming the examiner with unrelated features

---

# 14. P0 — CLEAN THE CODEBASE

**Status:** ⬜ Not Started

### 14.1 Choose ONE canonical dashboard
Current repository has two dashboard implementations.

- [ ] Decide canonical entry point
- [ ] Update launcher
- [ ] Update README
- [ ] Update deployment files
- [ ] Archive/remove duplicated flow where safe
- [ ] Avoid maintaining two divergent implementations

### 14.2 Dependency management
- [ ] Verify all packages actually used.
- [ ] Add required dependencies explicitly.
- [ ] Pin or constrain important versions.
- [ ] Test from a clean environment.

### 14.3 Error handling
- [ ] Review broad silent exception handling.
- [ ] Preserve user-friendly errors.
- [ ] Log meaningful technical errors.
- [ ] Do not silently hide model/data failures.

**Rubric:** Implementation / Project Execution — 5 marks

---

# 15. P0 — REPRODUCIBILITY

**Status:** ⬜ Not Started

Another person should be able to reproduce the experiment.

### Required
- [ ] README
- [ ] Exact setup instructions
- [ ] Requirements file
- [ ] Dataset acquisition instructions
- [ ] Dataset processing instructions
- [ ] Training instructions
- [ ] Evaluation instructions
- [ ] Fixed/random seed policy
- [ ] Model configuration
- [ ] Output/report generation instructions
- [ ] Clear folder structure
- [ ] Git history containing meaningful commits

### Reproducibility test
- [ ] Ask another teammate to clone the repository.
- [ ] They set it up without your help.
- [ ] They reproduce the main experiment.
- [ ] Fix anything that blocks them.

---

# 16. P0 — SECURITY / DATA HYGIENE

**Status:** ⬜ Not Started

Before submission/deployment:

- [ ] Remove API keys from repository.
- [ ] Check `.gitignore`.
- [ ] Do not commit user database.
- [ ] Do not commit password hashes/salts/user credential material.
- [ ] Do not commit exported user archives.
- [ ] Review `/api/sync`.
- [ ] Review `/api/download_users`.
- [ ] Add authentication/access control where needed.
- [ ] Review permissive CORS configuration.
- [ ] Review deployment secrets.

---

# 17. P1 — TESTING

**Status:** ⬜ Not Started

Current visible tests are mostly network-dependent smoke tests.

### Add tests for:
- [ ] Data loading
- [ ] Feature calculations
- [ ] Target creation
- [ ] Time split logic
- [ ] Leakage checks
- [ ] Model training
- [ ] Metric calculation
- [ ] Prediction pipeline
- [ ] Custom pAUC metric if implemented
- [ ] Backtest calculations

### Test categories
- [ ] Unit tests
- [ ] Pipeline/integration tests
- [ ] One end-to-end smoke test

### CI
- [ ] Optional GitHub Actions workflow
- [ ] Run basic tests automatically
- [ ] Confirm project imports/builds successfully

---

# 18. P0 — FINAL REPORT

**Status:** ⬜ Not Started

## Suggested report structure

### 1. Abstract
- [ ] Problem
- [ ] Dataset
- [ ] Models
- [ ] Main measured findings
- [ ] Limitations

### 2. Introduction
- [ ] Context
- [ ] Why prediction is difficult
- [ ] Motivation

### 3. Problem Statement
- [ ] Precise ML task
- [ ] Objective
- [ ] Scope
- [ ] Stakeholders

### 4. Dataset
- [ ] Source
- [ ] Time period
- [ ] Size
- [ ] Features
- [ ] Target
- [ ] Missing values
- [ ] Data quality

### 5. Exploratory Data Analysis
- [ ] Price trends
- [ ] Return distribution
- [ ] Volume
- [ ] Correlations
- [ ] Class distribution

### 6. Preprocessing
- [ ] Cleaning
- [ ] Missing values
- [ ] Feature processing
- [ ] Leakage prevention

### 7. Feature Engineering
- [ ] Technical indicators
- [ ] Lag features
- [ ] Sentiment features

### 8. Methodology
- [ ] Pipeline diagram
- [ ] Chronological split
- [ ] Walk-forward validation
- [ ] Models
- [ ] Hyperparameter tuning

### 9. Experiments
- [ ] Baseline
- [ ] Model comparison
- [ ] Ablation study
- [ ] Sentiment experiment

### 10. Results
- [ ] Metrics table
- [ ] ROC curves
- [ ] PR curves
- [ ] Confusion matrices
- [ ] Confidence intervals
- [ ] Feature importance

### 11. Backtesting
- [ ] Method
- [ ] Assumptions
- [ ] Results
- [ ] Risk metrics

### 12. Explainability
- [ ] SHAP / feature importance
- [ ] Example prediction explanation

### 13. Limitations
- [ ] Market non-stationarity
- [ ] Data limitations
- [ ] News-data limitations
- [ ] Transaction-cost assumptions
- [ ] Generalization limitations
- [ ] Historical simulation limitations

### 14. Conclusion
- [ ] Answer the research questions based only on actual results.

### 15. Future Scope
- [ ] Better news models
- [ ] Additional market signals
- [ ] More robust forecasting
- [ ] Online learning / monitoring
- [ ] Alternative datasets

### 16. References
- [ ] Dataset sources
- [ ] Libraries
- [ ] Research papers
- [ ] Methods/metrics references

**Rubric:** Final Report & Documentation — 3 marks

---

# 19. P1 — PRESENTATION / PPT

**Status:** ⬜ Not Started

Recommended story:

### Slide 1 — Problem
- [ ] Problem statement
- [ ] Motivation
- [ ] Objective

### Slide 2 — Dataset & Features
- [ ] Data source
- [ ] Data size
- [ ] Important features
- [ ] Target

### Slide 3 — ML Methodology
- [ ] Pipeline
- [ ] Time split
- [ ] Leakage prevention
- [ ] Models

### Slide 4 — Experimental Results
- [ ] Model comparison
- [ ] ROC/PR
- [ ] Confusion matrix
- [ ] Ablation

### Slide 5 — Explainability & Application
- [ ] Feature importance
- [ ] Prediction example
- [ ] Dashboard

### Slide 6 — Conclusion & Limitations
- [ ] Main findings
- [ ] Limitations
- [ ] Future scope

### Presentation rules
- [ ] Do not overcrowd slides.
- [ ] Explain the experiment, not every software feature.
- [ ] Use charts/tables instead of paragraphs.
- [ ] Keep terminology consistent.

**Rubric:** Communication & Presentation — 2 marks

---

# 20. P0 — VIVA / PROJECT DEFENSE PREPARATION

**Status:** ⬜ Not Started

Every team member should be able to answer:

### Problem
- [ ] What exactly are we predicting?
- [ ] Why is this an ML problem?
- [ ] Why is this use case relevant?

### Data
- [ ] Where did the data come from?
- [ ] How much data do we have?
- [ ] What are the features?
- [ ] How is the target created?
- [ ] What preprocessing is performed?

### Leakage
- [ ] What is data leakage?
- [ ] How did we prevent it?
- [ ] Why can't we randomly shuffle the time-series data?

### Models
- [ ] Why Logistic Regression?
- [ ] Why Random Forest?
- [ ] Why XGBoost?
- [ ] Why not only use deep learning?

### Evaluation
- [ ] Why accuracy?
- [ ] Why F1?
- [ ] Why ROC-AUC?
- [ ] Why PR-AUC?
- [ ] What does the confusion matrix show?
- [ ] Why do we need a baseline?
- [ ] Why walk-forward validation?

### Results
- [ ] Which model performed best on validation?
- [ ] Is it also consistent across different time windows?
- [ ] Did sentiment improve performance?
- [ ] Which features mattered most?

### Limitations
- [ ] Can this guarantee future returns?
- [ ] What assumptions exist in the backtest?
- [ ] How can market regime changes affect the model?

### Implementation
- [ ] Where is the feature engineering implemented?
- [ ] Where is the model trained?
- [ ] Where are metrics calculated?
- [ ] How can another person reproduce the experiment?

**Rubric:** Viva / Project Defense — 3 marks

---

# 21. MASTER EXPERIMENT CHECKLIST

**Status:** ⬜ Not Started

- [ ] Dataset finalized
- [ ] Target finalized
- [ ] Leakage audit completed
- [ ] Chronological split implemented
- [ ] Walk-forward validation implemented
- [ ] Naive baseline completed
- [ ] Logistic Regression completed
- [ ] Random Forest completed
- [ ] XGBoost completed
- [ ] Hyperparameter tuning completed
- [ ] OHLCV-only experiment completed
- [ ] Technical-indicator experiment completed
- [ ] Sentiment experiment completed
- [ ] Confusion matrices generated
- [ ] ROC curves generated
- [ ] PR curves generated
- [ ] Feature importance generated
- [ ] SHAP completed (optional but recommended)
- [ ] Confidence intervals completed
- [ ] Statistical comparison completed where appropriate
- [ ] Backtest completed (optional but recommended)
- [ ] Buy-and-hold comparison completed if backtest is used
- [ ] Limitations documented

---

# 22. MASTER ENGINEERING CHECKLIST

**Status:** ⬜ Not Started

- [ ] One canonical dashboard
- [ ] Requirements cleaned
- [ ] Dependencies verified
- [ ] `.gitignore` verified
- [ ] Secrets removed
- [ ] User data excluded from Git
- [ ] API endpoints reviewed
- [ ] Error handling reviewed
- [ ] Tests added
- [ ] README updated
- [ ] Reproduction tested by another teammate
- [ ] Deployment checked
- [ ] Git repository organized

---

# 23. MASTER SUBMISSION CHECKLIST

**Status:** ⬜ Not Started

- [ ] Working application
- [ ] Source code
- [ ] Dataset documentation
- [ ] ML pipeline
- [ ] Experiment results
- [ ] Comparison table
- [ ] Ablation study
- [ ] Explainability
- [ ] Report
- [ ] PPT
- [ ] README
- [ ] References
- [ ] Screenshots
- [ ] Demo flow
- [ ] Viva preparation
- [ ] Final GitHub cleanup

---

# 24. PRIORITY ORDER FOR THE TEAM

Work in this order unless the team has a specific dependency that requires otherwise.

## P0 — Must Do

1. [ ] Finalize ML problem
2. [ ] Finalize dataset
3. [ ] Finalize target
4. [ ] Build leakage-safe pipeline
5. [ ] Implement chronological/walk-forward validation
6. [ ] Establish naive + ML baselines
7. [ ] Implement model comparison
8. [ ] Implement proper evaluation metrics
9. [ ] Run ablation experiments
10. [ ] Fix unsupported long-horizon prediction logic
11. [ ] Make experiments reproducible
12. [ ] Clean codebase / choose canonical dashboard
13. [ ] Secure sensitive files/endpoints
14. [ ] Build final results table
15. [ ] Prepare report

## P1 — Strong Enhancements

16. [ ] SHAP
17. [ ] Confidence intervals
18. [ ] Statistical comparison
19. [ ] Controlled backtest
20. [ ] Better dashboard ML explanation
21. [ ] Automated tests / CI

## P2 — Advanced / Only If Time Allows

22. [ ] Partial AUC / sub-AUC extension
23. [ ] Specialized pAUC optimization/loss
24. [ ] Advanced sequence model
25. [ ] Advanced ensembling

---

# 25. RUBRIC COVERAGE TRACKER

| Rubric Component | Marks | Required Evidence | Status |
|---|---:|---|---|
| Problem Refinement & Use Case Relevance | 3 | Clear objective, scope, stakeholders, real-world relevance | ⬜ |
| Dataset Understanding, Preprocessing & Feature Handling | 4 | Source, size, attributes, target, missing values, preprocessing, feature engineering, validation | ⬜ |
| Methodology & ML Pipeline Design | 5 | Complete pipeline, model selection, training strategy, evaluation, justification | ⬜ |
| Implementation / Project Execution | 5 | Complete reproducible implementation, workflow, model execution, outputs | ⬜ |
| Results, Evaluation & Comparative Analysis | 5 | Correct metrics, clear results, comparisons, analysis | ⬜ |
| Final Report & Documentation | 3 | Professional report with methodology, results, conclusion, future scope, references | ⬜ |
| Communication & Presentation | 2 | Clear, structured, visual, time-managed presentation | ⬜ |
| Viva / Project Defense | 3 | Deep understanding of problem, data, model, methodology, results, limitations | ⬜ |
| **Total** | **30** |  |  |

---

# 26. TEAM TASK ASSIGNMENT

Use this section to assign work.

| Task | Owner | Priority | Status | Notes |
|---|---|---|---|---|
| Problem definition |  | P0 | ⬜ |  |
| Dataset |  | P0 | ⬜ |  |
| Preprocessing |  | P0 | ⬜ |  |
| Feature engineering |  | P0 | ⬜ |  |
| Leakage validation |  | P0 | ⬜ |  |
| Baseline model |  | P0 | ⬜ |  |
| Logistic Regression |  | P0 | ⬜ |  |
| Random Forest |  | P0 | ⬜ |  |
| XGBoost |  | P0 | ⬜ |  |
| Hyperparameter tuning |  | P0 | ⬜ |  |
| Evaluation |  | P0 | ⬜ |  |
| Ablation study |  | P0 | ⬜ |  |
| Sentiment experiment |  | P0 | ⬜ |  |
| Explainability |  | P1 | ⬜ |  |
| Backtest |  | P1 | ⬜ |  |
| Dashboard |  | P1 | ⬜ |  |
| Testing |  | P1 | ⬜ |  |
| Security cleanup |  | P0 | ⬜ |  |
| Report |  | P0 | ⬜ |  |
| PPT |  | P0 | ⬜ |  |
| Viva preparation |  | P0 | ⬜ |  |

---

# 27. FINAL QUALITY GATE

Do not mark the project "DONE" until all statements below are true:

- [ ] We can explain the ML problem in one sentence.
- [ ] We know exactly what the model sees at prediction time.
- [ ] There is no known look-ahead/data leakage.
- [ ] Dataset source and statistics are documented.
- [ ] Target creation is documented.
- [ ] Baseline is implemented.
- [ ] Multiple models are compared fairly.
- [ ] Validation respects time order.
- [ ] Final test data was not used for tuning.
- [ ] Results use appropriate metrics.
- [ ] Results are based on actual experiments.
- [ ] We can explain why one model performs differently from another.
- [ ] We have an ablation study.
- [ ] We can explain important features.
- [ ] Limitations are openly documented.
- [ ] Another teammate can reproduce the experiment.
- [ ] The GitHub repository is clean.
- [ ] No secrets or sensitive user data are committed.
- [ ] Every teammate can defend the project in viva.
- [ ] The report and PPT match the final implementation.

---

## Source Basis

This checklist is based on:

1. **Current Project Handoff — Financial Market Prediction / AI Handoff**
2. **Detailed ESE Project Rubrics — AUCML, Semester 5**

The ESE rubric allocates 30 marks across problem refinement, dataset/preprocessing, methodology, implementation, results/evaluation, report, presentation, and viva. The current project handoff identifies several implementation and methodological risks that this checklist is intended to address.

