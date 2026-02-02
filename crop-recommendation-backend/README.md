# 🔧 Crop Recommendation API

The professional intelligence layer for the Smart Crop Recommendation System.

## ✨ Core Features
- **API Versioning**: Standardized `/api/v1/` routes for professional deployments.
- **Health Heartbeat**: Live `/api/v1/health` endpoint for system monitoring.
- **RESTful Endpoints**: Robust `/predict`, `/history`, and `/model-comparison`.
- **AI Explanations**: SHAP integration providing agricultural reasoning.
- **Production DevOps**: Centralized logging, UUID request tracking, and robust error handling.
- **Scientifically Optimized**: Tuned via RandomizedSearchCV with 5-fold cross-validation.

## 📁 Directory Structure
- `/Data`: Raw agricultural datasets.
- `/ml_models`: Trained `.pkl` artifacts (Model & Scaler).
- `app.py`: Main Flask application with request tracking.
- `explainability.py`: Lazy-loaded SHAP explainer logic.
- `utils.py`: Domain-specific multi-error validation logic.
- `evaluate_model.py`: Script for hyperparameter tuning and deep metrics evaluation.

## 🚀 Running
```bash
pip install -r requirements.txt
python app.py
```
