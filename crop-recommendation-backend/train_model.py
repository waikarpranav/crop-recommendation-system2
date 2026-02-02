import pandas as pd
import pickle
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from feature_engineering import engineer_features

def train_and_save_model():
    """Retrain model with engineered features and save artifacts"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, 'Data', 'Crop_recommendation.csv')
    
    if not os.path.exists(data_path):
        print(f"Error: Dataset not found at {data_path}")
        return

    # Load data
    df = pd.read_csv(data_path)
    X = df.drop('label', axis=1)
    y = df['label']

    # Apply feature engineering
    print("Applying feature engineering...")
    X_engineered = engineer_features(X)

    # Scale features
    print("Scaling features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_engineered)

    # Train model
    print("Training Random Forest model...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_scaled, y)

    # Save artifacts
    ml_models_dir = os.path.join(base_dir, 'ml_models')
    os.makedirs(ml_models_dir, exist_ok=True)

    model_path = os.path.join(ml_models_dir, 'crop_recommendation_model.pkl')
    scaler_path = os.path.join(ml_models_dir, 'scaler.pkl')

    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)

    print(f"✓ Model saved to {model_path}")
    print(f"✓ Scaler saved to {scaler_path}")
    
    # Save the feature names for reference in utils.py
    feature_names = X_engineered.columns.tolist()
    print(f"Features used: {feature_names}")
    
    return model, scaler, feature_names

if __name__ == "__main__":
    train_and_save_model()
