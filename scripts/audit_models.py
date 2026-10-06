import os
import sys
import pandas as pd
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.validation import evaluate_walk_forward
from src.feature_engineering import create_ablation_feature_sets
from src.ml_dataset import split_chronologically

def audit_models():
    processed_path = "data/processed_dataset.csv"
    df = pd.read_csv(processed_path)
    train_val_df, test_df = split_chronologically(df, test_size=0.2)
    
    ablation_sets = create_ablation_feature_sets()
    features = ablation_sets["E1_OHLCV_Only"] # Basic features for Logistic Regression
    
    wfv_results = evaluate_walk_forward(
        df=train_val_df,
        feature_cols=features,
        target_col="Target",
        n_splits=5,
        window_type="expanding",
        random_state=42
    )
    
    print("\n--- Logistic Regression Fold-by-Fold Results (Basic Features) ---")
    for fold in wfv_results["fold_details"]:
        lr_metrics = fold["models"].get("logistic_regression", {})
        print(f"Fold {fold['fold']}:")
        print(f"  Accuracy:  {lr_metrics.get('accuracy', 0):.4f}")
        print(f"  Precision: {lr_metrics.get('precision', 0):.4f}")
        print(f"  Recall:    {lr_metrics.get('recall', 0):.4f}")
        print(f"  F1:        {lr_metrics.get('f1_score', 0):.4f}")
        print(f"  Confusion Matrix: {lr_metrics.get('confusion_matrix')}")
        
if __name__ == "__main__":
    audit_models()
