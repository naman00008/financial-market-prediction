# Financial Market Prediction: Final Case Study Report

## 1. Abstract
*Summarize the ML problem, dataset size/period, models compared, and the main findings regarding next-day direction predictability and sentiment impact.*

## 2. Introduction
*Provide context on why financial prediction is challenging (non-stationarity, noise) and the motivation for this project.*

## 3. Problem Statement
*Define the precise ML task: Next-day binary classification (1 if Close_{t+1} > Close_t). Define the scope and stakeholders.*

## 4. Dataset
*Detail the 45 NSE stocks, time period (2021-2026), 53k+ rows, handling of missing values, and data quality checks.*

## 5. Exploratory Data Analysis
*Summarize class distribution (~50/50), return distribution, and correlation insights.*

## 6. Preprocessing
*Explain leakage prevention (no bfill, chronological splits, target shifting).*

## 7. Feature Engineering
*Detail the 7 feature groups (OHLCV, Lags, Trend, Momentum, Volatility, Volume, Sentiment).*

## 8. Methodology
*Explain Walk-Forward Validation, model selection (Logistic Regression, Random Forest, XGBoost), and hyperparameter tuning.*

## 9. Experiments
*Detail the ablation studies (E1 to E5).*

## 10. Results
*Present the metrics table (Accuracy, F1, ROC-AUC), confusion matrices, and confidence intervals.*

## 11. Backtesting
*Explain the historical simulation rules (entry/exit/costs) and present Sharpe ratio and drawdown comparisons vs Buy & Hold.*

## 12. Explainability
*Insert global SHAP summary findings and an example of a local prediction explanation.*

## 13. Limitations
*Discuss transaction costs, market non-stationarity, and generalization limits.*

## 14. Conclusion
*Answer the core research questions using the experimental results.*

## 15. Future Scope
*Discuss potential improvements (deep learning, tick data).*

## 16. References
*List Yahoo Finance, libraries (scikit-learn, XGBoost, SHAP), and relevant literature.*
