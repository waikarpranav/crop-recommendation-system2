import pickle
import numpy as np
import os
from typing import Tuple, Dict, Any, List, Optional
from feature_engineering import engineer_features

def load_model(model_path: Optional[str] = None, scaler_path: Optional[str] = None) -> Tuple[Any, Any]:
    """
    Load trained ML model and feature scaler from disk.
    
    Args:
        model_path: Absolute path to pickled model file
        scaler_path: Absolute path to pickled scaler file
        
    Returns:
        Tuple of (model, scaler) objects
        
    Raises:
        FileNotFoundError: If either artifact is missing
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    if not model_path:
        model_path = os.path.join(base_dir, 'ml_models', 'crop_recommendation_model.pkl')
    if not scaler_path:
        scaler_path = os.path.join(base_dir, 'ml_models', 'scaler.pkl')
        
    print(f"🔍 Loading model from: {model_path}")
    print(f"🔍 Loading scaler from: {scaler_path}")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}")
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(f"Scaler file not found at {scaler_path}")

    with open(model_path, "rb") as f:
        model = pickle.load(f)
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    
    return model, scaler

def validate_input(data: Dict[str, Any]) -> List[str]:
    """
    Validate agricultural input data against domain-specific constraints.
    
    Args:
        data: Dictionary containing soil and climate measurements
        
    Returns:
        List of validation error messages (empty if valid)
        
    Example:
        >>> errors = validate_input({'N': 50, 'P': 60, ...})
        >>> if errors:
        >>>     print("Validation failed:", errors)
    """
    errors = []
    required_fields = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
    
    # 1. Check required fields
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
            
    if errors:
        return errors
        
    # 2. Domain-specific validation constraints
    constraints = {
        'N': (0, 140, 'Nitrogen'),
        'P': (5, 145, 'Phosphorus'),
        'K': (5, 205, 'Potassium'),
        'temperature': (8, 44, 'Temperature'),
        'humidity': (14, 100, 'Humidity'),
        'ph': (3.5, 10, 'pH'),
        'rainfall': (20, 300, 'Rainfall')
    }
    
    for field, (min_val, max_val, name) in constraints.items():
        try:
            val = float(data[field])
            if val < min_val or val > max_val:
                errors.append(f"{name} must be between {min_val} and {max_val}")
        except (ValueError, TypeError):
            errors.append(f"{name} must be a valid number")
            
    return errors

def prepare_input(data: Dict[str, float]) -> np.ndarray:
    """
    Transform raw agricultural data into engineered feature array for ML model.
    
    Args:
        data: Dictionary with keys: N, P, K, temperature, humidity, ph, rainfall
        
    Returns:
        2D numpy array ready for model.predict() or scaler.transform()
        
    Note:
        Feature order must match training pipeline exactly.
    """
    # engineer_features returns a dict when given a dict
    features_dict = engineer_features(data)
    
    # Ensure features are in the correct order for the model
    # The order must match the one used during training
    feature_order = [
        'N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall',
        'NPK_ratio', 'nutrient_balance', 'temp_humidity_index', 
        'ph_optimality', 'water_stress_index', 'growing_degree_days', 
        'N_P_ratio', 'N_K_ratio'
    ]
    
    input_list = [features_dict[f] for f in feature_order]
    return np.array([input_list])