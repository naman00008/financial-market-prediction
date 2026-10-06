import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.tracker import add_experiment

initial_results = [
    {"Experiment_ID": "E1", "Version": "1.0", "Model": "Naive Baseline", "Feature_Set": "Basic", "Accuracy": 0.4878, "Precision": 0.4944, "Recall": 0.4946, "F1": 0.4945, "ROC_AUC": 0.4876, "PR_AUC": 0.5006, "Experiment_Type": "Baseline", "Interpretation": "Slightly worse than coin flip."},
    {"Experiment_ID": "E2", "Version": "1.0", "Model": "Logistic Regression", "Feature_Set": "Basic", "Accuracy": 0.5077, "Precision": 0.5083, "Recall": 0.9463, "F1": 0.6587, "ROC_AUC": 0.5134, "PR_AUC": 0.5226, "Experiment_Type": "Baseline", "Interpretation": "High recall but low precision. May be predicting one class constantly."},
    {"Experiment_ID": "E3", "Version": "1.0", "Model": "Random Forest", "Feature_Set": "Technical", "Accuracy": 0.5153, "Precision": 0.5164, "Recall": 0.7983, "F1": 0.6191, "ROC_AUC": 0.5253, "PR_AUC": 0.5358, "Experiment_Type": "Baseline", "Interpretation": "Best accuracy and ROC-AUC among initial baselines."},
    {"Experiment_ID": "E4", "Version": "1.0", "Model": "XGBoost", "Feature_Set": "Technical", "Accuracy": 0.5103, "Precision": 0.5130, "Recall": 0.6782, "F1": 0.5812, "ROC_AUC": 0.5192, "PR_AUC": 0.5297, "Experiment_Type": "Baseline"},
    {"Experiment_ID": "E5", "Version": "1.0", "Model": "XGBoost", "Feature_Set": "Technical + Sentiment", "Accuracy": 0.5103, "Precision": 0.5130, "Recall": 0.6782, "F1": 0.5812, "ROC_AUC": 0.5192, "PR_AUC": 0.5297, "Experiment_Type": "Baseline", "Interpretation": "Identical to E4. Need to audit sentiment features."}
]

for res in initial_results:
    add_experiment(res)
