import pandas as pd
import numpy as np
import os
import json
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import RandomizedSearchCV, cross_validate, train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from feature_engineering import engineer_features

def run_maturity_upgrade():
    """Implement scientific rigor: Tuning, Validation, and Deep Metrics"""
    print("🚀 Starting ML Maturity Upgrade...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, 'Data', 'Crop_recommendation.csv')
    
    if not os.path.exists(data_path):
        print(f"❌ Error: Dataset not found at {data_path}")
        return

    # 1. Data Preparation
    df = pd.read_csv(data_path)
    X = df.drop('label', axis=1)
    y = df['label']
    X_engineered = engineer_features(X)
    
    # Split for final evaluation
    X_train, X_test, y_train, y_test = train_test_split(X_engineered, y, test_size=0.2, random_state=42)

    # 2. Hyperparameter Tuning (Random Forest)
    print("🧪 Tuning hyperparameters (RandomizedSearchCV)...")
    param_dist = {
        'n_estimators': [50, 100, 200],
        'max_depth': [10, 20, 30, None],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4]
    }
    
    # Using a subset for faster tuning in this environment if needed, but let's try full
    rf = RandomForestClassifier(random_state=42)
    random_search = RandomizedSearchCV(
        rf, param_distributions=param_dist, 
        n_iter=10, cv=3, random_state=42, n_jobs=-1
    )
    random_search.fit(X_train, y_train)
    
    best_model = random_search.best_estimator_
    print(f"✅ Best Parameters: {random_search.best_params_}")

    # 3. Proper Cross-Validation (Checking for overfitting)
    print("⚖️ Performing 5-Fold Cross-Validation...")
    cv_results = cross_validate(
        best_model, X_engineered, y, 
        cv=5, 
        return_train_score=True,
        scoring=['accuracy', 'precision_macro', 'recall_macro', 'f1_macro']
    )
    
    train_acc = cv_results['train_accuracy'].mean()
    test_acc = cv_results['test_accuracy'].mean()
    
    print(f"📈 Train Accuracy: {train_acc:.4f}")
    print(f"📈 Test Accuracy: {test_acc:.4f}")
    if (train_acc - test_acc) > 0.05:
        print("⚠️ Warning: Possible overfitting detected (gap > 5%)")

    # 4. Comprehensive Evaluation Metrics
    best_model.fit(X_train, y_train) # Re-fit on full train set for final metrics
    y_pred = best_model.predict(X_test)
    
    # Classification Report
    report = classification_report(y_test, y_pred, output_dict=True)
    
    # Confusion Matrix (Data for Plotly)
    cm = confusion_matrix(y_test, y_pred)
    classes = sorted(y.unique())
    
    # 5. Feature Importance Analysis
    importances = best_model.feature_importances_
    features = X_engineered.columns.to_list()
    feature_importance_data = sorted(
        [{"feature": f, "importance": float(i)} for f, i in zip(features, importances)],
        key=lambda x: x['importance'], reverse=True
    )

    # 6. Save Results
    results = {
        "best_params": random_search.best_params_,
        "cv_metrics": {
            "train_accuracy": float(train_acc),
            "test_accuracy": float(test_acc),
            "f1_score": float(cv_results['test_f1_macro'].mean())
        },
        "feature_importance": feature_importance_data,
        "confusion_matrix": {
            "values": cm.tolist(),
            "labels": classes
        },
        "classification_report": report
    }

    results_path = os.path.join(base_dir, 'ml_maturity_report.json')
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=4)
        
    # Save the optimized model
    ml_models_dir = os.path.join(base_dir, 'ml_models')
    model_path = os.path.join(ml_models_dir, 'crop_recommendation_model.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(best_model, f)

    print(f"🏁 Maturity Upgrade Complete! Report saved to {results_path}")
    return results

if __name__ == "__main__":
    run_maturity_upgrade()
