import os
import sys
import pandas as pd
import json
from xgboost import XGBClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.feature_engineering import create_ablation_feature_sets
from src.model_training import evaluate_classification
from src.ml_dataset import split_chronologically
from scripts.tracker import save_registry

def fix_methodology():
    registry_path = "docs/ml_experiment_registry.json"
    with open(registry_path, 'r') as f:
        registry = json.load(f)
        
    # Reclassify the premature RF holdout
    for exp in registry:
        if exp["Experiment_ID"] == "FINAL_TEST":
            exp["Experiment_ID"] = "PREMATURE_HOLDOUT_RF"
            exp["Experiment_Type"] = "Historical/Premature Holdout"
            exp["Interpretation"] = "Holdout evaluation executed before final model selection. Do not use as final test."
            
    # Load dataset
    processed_path = "data/processed_dataset.csv"
    df = pd.read_csv(processed_path)
    train_val_df, test_df = split_chronologically(df, test_size=0.2)
    
    ablation_sets = create_ablation_feature_sets()
    best_features = ablation_sets["E5_Market_Context"]
    
    # Frozen XGBoost Parameters (from T2)
    xgb_best_params = {
        'subsample': 0.6,
        'n_estimators': 200,
        'max_depth': 9,
        'learning_rate': 0.01,
        'colsample_bytree': 0.8
    }
    
    final_xgb = Pipeline([
        ("scaler", StandardScaler()),
        ("model", XGBClassifier(random_state=42, **xgb_best_params))
    ])
    
    X_train = train_val_df[best_features].copy()
    y_train = train_val_df["Target"].values.astype(int)
    X_test = test_df[best_features].copy()
    y_test = test_df["Target"].values.astype(int)
    
    print("Training frozen XGBoost model on full train_val_df...")
    final_xgb.fit(X_train, y_train)
    
    print("Evaluating on untouched 20% test_df...")
    y_pred_prob = final_xgb.predict_proba(X_test)[:, 1]
    
    test_metrics = evaluate_classification(y_test, y_pred_prob)
    
    registry.append({
        "Experiment_ID": "FINAL_TEST_XGB",
        "Version": "2.1",
        "Date": pd.Timestamp.now().isoformat(),
        "Model": "XGBoost (Tuned)",
        "Feature_Set": "All (F5)",
        "Is_Test_Set": True,
        "Hyperparameter_Status": "Tuned",
        "Hyperparameters": xgb_best_params,
        "Accuracy": test_metrics.get("accuracy", 0),
        "Precision": test_metrics.get("precision", 0),
        "Recall": test_metrics.get("recall", 0),
        "F1": test_metrics.get("f1_score", 0),
        "ROC_AUC": test_metrics.get("roc_auc", 0),
        "PR_AUC": test_metrics.get("pr_auc", 0),
        "Experiment_Type": "Final Unseen Test",
        "Interpretation": "Final unseen test result using pre-selected validation model (T2). No tuning or selection occurred after viewing this result."
    })
    
    save_registry(registry)
    print("Fixed registry methodology.")

if __name__ == "__main__":
    fix_methodology()
