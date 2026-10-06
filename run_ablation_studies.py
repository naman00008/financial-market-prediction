import json
import os
import pandas as pd
import numpy as np

from src.dataset_builder import build_and_save_panel_dataset
from src.feature_engineering import create_features, create_ablation_feature_sets
from src.ml_dataset import create_next_day_direction_target, split_chronologically
from src.validation import evaluate_walk_forward
from src.model_training import tune_hyperparameters

def run_ablation_studies():
    print("Loading raw dataset...")
    processed_path = "data/processed_dataset.csv"
    if os.path.exists(processed_path):
        df = pd.read_csv(processed_path)
    else:
        print("Processed dataset not found. Generating from sample...")
        df = build_and_save_panel_dataset(output_path=processed_path)


    train_val_df, test_df = split_chronologically(df, test_size=0.2)

    ablation_sets = create_ablation_feature_sets()
    
    experiments = [
        {"id": "E1", "model": "baseline", "feature_set_name": "Basic", "features": ablation_sets["E1_OHLCV_Only"]},
        {"id": "E2", "model": "logistic_regression", "feature_set_name": "Basic", "features": ablation_sets["E1_OHLCV_Only"]},
        {"id": "E3", "model": "random_forest", "feature_set_name": "Technical", "features": ablation_sets["E3_Technical_Indicators"]},
        {"id": "E4", "model": "xgboost", "feature_set_name": "Technical", "features": ablation_sets["E3_Technical_Indicators"]},
        {"id": "E5", "model": "xgboost", "feature_set_name": "Technical + Sentiment", "features": ablation_sets["E4_Technical_Plus_Sentiment"]},
    ]

    results_table = []
    
    for exp in experiments:
        print(f"Running Experiment {exp['id']}: {exp['model']} with {exp['feature_set_name']} features...")
        
        wfv_results = evaluate_walk_forward(
            df=train_val_df,
            feature_cols=exp["features"],
            target_col="Target",
            n_splits=5,
            window_type="expanding",
            random_state=42
        )
        
        summary = wfv_results["summary"]
        
        if exp["model"] not in summary:
            print(f"Model {exp['model']} not found in results. Skipping.")
            continue
            
        model_metrics = summary[exp["model"]]
        
        results_table.append({
            "Experiment": exp["id"],
            "Model": exp["model"].replace("_", " ").title(),
            "Feature Set": exp["feature_set_name"],
            "Validation Method": "Walk-forward",
            "Accuracy": model_metrics.get("accuracy_mean", 0.0),
            "Precision": model_metrics.get("precision_mean", 0.0),
            "Recall": model_metrics.get("recall_mean", 0.0),
            "F1": model_metrics.get("f1_score_mean", 0.0),
            "ROC-AUC": model_metrics.get("roc_auc_mean", 0.0),
            "PR-AUC": model_metrics.get("pr_auc_mean", 0.0),
        })

    md_table = "| Experiment | Model | Feature Set | Validation Method | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |\n"
    md_table += "|---|---|---|---|---:|---:|---:|---:|---:|---:|\n"
    
    for row in results_table:
        md_table += f"| {row['Experiment']} | {row['Model']} | {row['Feature Set']} | {row['Validation Method']} | "
        md_table += f"{row['Accuracy']:.4f} | {row['Precision']:.4f} | {row['Recall']:.4f} | {row['F1']:.4f} | "
        md_table += f"{row['ROC-AUC']:.4f} | {row['PR-AUC']:.4f} |\n"

    os.makedirs("docs", exist_ok=True)
    with open("docs/MASTER_RESULTS.md", "w") as f:
        f.write("# Master Results Table\n\n")
        f.write("Generated using 5-fold expanding walk-forward validation on the training set.\n\n")
        f.write(md_table)
        
    print("Master results table saved to docs/MASTER_RESULTS.md")

if __name__ == "__main__":
    run_ablation_studies()
