import os
import json
import pandas as pd

def generate_master_results():
    registry_path = "docs/ml_experiment_registry.json"
    with open(registry_path, 'r') as f:
        registry = json.load(f)
        
    df = pd.DataFrame(registry)
    cols = ['Experiment_ID', 'Model', 'Feature_Set', 'Accuracy', 'Precision', 'Recall', 'F1', 'ROC_AUC', 'PR_AUC']
    
    with open("docs/MASTER_RESULTS.md", 'w') as f:
        f.write("# Master Results Report\n\n")
        f.write("## 1. Initial Baseline Results\n")
        baselines = df[(df['Experiment_Type'] == 'Baseline')]
        f.write(baselines[cols].to_markdown(index=False))
        f.write("\n\n")
        
        f.write("## 2. Feature Ablation Results\n")
        ablation = df[(df['Experiment_Type'] == 'Ablation')]
        f.write(ablation[cols].to_markdown(index=False))
        f.write("\n\n")

        f.write("## 3. Model Tuning Results\n")
        tuning = df[(df['Experiment_Type'] == 'Tuning')]
        f.write(tuning[['Experiment_ID', 'Model', 'Feature_Set', 'Hyperparameters', 'ROC_AUC']].to_markdown(index=False))
        f.write("\n\n")
        
        f.write("## 4. Final Model Selection\n")
        f.write("- **Selection metric:** ROC-AUC\n")
        f.write("- **Selection methodology:** 5-fold expanding Walk-Forward Validation\n")
        f.write("- **Selected model:** XGBoost (Tuned) [Experiment T2]\n")
        f.write("- **Selected feature set:** All (F5) - OHLCV + Lags + Tech + Sentiment + Market Context\n")
        f.write("- *Note:* Selection was based on WFV validation strictly. The final holdout test was NOT used for model selection.\n\n")
        
        f.write("## 5. Historical/Premature Holdout Evaluations\n")
        f.write("This section preserves historical holdout evaluations that were run prior to finalizing the model selection process. These are NOT the final test results.\n\n")
        premature = df[df['Experiment_Type'] == 'Historical/Premature Holdout']
        if not premature.empty:
            f.write(premature[cols].to_markdown(index=False))
        f.write("\n\n")
        
        f.write("## 6. Final Unseen Test\n")
        final_test = df[df['Experiment_Type'] == 'Final Unseen Test']
        if not final_test.empty:
            f.write(final_test[cols].to_markdown(index=False))
            f.write("\n\n")
            f.write("- **Test Period:** Chronological Final 20% Holdout\n")
            f.write("- *Note:* No tuning or selection occurred after viewing this result.\n\n")
        
        f.write("## 7. Key Findings\n")
        f.write("- **Sentiment Audit:** Sentiment features (`Sentiment_Score` and `News_Count`) were exactly zero for 100% of the dataset, providing no signal.\n")
        f.write("- **Feature Engineering:** Adding technicals and market context improved performance over basic OHLCV.\n")
        f.write("- **Model Comparison:** Tree-based models (Random Forest and XGBoost) generalized better than Logistic Regression.\n")
        f.write("- **Tuning:** Random Search on walk-forward folds prevented test-set leakage while selecting optimal hyperparameters.\n\n")
        
        f.write("## 8. Limitations\n")
        f.write("- **Market Context Dependency:** Current market proxy assumes an equal-weighted basket, not actual NIFTY.\n")
        f.write("- **Non-stationarity:** Financial markets evolve, and a predictive edge can diminish over time.\n")
        f.write("- **Zero Sentiment:** Missing natural language data implies we cannot test true NLP capabilities here without acquiring better alternative data.\n")
        
    print("Generated docs/MASTER_RESULTS.md successfully.")

if __name__ == "__main__":
    generate_master_results()
