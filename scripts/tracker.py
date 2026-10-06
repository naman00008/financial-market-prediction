import json
import os
import pandas as pd
from datetime import datetime

REGISTRY_PATH = "docs/ml_experiment_registry.json"
TRACKER_PATH = "docs/ML_EXPERIMENT_TRACKER.md"

def load_registry():
    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH, 'r') as f:
            return json.load(f)
    return []

def save_registry(registry):
    os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
    with open(REGISTRY_PATH, 'w') as f:
        json.dump(registry, f, indent=4)
    update_tracker_markdown(registry)

def update_tracker_markdown(registry):
    df = pd.DataFrame(registry)
    
    with open(TRACKER_PATH, 'w') as f:
        f.write("# ML Experiment Tracker\n\n")
        f.write("This document permanently tracks all ML experiments conducted for the AUCML ESE Financial Market Prediction project.\n\n")
        
        f.write("## Current Best Results\n")
        if not df.empty:
            # Sort by ROC-AUC and Accuracy
            val_df = df[df['Is_Test_Set'] == False].sort_values(by=['ROC_AUC', 'Accuracy'], ascending=[False, False])
            if not val_df.empty:
                best = val_df.iloc[0]
                f.write(f"- **Best Model**: {best['Model']}\n")
                f.write(f"- **Experiment ID**: {best['Experiment_ID']}\n")
                f.write(f"- **Validation Accuracy**: {best.get('Accuracy', 0):.4f}\n")
                f.write(f"- **Validation ROC-AUC**: {best.get('ROC_AUC', 0):.4f}\n")
                f.write(f"- **Validation F1**: {best.get('F1', 0):.4f}\n")
                f.write(f"- **Feature Set**: {best['Feature_Set']}\n")
                f.write("\n")
        
        f.write("## Current Model Leaderboard\n")
        if not df.empty:
            val_df = df[df['Is_Test_Set'] == False].sort_values(by=['ROC_AUC', 'Accuracy'], ascending=[False, False])
            cols = ['Experiment_ID', 'Model', 'Feature_Set', 'Accuracy', 'Precision', 'Recall', 'F1', 'ROC_AUC', 'PR_AUC']
            # only select columns that exist
            cols = [c for c in cols if c in val_df.columns]
            f.write(val_df[cols].to_markdown(index=False))
            f.write("\n\n")
            
        f.write("## Version History\n")
        if not df.empty:
            f.write(df.to_markdown(index=False))
            f.write("\n\n")

def add_experiment(record):
    registry = load_registry()
    
    # Defaults
    full_record = {
        "Experiment_ID": record.get("Experiment_ID", f"EXP-{len(registry)+1}"),
        "Version": record.get("Version", "1.0"),
        "Date": datetime.now().isoformat(),
        "Model": record.get("Model", "Unknown"),
        "Feature_Set": record.get("Feature_Set", "Unknown"),
        "Feature_Count": record.get("Feature_Count", 0),
        "Dataset_Version": record.get("Dataset_Version", "V1"),
        "Validation_Method": record.get("Validation_Method", "WFV-5-Expanding"),
        "Number_of_Folds": record.get("Number_of_Folds", 5),
        "Is_Test_Set": record.get("Is_Test_Set", False),
        "Hyperparameter_Status": record.get("Hyperparameter_Status", "Default"),
        "Hyperparameters": record.get("Hyperparameters", {}),
        "Random_Seed": record.get("Random_Seed", 42),
        "Accuracy": record.get("Accuracy", 0.0),
        "Precision": record.get("Precision", 0.0),
        "Recall": record.get("Recall", 0.0),
        "F1": record.get("F1", 0.0),
        "ROC_AUC": record.get("ROC_AUC", 0.0),
        "PR_AUC": record.get("PR_AUC", 0.0),
        "Status": record.get("Status", "Complete"),
        "Notes": record.get("Notes", ""),
        "Interpretation": record.get("Interpretation", ""),
        "Experiment_Type": record.get("Experiment_Type", "Baseline"),
        "Fold_Details": record.get("Fold_Details", [])
    }
    
    registry.append(full_record)
    save_registry(registry)
    print(f"Added experiment {full_record['Experiment_ID']}")
