import os
import pandas as pd
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.feature_engineering import build_feature_groups
from src.ml_dataset import split_chronologically
from src.validation import evaluate_walk_forward
from src.model_training import train_classification_models

def run_experiment():
    print("Loading V1.1 Processed Dataset...")
    df = pd.read_csv("data/v1_1_sentiment/processed/processed_dataset.csv")
    
    train_val_df, test_df = split_chronologically(df, test_size=0.2)
    
    # Define S1 and S2 features
    groups = build_feature_groups()
    base_features = (
        groups["OHLCV"] + 
        groups["Lags"] + 
        groups["Trend"] + 
        groups["Momentum"] + 
        groups["Volatility"] + 
        groups["Volume"] + 
        groups["Market_Context"]
    )
    
    new_sentiment_features = [
        'News_Count', 'Mean_Sentiment', 'Positive_News_Proportion', 
        'Negative_News_Proportion', 'Neutral_News_Proportion'
    ]
    
    s1_features = base_features.copy()
    s2_features = base_features + new_sentiment_features
    
    print("Running Experiment S1 (Without IN-FINews Sentiment)...")
    s1_res = evaluate_walk_forward(
        df=train_val_df,
        feature_cols=s1_features,
        target_col="Target",
        n_splits=5,
        window_type="expanding",
        random_state=42
    )
    
    print("Running Experiment S2 (With IN-FINews Sentiment)...")
    s2_res = evaluate_walk_forward(
        df=train_val_df,
        feature_cols=s2_features,
        target_col="Target",
        n_splits=5,
        window_type="expanding",
        random_state=42
    )
    
    # We only care about XGBoost
    s1_summary = s1_res["summary"].get("xgboost", {})
    s2_summary = s2_res["summary"].get("xgboost", {})
    
    print("\n--- RESULTS ---")
    metrics = ["accuracy", "precision", "recall", "f1_score", "roc_auc", "pr_auc"]
    for m in metrics:
        s1_val = s1_summary.get(f"{m}_mean", 0)
        s2_val = s2_summary.get(f"{m}_mean", 0)
        diff = s2_val - s1_val
        print(f"{m.upper():<10} | S1: {s1_val:.4f} | S2: {s2_val:.4f} | Delta: {diff:+.4f}")
        
    print("\nFold Details ROC-AUC:")
    for i in range(5):
        s1_fold_auc = s1_res["fold_details"][i]["models"]["xgboost"]["roc_auc"]
        s2_fold_auc = s2_res["fold_details"][i]["models"]["xgboost"]["roc_auc"]
        print(f"Fold {i+1}: S1={s1_fold_auc:.4f}, S2={s2_fold_auc:.4f} (Delta: {s2_fold_auc - s1_fold_auc:+.4f})")

if __name__ == "__main__":
    run_experiment()
