import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

try:
    import shap
    HAS_SHAP = True
except ImportError:
    shap = None
    HAS_SHAP = False

def get_tree_explainer(model, X_train=None):
    """
    Returns a SHAP TreeExplainer for tree-based models like Random Forest or XGBoost.
    """
    if HAS_SHAP and shap is not None:
        try:
            if X_train is not None:
                return shap.TreeExplainer(model, X_train)
            return shap.TreeExplainer(model)
        except Exception:
            pass
    return None

def generate_shap_summary_plot(model, X_test, show_plot=False, save_path=None):
    """
    Generates a SHAP summary plot for global feature importance.
    """
    if not (HAS_SHAP and shap is not None):
        return None
    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_test)
        
        if isinstance(shap_values, list):
            shap_values = shap_values[1]
            
        plt.figure(figsize=(10, 8))
        shap.summary_plot(shap_values, X_test, show=show_plot)
        
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            plt.close()
        
        return shap_values
    except Exception:
        return None

def generate_local_explanation(model, X_test, instance_index, show_plot=False, save_path=None):
    """
    Generates a SHAP force plot or waterfall plot for a single prediction.
    """
    if not (HAS_SHAP and shap is not None):
        return None
    try:
        explainer = shap.TreeExplainer(model)
        explanation = explainer(X_test.iloc[[instance_index]])
        
        if hasattr(explanation, 'values') and len(explanation.values.shape) == 3:
            explanation = explanation[:, :, 1]
        
        plt.figure(figsize=(12, 6))
        shap.plots.waterfall(explanation[0], show=show_plot)
        
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            plt.close()
            
        return explanation
    except Exception:
        return None

def get_global_feature_importance(model, X_test):
    """
    Returns a DataFrame of features sorted by feature importance / SHAP value.
    Supports DataFrame or list of column names, and falls back gracefully
    to tree model feature_importances_ if SHAP is absent or computation fails.
    """
    if isinstance(X_test, (list, tuple, np.ndarray)):
        cols = list(X_test)
    elif hasattr(X_test, 'columns'):
        cols = list(X_test.columns)
    else:
        cols = [f"Feature_{i}" for i in range(len(getattr(model, 'feature_importances_', [])))]

    importances = None

    if HAS_SHAP and shap is not None and hasattr(X_test, 'columns'):
        try:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_test)
            if isinstance(shap_values, list):
                shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
            elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
                # Shape: (n_samples, n_features, n_classes) -> extract positive class (index 1)
                shap_values = shap_values[:, :, 1] if shap_values.shape[-1] > 1 else shap_values[:, :, 0]
            importances = np.abs(shap_values).mean(axis=0)
            if importances.ndim > 1:
                importances = importances.flatten()
        except Exception:
            importances = None

    if importances is None:
        if hasattr(model, 'feature_importances_'):
            importances = np.array(model.feature_importances_)
        elif hasattr(model, 'coef_'):
            importances = np.abs(np.array(model.coef_)).flatten()
        else:
            importances = np.ones(len(cols)) / max(len(cols), 1)

    importances = np.asarray(importances, dtype=float).flatten()
    if len(importances) != len(cols):
        importances = importances[:len(cols)]

    df = pd.DataFrame({
        'Feature': cols,
        'Importance': importances,
        'SHAP_Importance': importances
    }).sort_values(by='Importance', ascending=False).reset_index(drop=True)

    return df

