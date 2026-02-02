from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, StratifiedKFold
import pandas as pd
import json
import os

def compare_models(csv_path):
    """
    Loads dataset, trains multiple models using cross-validation, 
    and returns a summary of results.
    """
    if not os.path.exists(csv_path):
        return {"error": f"Dataset not found at {csv_path}"}

    # Load data
    df = pd.read_csv(csv_path)
    X = df.drop('label', axis=1)
    y = df['label']

    # Define models
    models = {
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
        'XGBoost': XGBClassifier(n_estimators=100, random_state=42, eval_metric='mlogloss'),
        'SVM': SVC(kernel='rbf', random_state=42),
        'Naive Bayes': GaussianNB(),
        'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42)
    }

    results = {}
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    for name, model in models.items():
        print(f"Evaluating {name}...")
        try:
            # XGBoost needs label encoding for y if it's categorical
            if name == 'XGBoost':
                from sklearn.preprocessing import LabelEncoder
                le = LabelEncoder()
                y_encoded = le.fit_transform(y)
                scores = cross_val_score(model, X, y_encoded, cv=cv, scoring='accuracy')
            else:
                scores = cross_val_score(model, X, y, cv=cv, scoring='accuracy')
            
            results[name] = {
                'mean_accuracy': float(scores.mean()),
                'std_accuracy': float(scores.std()),
                'scores': scores.tolist()
            }
        except Exception as e:
            results[name] = {"error": str(e)}

    # Save comparison results
    results_path = os.path.join(os.path.dirname(csv_path), '..', 'model_comparison_results.json')
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)

    return results

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, 'Data', 'Crop_recommendation.csv')
    print("Running comparison...")
    comparison_results = compare_models(data_path)
    print("Results saved to model_comparison_results.json")
