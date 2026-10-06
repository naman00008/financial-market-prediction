import os
import sys
import pandas as pd
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.dataset_builder import build_and_save_panel_dataset
from src.feature_engineering import create_ablation_feature_sets
from src.validation import evaluate_walk_forward
from src.model_training import tune_hyperparameters, train_classification_models
from src.ml_dataset import split_chronologically
from scripts.tracker import add_experiment, update_tracker_markdown

def run_all_experiments():
    processed_path = "data/processed_dataset.csv"
    print("Rebuilding panel dataset with Market Context features...")
    df = build_and_save_panel_dataset(output_path=processed_path)
    
    # Fill NAs introduced by Market Context if any
    df = df.fillna(0)

    train_val_df, test_df = split_chronologically(df, test_size=0.2)
    
    ablation_sets = create_ablation_feature_sets()
    
    # Phase 6: Ablation Study
    # The user wants F1=OHLCV, F2=OHLCV+Lags, F3=OHLCV+Lags+Tech, F4=F3+Sentiment, F5=F4+Market
    print("\n--- Running Feature Ablation Study ---")
    ablation_experiments = [
        {"id": "F1", "name": "OHLCV Only", "features": ablation_sets["E1_OHLCV_Only"]},
        {"id": "F2", "name": "OHLCV + Lags", "features": ablation_sets["E2_OHLCV_Plus_Lags"]},
        {"id": "F3", "name": "OHLCV + Lags + Tech", "features": ablation_sets["E3_Technical_Indicators"]},
        {"id": "F4", "name": "OHLCV + Lags + Tech + Sentiment", "features": ablation_sets["E4_Technical_Plus_Sentiment"]},
        {"id": "F5", "name": "OHLCV + Lags + Tech + Sentiment + Market", "features": ablation_sets["E5_Market_Context"]}
    ]
    
    # We will use Random Forest as it was the best base model
    model_name = "random_forest"
    
    for exp in ablation_experiments:
        print(f"Running {exp['id']} with {exp['name']}...")
        wfv = evaluate_walk_forward(
            df=train_val_df,
            feature_cols=exp["features"],
            target_col="Target",
            n_splits=5,
            window_type="expanding",
            random_state=42
        )
        metrics = wfv["summary"].get(model_name, {})
        add_experiment({
            "Experiment_ID": exp["id"],
            "Version": "2.0",
            "Model": "Random Forest",
            "Feature_Set": exp["name"],
            "Feature_Count": len(exp["features"]),
            "Accuracy": metrics.get("accuracy_mean", 0),
            "Precision": metrics.get("precision_mean", 0),
            "Recall": metrics.get("recall_mean", 0),
            "F1": metrics.get("f1_score_mean", 0),
            "ROC_AUC": metrics.get("roc_auc_mean", 0),
            "PR_AUC": metrics.get("pr_auc_mean", 0),
            "Experiment_Type": "Ablation",
            "Fold_Details": wfv["fold_details"]
        })
    
    # Phase 5: Hyperparameter Tuning
    print("\n--- Running Hyperparameter Tuning ---")
    best_features = ablation_sets["E5_Market_Context"] # assume best features
    from src.validation import generate_walk_forward_splits
    cv_splits = generate_walk_forward_splits(n_samples=len(train_val_df), n_splits=5, window_type="expanding")
    
    tuning_res = tune_hyperparameters(
        df=train_val_df,
        feature_cols=best_features,
        target_col="Target",
        cv_splits=cv_splits,
        n_iter=10, # Keep it small for time
        random_state=42
    )
    
    # Evaluate Default vs Tuned Random Forest
    rf_best_params = tuning_res["random_forest"]["best_params"]
    print(f"RF Best Params: {rf_best_params}")
    add_experiment({
        "Experiment_ID": "T1",
        "Version": "2.0",
        "Model": "Random Forest (Tuned)",
        "Feature_Set": "All (F5)",
        "Hyperparameter_Status": "Tuned",
        "Hyperparameters": rf_best_params,
        "ROC_AUC": tuning_res["random_forest"]["best_score"],
        "Experiment_Type": "Tuning"
    })
    
    xgb_best_params = tuning_res.get("xgboost", {}).get("best_params", {})
    if xgb_best_params:
        print(f"XGB Best Params: {xgb_best_params}")
        add_experiment({
            "Experiment_ID": "T2",
            "Version": "2.0",
            "Model": "XGBoost (Tuned)",
            "Feature_Set": "All (F5)",
            "Hyperparameter_Status": "Tuned",
            "Hyperparameters": xgb_best_params,
            "ROC_AUC": tuning_res["xgboost"]["best_score"],
            "Experiment_Type": "Tuning"
        })

    # Phase 8: Final 20% Test
    print("\n--- Running Final Test on 20% Holdout ---")
    # Train Random Forest with tuned params on full train_val_df
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from src.model_training import evaluate_classification
    
    final_rf = Pipeline([
        ("scaler", StandardScaler()),
        ("model", RandomForestClassifier(random_state=42, **rf_best_params))
    ])
    
    X_train = train_val_df[best_features].copy()
    y_train = train_val_df["Target"].values.astype(int)
    X_test = test_df[best_features].copy()
    y_test = test_df["Target"].values.astype(int)
    
    final_rf.fit(X_train, y_train)
    y_pred_prob = final_rf.predict_proba(X_test)[:, 1]
    
    test_metrics = evaluate_classification(y_test, y_pred_prob)
    
    add_experiment({
        "Experiment_ID": "FINAL_TEST",
        "Version": "2.0",
        "Model": "Random Forest (Tuned)",
        "Feature_Set": "All (F5)",
        "Is_Test_Set": True,
        "Hyperparameter_Status": "Tuned",
        "Hyperparameters": rf_best_params,
        "Accuracy": test_metrics.get("accuracy", 0),
        "Precision": test_metrics.get("precision", 0),
        "Recall": test_metrics.get("recall", 0),
        "F1": test_metrics.get("f1_score", 0),
        "ROC_AUC": test_metrics.get("roc_auc", 0),
        "PR_AUC": test_metrics.get("pr_auc", 0),
        "Experiment_Type": "Final Test",
        "Interpretation": "Final unseen test result using best validation model."
    })
    
    print("All experiments complete. Tracker updated.")

if __name__ == "__main__":
    run_all_experiments()
