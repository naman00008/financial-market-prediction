# Final Defense Presentation Outline

### Slide 1 — Problem & Motivation
- **Problem Statement:** Predict next-day stock direction (UP/DOWN) for NSE equities using historical and sentiment data.
- **Motivation:** Explore whether machine learning can extract tradable signals from noisy financial time series.
- **Objective:** Build a robust, leakage-free ML pipeline to compare technical features vs. sentiment features.

### Slide 2 — Dataset & Features
- **Data Source:** Yahoo Finance (45 NSE stocks, 2021-2026, ~53k rows).
- **Target Variable:** Binary Classification (1 if Next Day Close > Today's Close).
- **Features:** 43 engineered features across 7 categories (Trend, Momentum, Volatility, Volume, Sentiment).

### Slide 3 — ML Methodology
- **Leakage Prevention:** No random shuffling; strict Walk-Forward Validation.
- **Models:** Baseline, Logistic Regression, Random Forest, XGBoost.
- **Tuning:** Hyperparameter optimization performed only on chronological training splits.

### Slide 4 — Experimental Results
- **Model Comparison:** Present the ROC-AUC, Precision, and F1 scores.
- **Ablation Study:** Did adding Sentiment features improve the XGBoost model over Technicals alone?
- **Confusion Matrix:** Highlight the True Positive vs False Positive trade-off.

### Slide 5 — Explainability & Backtesting
- **Feature Importance:** Show the SHAP summary plot (What drives the model?).
- **Historical Simulation:** Show the Equity Curve (ML Strategy vs. Buy & Hold) factoring in transaction costs.
- **Dashboard Demo:** Briefly showcase the interactive Streamlit UI.

### Slide 6 — Conclusion & Limitations
- **Main Findings:** Answer the research questions.
- **Limitations:** Transaction costs, market regime shifts (non-stationarity).
- **Future Scope:** Deep learning (LSTMs), higher frequency data.
