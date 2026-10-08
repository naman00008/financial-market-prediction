import numpy as np
import pandas as pd
import shap
import matplotlib.pyplot as plt

def get_tree_explainer(model, X_train):
    """
    Returns a SHAP TreeExplainer for tree-based models like Random Forest or XGBoost.
    """
    # For some models, we might need to configure feature perturbation
    explainer = shap.TreeExplainer(model, X_train)
    return explainer

def generate_shap_summary_plot(model, X_test, show_plot=False, save_path=None):
    """
    Generates a SHAP summary plot for global feature importance.
    """
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    
    # SHAP sometimes returns a list of arrays for classification (one for each class). 
    # For binary classification, we usually take the values for class 1.
    if isinstance(shap_values, list):
        shap_values = shap_values[1]
        
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_test, show=show_plot)
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight')
        plt.close()
    
    return shap_values

def generate_local_explanation(model, X_test, instance_index, show_plot=False, save_path=None):
    """
    Generates a SHAP force plot or waterfall plot for a single prediction.
    """
    explainer = shap.TreeExplainer(model)
    
    # In shap 0.40+, explainer(X) returns an Explanation object which is easier to plot
    explanation = explainer(X_test.iloc[[instance_index]])
    
    # For binary classification with TreeExplainer, explanation.values might have shape (1, num_features, 2)
    if len(explanation.values.shape) == 3:
        # Slice for the positive class (class 1)
        explanation = explanation[:, :, 1]
    
    plt.figure(figsize=(12, 6))
    # Waterfall plot is great for local explainability
    shap.plots.waterfall(explanation[0], show=show_plot)
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight')
        plt.close()
        
    return explanation

def get_global_feature_importance(model, X_test):
    """
    Returns a DataFrame of features sorted by their mean absolute SHAP value.
    This serves as a robust global feature importance metric.
    """
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    
    if isinstance(shap_values, list):
        shap_values = shap_values[1]
        
    # Calculate mean absolute SHAP values for each feature
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    
    importance_df = pd.DataFrame({
        'Feature': X_test.columns,
        'SHAP_Importance': mean_abs_shap
    }).sort_values(by='SHAP_Importance', ascending=False).reset_index(drop=True)
    
    return importance_df
