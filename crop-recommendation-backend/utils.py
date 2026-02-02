import pickle
import numpy as np
import os
from feature_engineering import engineer_features

def load_model():
    """Load both model and scaler"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load model
    model_path = os.path.join(base_dir, 'ml_models', 'crop_recommendation_model.pkl')
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    
    # Load scaler
    scaler_path = os.path.join(base_dir, 'ml_models', 'scaler.pkl')
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    
    return model, scaler

def validate_input(data):
    """Robust validation of agricultural inputs with domain constraints"""
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

def prepare_input(data):
    """Prepare engineered features for model prediction"""
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