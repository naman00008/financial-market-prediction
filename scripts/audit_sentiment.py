import pandas as pd
import numpy as np
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.feature_engineering import create_ablation_feature_sets

def audit_sentiment():
    print("Loading processed dataset...")
    processed_path = "data/processed_dataset.csv"
    if not os.path.exists(processed_path):
        print("Processed dataset not found.")
        return
        
    df = pd.read_csv(processed_path)
    
    print("\n--- Sentiment Columns Audit ---")
    ablation_sets = create_ablation_feature_sets()
    print(f"Features in E4: {len(ablation_sets['E3_Technical_Indicators'])}")
    print(f"Features in E5: {len(ablation_sets['E4_Technical_Plus_Sentiment'])}")
    sentiment_features = ablation_sets['E4_Technical_Plus_Sentiment'][-2:] 
    # Usually "Sentiment_Score", "News_Count"
    print(f"Sentiment features added in E5: {sentiment_features}")
    
    print("\n--- Sentiment Distributions ---")
    for col in sentiment_features:
        if col in df.columns:
            non_zero = (df[col] != 0).sum()
            missing = df[col].isna().sum()
            print(f"Column: {col}")
            print(f"  Missing (NaN): {missing} ({missing/len(df)*100:.2f}%)")
            print(f"  Zeros: {len(df) - non_zero - missing} ({(len(df) - non_zero - missing)/len(df)*100:.2f}%)")
            print(f"  Non-Zeros: {non_zero} ({non_zero/len(df)*100:.2f}%)")
            print(f"  Mean (all): {df[col].mean():.4f}")
            if non_zero > 0:
                print(f"  Mean (non-zero): {df.loc[df[col] != 0, col].mean():.4f}")
        else:
            print(f"Column {col} NOT found in processed_dataset.csv!")

if __name__ == "__main__":
    audit_sentiment()
