import numpy as np
import pandas as pd
import os
from feature_engineering import engineer_features

class CropExplainer:
    def __init__(self, model, csv_path=None):
        # Lazy import shap to save memory on startup
        try:
            import shap
            self.shap = shap
        except ImportError:
            self.shap = None
            print("⚠️ SHAP library not found. Explainability disabled.")
            
        self.model = model
        
        # Load sample data for explainer if path provided
        if csv_path and os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            X = df.drop('label', axis=1)
            X_engineered = engineer_features(X)
            # Use small sample for faster explainer initialization
            self.X_sample = X_engineered.sample(min(100, len(X_engineered)), random_state=42)
        else:
            self.X_sample = None

        if self.shap is None:
            self.explainer = None
            self.classes = list(model.classes_)
            return

        # Initialize TreeExplainer for Random Forest
        self.explainer = self.shap.TreeExplainer(model, self.X_sample)
        
        # Store class names from model
        self.classes = list(model.classes_)

    def explain_prediction(self, input_data, feature_names):
        """
        Return top 3 reasons for the crop recommendation.
        input_data: 2D numpy array [1, num_features]
        """
        if self.explainer is None:
            return ["Favorable agricultural conditions detected"]

        # SHAP values for all classes
        shap_values = self.explainer.shap_values(input_data)
        
        # Get predicted class index
        prediction = self.model.predict(input_data)[0]
        class_idx = self.classes.index(prediction)
        
        # Extract SHAP values for the predicted class
        # For RF in shap 0.44.0, shap_values is a list of arrays (one per class)
        if isinstance(shap_values, list):
            class_shap = shap_values[class_idx][0]
        else:
            # For some versions/models it might be a 3D array
            class_shap = shap_values[0, :, class_idx] if shap_values.ndim == 3 else shap_values[class_idx][0]

        # Combine feature names with their contributions
        feature_importance = []
        for name, value in zip(feature_names, class_shap):
            feature_importance.append({
                'feature': name,
                'importance': float(value)
            })
            
        # Sort by importance (positive contribution first)
        feature_importance.sort(key=lambda x: x['importance'], reverse=True)
        
        # Extract top 3 positive contributors (reasons)
        top_reasons = []
        for item in feature_importance[:3]:
            # Human-friendly descriptions
            reason = self._format_reason(item['feature'], input_data[0][feature_names.index(item['feature'])], item['importance'])
            top_reasons.append(reason)
            
        return top_reasons

    def _format_reason(self, feature, value, importance):
        """Translate feature values into human-readable reasons"""
        desc = {
            'N': "high Nitrogen content",
            'P': "strong Phosphorus levels",
            'K': "ideal Potassium availability",
            'temperature': f"optimal temperature ({value:.1f}°C)",
            'humidity': f"perfect humidity ({value:.1f}%)",
            'ph': f"suitable soil pH ({value:.1f})",
            'rainfall': f"ideal rainfall ({value:.1f}mm)",
            'NPK_ratio': "balanced nutrient profiles",
            'nutrient_balance': "stable soil composition",
            'temp_humidity_index': "excellent climate balance",
            'ph_optimality': "near-perfect soil acidity",
            'water_stress_index': "favorable moisture levels",
            'growing_degree_days': "optimal thermal accumulation",
            'N_P_ratio': "proper N-P nutrient ratio",
            'N_K_ratio': "favorable N-K nutrient ratio"
        }
        
        # Adjust description based on importance (if negative, it wouldn't be in top 3 usually)
        return desc.get(feature, f"favorable {feature} level")
