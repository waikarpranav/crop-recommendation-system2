# 🔧 Crop Recommendation API

The professional intelligence layer for the Smart Crop Recommendation System.

## ✨ Core Features
- **JWT Authentication**: Full user lifecycle management (Register, Login, Refresh, Logout).
- **Secure Password Hashing**: Implemented using **Bcrypt**.
- **Pydantic Validation**: Strict schema enforcement for all incoming and outgoing data.
- **Explainable AI (XAI)**: SHAP integration providing agricultural reasoning.
- **Production DevOps**: Centralized logging, UUID request tracking, and robust error handling.
- **Scientifically Optimized**: Tuned via RandomizedSearchCV with 5-fold cross-validation.

## 📁 Directory Structure
- `/Data`: Raw agricultural datasets.
- `/ml_models`: Trained `.pkl` artifacts (Model & Scaler).
- `app.py`: Main Flask application with JWT-protected routes.
- `auth_utils.py`: JWT token generation, verification, and rotation logic.
- `models.py`: SQLAlchemy database models (User, Prediction).
- `schemas.py`: Pydantic models for request/response validation.
- `explainability.py`: Lazy-loaded SHAP explainer logic.
- `evaluate_model.py`: Script for hyperparameter tuning and deep metrics evaluation.

## 🚀 API Endpoints

### 🔐 Auth (Public)
- `POST /api/v1/auth/register`: Create a new user.
- `POST /api/v1/auth/login`: Authenticate and receive tokens.

### 🌾 Agriculture (Protected)
- `POST /api/v1/predict`: Get crop recommendations (+ reasons).
- `GET /api/v1/history`: View personal prediction history.
- `GET /api/v1/stats`: View personal usage statistics.

## 🏃 Running locally
```bash
python -m venv venv
# venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
