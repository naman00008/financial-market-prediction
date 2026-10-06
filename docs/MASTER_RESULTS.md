# Master Results Report

## 1. Initial Baseline Results
| Experiment_ID   | Model               | Feature_Set           |   Accuracy |   Precision |   Recall |     F1 |   ROC_AUC |   PR_AUC |
|:----------------|:--------------------|:----------------------|-----------:|------------:|---------:|-------:|----------:|---------:|
| E1              | Naive Baseline      | Basic                 |     0.4878 |      0.4944 |   0.4946 | 0.4945 |    0.4876 |   0.5006 |
| E1              | Naive Baseline      | Basic                 |     0.4878 |      0.4944 |   0.4946 | 0.4945 |    0.4876 |   0.5006 |
| E2              | Logistic Regression | Basic                 |     0.5077 |      0.5083 |   0.9463 | 0.6587 |    0.5134 |   0.5226 |
| E3              | Random Forest       | Technical             |     0.5153 |      0.5164 |   0.7983 | 0.6191 |    0.5253 |   0.5358 |
| E4              | XGBoost             | Technical             |     0.5103 |      0.513  |   0.6782 | 0.5812 |    0.5192 |   0.5297 |
| E5              | XGBoost             | Technical + Sentiment |     0.5103 |      0.513  |   0.6782 | 0.5812 |    0.5192 |   0.5297 |

## 2. Feature Ablation Results
| Experiment_ID   | Model         | Feature_Set                              |   Accuracy |   Precision |   Recall |       F1 |   ROC_AUC |   PR_AUC |
|:----------------|:--------------|:-----------------------------------------|-----------:|------------:|---------:|---------:|----------:|---------:|
| F1              | Random Forest | OHLCV Only                               |   0.510738 |    0.511584 | 0.842919 | 0.630615 |  0.518812 | 0.524578 |
| F2              | Random Forest | OHLCV + Lags                             |   0.508497 |    0.510736 | 0.804977 | 0.618403 |  0.523014 | 0.533838 |
| F3              | Random Forest | OHLCV + Lags + Tech                      |   0.515313 |    0.516398 | 0.79826  | 0.619134 |  0.52531  | 0.535844 |
| F4              | Random Forest | OHLCV + Lags + Tech + Sentiment          |   0.514893 |    0.515868 | 0.801275 | 0.61993  |  0.528504 | 0.5376   |
| F5              | Random Forest | OHLCV + Lags + Tech + Sentiment + Market |   0.526471 |    0.525066 | 0.714804 | 0.602095 |  0.549409 | 0.558568 |

## 3. Model Tuning Results
| Experiment_ID   | Model                 | Feature_Set   | Hyperparameters                                                                                         |   ROC_AUC |
|:----------------|:----------------------|:--------------|:--------------------------------------------------------------------------------------------------------|----------:|
| T1              | Random Forest (Tuned) | All (F5)      | {'n_estimators': 100, 'min_samples_split': 10, 'min_samples_leaf': 1, 'max_depth': None}                |  0.56191  |
| T2              | XGBoost (Tuned)       | All (F5)      | {'subsample': 0.6, 'n_estimators': 200, 'max_depth': 9, 'learning_rate': 0.01, 'colsample_bytree': 0.8} |  0.576489 |

## 4. Final Model Selection
- **Selection metric:** ROC-AUC
- **Selection methodology:** 5-fold expanding Walk-Forward Validation
- **Selected model:** XGBoost (Tuned) [Experiment T2]
- **Selected feature set:** All (F5) - OHLCV + Lags + Tech + Sentiment + Market Context
- *Note:* Selection was based on WFV validation strictly. The final holdout test was NOT used for model selection.

## 5. Historical/Premature Holdout Evaluations
This section preserves historical holdout evaluations that were run prior to finalizing the model selection process. These are NOT the final test results.

| Experiment_ID        | Model                 | Feature_Set   |   Accuracy |   Precision |   Recall |       F1 |   ROC_AUC |   PR_AUC |
|:---------------------|:----------------------|:--------------|-----------:|------------:|---------:|---------:|----------:|---------:|
| PREMATURE_HOLDOUT_RF | Random Forest (Tuned) | All (F5)      |   0.528852 |    0.524313 | 0.620284 | 0.568275 |  0.549352 | 0.554768 |

## 6. Final Unseen Test
| Experiment_ID   | Model           | Feature_Set   |   Accuracy |   Precision |   Recall |       F1 |   ROC_AUC |   PR_AUC |
|:----------------|:----------------|:--------------|-----------:|------------:|---------:|---------:|----------:|---------:|
| FINAL_TEST_XGB  | XGBoost (Tuned) | All (F5)      |   0.553782 |    0.542473 | 0.685842 | 0.605791 |  0.582681 | 0.582097 |

- **Test Period:** Chronological Final 20% Holdout
- *Note:* No tuning or selection occurred after viewing this result.

## 7. Key Findings
- **Sentiment Audit:** Sentiment features (`Sentiment_Score` and `News_Count`) were exactly zero for 100% of the dataset, providing no signal.
- **Feature Engineering:** Adding technicals and market context improved performance over basic OHLCV.
- **Model Comparison:** Tree-based models (Random Forest and XGBoost) generalized better than Logistic Regression.
- **Tuning:** Random Search on walk-forward folds prevented test-set leakage while selecting optimal hyperparameters.

## 8. Limitations
- **Market Context Dependency:** Current market proxy assumes an equal-weighted basket, not actual NIFTY.
- **Non-stationarity:** Financial markets evolve, and a predictive edge can diminish over time.
- **Zero Sentiment:** Missing natural language data implies we cannot test true NLP capabilities here without acquiring better alternative data.
