# Model Evaluation Framework & Benchmarks

**Course:** AUCML Semester V ESE  
**Project:** Market ML — Financial Market Direction Prediction & Risk Simulation Platform  
**Target:** Next-Day Direction Classification ($Y_t \in \{0, 1\}$)  

---

## 1. Evaluation Methodology Principles

### 1.1 Strict Temporal Decoupling
Standard machine learning practices that shuffle rows or select models based on test-set performance are mathematically flawed in financial time series. The evaluation framework implements:
1. **Walk-Forward Cross Validation:** Hyperparameter tuning and model selection are conducted strictly on past data using expanding chronological windows ($k=4$ folds).
2. **Holdout Evaluation:** The terminal 15% of trading sessions (2025–2026) is evaluated **once** as a true out-of-sample test. No decisions, feature selection, or hyperparameter updates ever consult this window.

### 1.2 Multi-Metric Evaluation Suite
Because financial markets exhibit low signal-to-noise ratios, relying solely on accuracy is deceptive. Every model is evaluated across seven statistical dimensions:

| Metric | Formula | Financial Interpretation |
|---|---|---|
| **Accuracy** | $\frac{TP + TN}{TP + TN + FP + FN}$ | Overall percentage of correct directional calls. |
| **Precision** | $\frac{TP}{TP + FP}$ | Fraction of predicted UP days that actually closed higher (avoids false longs). |
| **Recall (Sensitivity)** | $\frac{TP}{TP + FN}$ | Fraction of true UP days captured by the model. |
| **F1 Score** | $2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$ | Harmonic mean of precision and recall. |
| **ROC-AUC** | $\int_0^1 \text{TPR}(\text{FPR}^{-1}(t)) \, dt$ | Discriminative capacity across varying decision thresholds ($0.50 = \text{random}$). |
| **PR-AUC** | Area under Precision-Recall Curve | Performance baseline under minor class skew. |
| **Confusion Matrix** | Count matrix of $\{TN, FP, FN, TP\}$ | Precise breakdown of type I vs type II errors. |

---

## 2. Models Evaluated

### 2.1 Baseline: Naive Majority-Class Predictor
- **Mechanism:** Predicts the most frequent class observed in the training partition.
- **Purpose:** Serves as the zero-intelligence benchmark. Any ML model failing to beat this baseline offers no predictive value.

### 2.2 Logistic Regression (Regularized)
- **Hyperparameters:** L2 penalty, `C=1.0`, `max_iter=1000`, `StandardScaler` preprocessing.
- **Purpose:** Linear benchmark establishing the linearly separable information boundary in the feature space.

### 2.3 Random Forest Classifier
- **Hyperparameters:** `n_estimators=300`, `min_samples_leaf=20`, `max_depth=None`, `random_state=42`, `n_jobs=-1`.
- **Purpose:** Non-linear ensemble utilizing bagging and random subspace selection to control variance. Conservative leaf sizes (`min_samples_leaf=20`) prevent memorization of noise.

### 2.4 Gradient Boosting Classifier (Scikit-Learn)
- **Hyperparameters:** `n_estimators=200`, `learning_rate=0.05`, `max_depth=3`, `subsample=0.8`, `random_state=42`.
- **Purpose:** Sequential additive boosting with shrinkage and row subsampling to capture subtle non-linear interactions.

### 2.5 XGBoost Classifier
- **Hyperparameters:** `n_estimators=300`, `learning_rate=0.05`, `max_depth=4`, `subsample=0.8`, `colsample_bytree=0.8`, `reg_lambda=1.0`.
- **Purpose:** Scalable tree boosting with second-order gradient optimization and column subsampling.

---

## 3. Global Explainability (SHAP Analysis)

Global feature importance is evaluated via TreeSHAP (Tree Explainer) on the holdout test set:

$$
\phi_i = \sum_{S \subseteq F \setminus \{i\}} \frac{|S|!(|F| - |S| - 1)!}{|F|!} \left[ f(S \cup \{i\}) - f(S) \right]
$$

### Empirical Finding:
- **Leading Features:** `Volume_Change_1d`, `RSI_14`, `Return_3d`, and `BB_Width_20`.
- **Academic Insight:** Volume shocks paired with mean-reversion oscillators (RSI, Bollinger Width) exhibit the strongest marginal association with next-day direction, whereas multi-week moving average distances contribute minimal incremental signal on daily frequencies.
- **Associative Caveat:** SHAP importances reflect associative correlations within the trained model, not causal macroeconomic drivers.

