import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

try:
    from xgboost import XGBClassifier, XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError as e:
    XGBClassifier = None
    XGBRegressor = None
    XGBOOST_AVAILABLE = False

try:
    from tensorflow.keras.layers import Dense, LSTM
    from tensorflow.keras.models import Sequential
    TENSORFLOW_AVAILABLE = True
except Exception:
    LSTM = None
    Dense = None
    Sequential = None
    TENSORFLOW_AVAILABLE = False


def evaluate_classification(y_true: np.ndarray, y_pred_prob: np.ndarray, threshold: float = 0.5) -> dict:
    """Compute comprehensive classification metrics for next-day direction prediction.
    
    Metrics include Accuracy, Precision, Recall, F1-score, ROC-AUC, PR-AUC,
    and Confusion Matrix counts (TN, FP, FN, TP).
    """
    y_true = np.asarray(y_true, dtype=int)
    y_pred_prob = np.asarray(y_pred_prob, dtype=float)
    y_pred = (y_pred_prob >= threshold).astype(int)

    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    try:
        roc_auc = float(roc_auc_score(y_true, y_pred_prob))
    except Exception:
        roc_auc = 0.5

    try:
        pr_auc = float(average_precision_score(y_true, y_pred_prob))
    except Exception:
        pr_auc = 0.5

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)

    return {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def train_classification_models(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str = "Target",
    random_state: int = 42,
) -> dict:
    """Train classification models for next-day direction prediction.
    
    Fits scaler ONLY on train_df to prevent scaling data leakage.
    Returns dictionary with models, scalers, predictions, probabilities, and evaluation metrics.
    """
    if target_col not in train_df.columns or target_col not in test_df.columns:
        raise ValueError(f"Target column '{target_col}' missing from train or test DataFrame")

    X_train = train_df[feature_cols].copy()
    y_train = train_df[target_col].values.astype(int)
    X_test = test_df[feature_cols].copy()
    y_test = test_df[target_col].values.astype(int)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    results = {}

    # Naive Baseline (Predict tomorrow's direction = today's direction)
    if "Return_1d" in test_df.columns:
        naive_probs = (test_df["Return_1d"].fillna(0) > 0).astype(float).values
    elif "Close" in test_df.columns and "Open" in test_df.columns:
        naive_probs = (test_df["Close"] > test_df["Open"]).astype(float).values
    else:
        majority_class = int(np.bincount(y_train).argmax())
        naive_probs = np.full(len(y_test), fill_value=float(majority_class))

    results["baseline"] = {
        "model": None,
        "y_pred_prob": naive_probs,
        "metrics": evaluate_classification(y_test, naive_probs),
        "feature_cols": feature_cols,
    }

    # Logistic Regression
    lr = LogisticRegression(max_iter=1000, random_state=random_state)
    lr.fit(X_train_scaled, y_train)
    lr_probs = lr.predict_proba(X_test_scaled)[:, 1]
    results["logistic_regression"] = {
        "model": lr,
        "scaler": scaler,
        "y_pred_prob": lr_probs,
        "metrics": evaluate_classification(y_test, lr_probs),
        "feature_cols": feature_cols,
    }

    # Random Forest Classifier
    rf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=random_state)
    rf.fit(X_train_scaled, y_train)
    rf_probs = rf.predict_proba(X_test_scaled)[:, 1]
    results["random_forest"] = {
        "model": rf,
        "scaler": scaler,
        "y_pred_prob": rf_probs,
        "metrics": evaluate_classification(y_test, rf_probs),
        "feature_cols": feature_cols,
        "feature_importances": dict(zip(feature_cols, rf.feature_importances_)),
    }

    # XGBoost Classifier
    if XGBOOST_AVAILABLE and XGBClassifier is not None:
        xgb = XGBClassifier(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.05,
            random_state=random_state,
            eval_metric="logloss",
        )
        xgb.fit(X_train_scaled, y_train)
        xgb_probs = xgb.predict_proba(X_test_scaled)[:, 1]
        results["xgboost"] = {
            "model": xgb,
            "scaler": scaler,
            "y_pred_prob": xgb_probs,
            "metrics": evaluate_classification(y_test, xgb_probs),
            "feature_cols": feature_cols,
            "feature_importances": dict(zip(feature_cols, xgb.feature_importances_)),
        }

    return results


def train_regression_models(df: pd.DataFrame, target_col: str = "Close") -> dict:
    """Legacy helper: Train Linear Regression, Random Forest, and XGBoost models on stock data."""
    df = df.copy()

    features = df.drop(columns=["Date", target_col], errors='ignore')
    features = features.select_dtypes(include=[np.number])

    targets = pd.to_numeric(df[target_col], errors="coerce")

    if features.empty or targets.isna().all():
        raise ValueError("No numeric features or valid target values available for training")

    X_train, X_test, y_train, y_test = train_test_split(
        features, targets, test_size=0.2, shuffle=False
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    models = {}

    lr = LinearRegression()
    lr.fit(X_train_scaled, y_train)
    y_pred_lr = lr.predict(X_test_scaled)
    models["linear_regression"] = {
        "model": lr,
        "scaler": scaler,
        "X_test": X_test,
        "feature_names": list(X_train.columns),
        "y_test": y_test,
        "y_pred": y_pred_lr,
        "r2_score": float(r2_score(y_test, y_pred_lr)),
    }

    rf = RandomForestRegressor(n_estimators=100, random_state=42)
    rf.fit(X_train_scaled, y_train)
    y_pred_rf = rf.predict(X_test_scaled)
    models["random_forest"] = {
        "model": rf,
        "scaler": scaler,
        "X_test": X_test,
        "feature_names": list(X_train.columns),
        "y_test": y_test,
        "y_pred": y_pred_rf,
        "r2_score": float(r2_score(y_test, y_pred_rf)),
    }

    if XGBOOST_AVAILABLE and XGBRegressor is not None:
        xgb = XGBRegressor(n_estimators=100, random_state=42)
        xgb.fit(X_train_scaled, y_train)
        y_pred_xgb = xgb.predict(X_test_scaled)
        models["xgboost"] = {
            "model": xgb,
            "scaler": scaler,
            "X_test": X_test,
            "feature_names": list(X_train.columns),
            "y_test": y_test,
            "y_pred": y_pred_xgb,
            "r2_score": float(r2_score(y_test, y_pred_xgb)),
        }

    return models


def evaluate_regression(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Compute evaluation metrics for regression predictions."""
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)

    return {
        "rmse": float(rmse),
        "mae": float(mae),
    }


def directional_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate direction accuracy: proportion of times predicted direction matches actual."""
    if len(y_true) < 2 or len(y_pred) < 2:
        return 0.0

    true_dir = np.sign(np.diff(y_true))
    pred_dir = np.sign(np.diff(y_pred))
    return float((true_dir == pred_dir).mean())


def build_lstm_model(input_shape, units=32):
    if Sequential is None:
        raise ImportError("TensorFlow/Keras is required for LSTM model")

    model = Sequential()
    model.add(LSTM(units, input_shape=input_shape, return_sequences=False))
    model.add(Dense(1, activation="linear"))
    model.compile(optimizer="adam", loss="mse")
    return model


def create_lstm_dataset(series: pd.Series, lookback: int = 20):
    """Build sequences for training LSTM models."""
    X, y = [], []
    for i in range(lookback, len(series)):
        X.append(series[i - lookback : i].values)
        y.append(series[i])
    X = np.array(X)
    y = np.array(y)
    return X, y


from sklearn.model_selection import RandomizedSearchCV
import warnings

def tune_hyperparameters(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str = "Target",
    cv_splits: list = None,
    n_iter: int = 20,
    random_state: int = 42,
) -> dict:
    """Tune hyperparameters for Random Forest and XGBoost using RandomizedSearchCV.
    
    cv_splits should be a list of (train_idx, val_idx) arrays from walk-forward validation.
    Returns dictionary with best parameters and models.
    """
    if cv_splits is None:
        raise ValueError("cv_splits must be provided for chronological tuning.")

    X = df[feature_cols].copy()
    y = df[target_col].values.astype(int)

    # Standardize features (Wait, scaler needs to be fit per fold in CV.
    # We should use a Pipeline with StandardScaler to avoid leakage during CV).
    from sklearn.pipeline import Pipeline

    results = {}

    # Random Forest Tuning
    rf_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("model", RandomForestClassifier(random_state=random_state))
    ])
    rf_param_grid = {
        "model__n_estimators": [50, 100, 200, 300],
        "model__max_depth": [3, 5, 7, 10, None],
        "model__min_samples_split": [2, 5, 10],
        "model__min_samples_leaf": [1, 2, 4],
    }
    rf_search = RandomizedSearchCV(
        rf_pipeline,
        param_distributions=rf_param_grid,
        n_iter=n_iter,
        scoring="roc_auc",
        cv=cv_splits,
        random_state=random_state,
        n_jobs=-1,
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        rf_search.fit(X, y)
    
    results["random_forest"] = {
        "best_params": {k.replace("model__", ""): v for k, v in rf_search.best_params_.items()},
        "best_score": rf_search.best_score_,
    }

    # XGBoost Tuning
    if XGBOOST_AVAILABLE and XGBClassifier is not None:
        xgb_pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("model", XGBClassifier(eval_metric="logloss", random_state=random_state))
        ])
        xgb_param_grid = {
            "model__n_estimators": [50, 100, 200, 300],
            "model__max_depth": [3, 5, 7, 9],
            "model__learning_rate": [0.01, 0.05, 0.1, 0.2],
            "model__subsample": [0.6, 0.8, 1.0],
            "model__colsample_bytree": [0.6, 0.8, 1.0],
        }
        xgb_search = RandomizedSearchCV(
            xgb_pipeline,
            param_distributions=xgb_param_grid,
            n_iter=n_iter,
            scoring="roc_auc",
            cv=cv_splits,
            random_state=random_state,
            n_jobs=-1,
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            xgb_search.fit(X, y)
        
        results["xgboost"] = {
            "best_params": {k.replace("model__", ""): v for k, v in xgb_search.best_params_.items()},
            "best_score": xgb_search.best_score_,
        }

    return results

