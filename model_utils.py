"""
Utility functions for saving and loading trained machine learning models.
Uses joblib for efficient serialization of scikit-learn models.
"""
import joblib
import os
from typing import Dict, Any, Tuple, List


# Directory where models will be saved
MODELS_DIR = "models"


def ensure_models_directory():
    """Create the models directory if it doesn't exist."""
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)
        print(f"Created {MODELS_DIR} directory")


def save_pbp_model(model, feature_columns: List[str], filename: str = "pbp_model.pkl"):
    """
    Save the PBP (play-by-play) model and its feature columns.
    
    Args:
        model: Trained scikit-learn model
        feature_columns: List of feature column names
        filename: Name of the file to save the model
    """
    ensure_models_directory()
    filepath = os.path.join(MODELS_DIR, filename)
    
    data = {
        'model': model,
        'feature_columns': feature_columns
    }
    
    joblib.dump(data, filepath)
    print(f"PBP model saved to {filepath}")


def load_pbp_model(filename: str = "pbp_model.pkl") -> Tuple[Any, List[str]]:
    """
    Load the PBP model and its feature columns.
    
    Args:
        filename: Name of the file to load
        
    Returns:
        Tuple of (model, feature_columns)
    """
    filepath = os.path.join(MODELS_DIR, filename)
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Model file not found: {filepath}")
    
    data = joblib.load(filepath)
    print(f"PBP model loaded from {filepath}")
    
    return data['model'], data['feature_columns']


def save_run_models(trained_models: Dict[str, Dict[str, Any]], filename: str = "run_models.pkl"):
    """
    Save all run models (run_gap, run_location, offense_formation, personnel_off).
    
    Args:
        trained_models: Dictionary of trained models with their metadata
        filename: Name of the file to save the models
    """
    ensure_models_directory()
    filepath = os.path.join(MODELS_DIR, filename)
    
    joblib.dump(trained_models, filepath)
    print(f"Run models saved to {filepath}")


def load_run_models(filename: str = "run_models.pkl") -> Dict[str, Dict[str, Any]]:
    """
    Load all run models.
    
    Args:
        filename: Name of the file to load
        
    Returns:
        Dictionary of trained models with their metadata
    """
    filepath = os.path.join(MODELS_DIR, filename)
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Model file not found: {filepath}")
    
    trained_models = joblib.load(filepath)
    print(f"Run models loaded from {filepath}")
    
    return trained_models


def save_pass_model(model, feature_columns: List[str], df_pass_processed=None, filename: str = "pass_model.pkl"):
    """
    Save the pass model and its feature columns.
    
    Args:
        model: Trained scikit-learn model
        feature_columns: List of feature column names
        df_pass_processed: Optional processed dataframe (can be omitted to save space)
        filename: Name of the file to save the model
    """
    ensure_models_directory()
    filepath = os.path.join(MODELS_DIR, filename)
    
    data = {
        'model': model,
        'feature_columns': feature_columns,
        # Optionally include processed dataframe (can be large)
        # 'df_pass_processed': df_pass_processed
    }
    
    joblib.dump(data, filepath)
    print(f"Pass model saved to {filepath}")


def load_pass_model(filename: str = "pass_model.pkl") -> Tuple[Any, List[str]]:
    """
    Load the pass model and its feature columns.
    
    Args:
        filename: Name of the file to load
        
    Returns:
        Tuple of (model, feature_columns)
    """
    filepath = os.path.join(MODELS_DIR, filename)
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Model file not found: {filepath}")
    
    data = joblib.load(filepath)
    print(f"Pass model loaded from {filepath}")
    
    return data['model'], data['feature_columns']


def check_models_exist() -> Dict[str, bool]:
    """
    Check which model files exist.
    
    Returns:
        Dictionary with model names as keys and existence status as values
    """
    models = {
        'pbp_model': os.path.exists(os.path.join(MODELS_DIR, "pbp_model.pkl")),
        'run_models': os.path.exists(os.path.join(MODELS_DIR, "run_models.pkl")),
        'pass_model': os.path.exists(os.path.join(MODELS_DIR, "pass_model.pkl"))
    }
    
    return models
