import pickle
import numpy as np
import os

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
    """Validate input data"""
    required_fields = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
    
    # Check all required fields are present
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate ranges
    ranges = {
        'N': (0, 140),
        'P': (5, 145),
        'K': (5, 205),
        'temperature': (8.0, 44.0),
        'humidity': (14.0, 100.0),
        'ph': (3.5, 10.0),
        'rainfall': (20.0, 300.0)
    }
    
    for field, (min_val, max_val) in ranges.items():
        value = data[field]
        if not isinstance(value, (int, float)):
            raise ValueError(f"{field} must be a number")
        if value < min_val or value > max_val:
            raise ValueError(f"{field} must be between {min_val} and {max_val}")
    
    return True

def prepare_input(data):
    """Prepare input array for model prediction"""
    return np.array([[
        data["N"],
        data["P"],
        data["K"],
        data["temperature"],
        data["humidity"],
        data["ph"],
        data["rainfall"]
    ]])