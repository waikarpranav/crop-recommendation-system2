# 🌾 Smart Crop Recommendation System 2.0: Full-Stack Documentation

**Version:** 2.0.0  
**Architect:** Senior Engineering Team  
**Tech Stack:** Flask, Streamlit, PostgreSQL, Scikit-Learn, SHAP, JWT  

---

## 1. Project Overview

### Problem Statement
Agricultural productivity is often hindered by traditional "trial and error" farming. Farmers frequently plant crops based on historic precedent rather than real-time soil chemistry and climate data, leading to suboptimal yields, resource wastage, and financial instability.

### Why This Project Exists
This project serves as a **Decision Support System (DSS)**. It bridges the gap between raw agricultural data and actionable intelligence. By leveraging Machine Learning, it provides high-precision crop recommendations tailored to specific soil types and environmental conditions.

### Real-World Use Cases
- **Precision Farming**: Optimizing NPK (Nitrogen, Phosphorus, Potassium) application.
- **Climate Resilience**: Adapting crop selection to changing rainfall and temperature patterns.
- **Resource Management**: Reducing water stress by choosing crops suited for available humidity and rainfall.

### High-Level Architecture
The system follows a decoupled **Client-Server Architecture**:
- **Frontend (Streamlit)**: A multi-language interactive dashboard for data entry and visualization.
- **Backend (Flask)**: A RESTful API that handles authentication, ML inference, and data persistence.
- **ML Engine**: A tuned Random Forest pipeline with custom feature engineering and SHAP explainability.
- **Auth Layer**: Stateless JWT-based security with bcrypt hashing.
- **Database**: PostgreSQL (Production) / SQLite (Dev) for tracking historical predictions.

---

## 2. System Architecture

### Component Communication
The system utilizes **RESTful Communication**. The Frontend (Streamlit) acts as a consumer of the Backend (Flask) services. All communication occurs over HTTPS (in production) using JSON payloads.

### Data Flow Diagram (Textual)
1. **Input**: User enters 7 soil/climate parameters via Streamlit.
2. **Auth**: Frontend attaches a JWT Bearer token to the Request Header.
3. **Gateway**: Backend validates the token and sanitizes the JSON payload using Pydantic.
4. **Engineering**: Raw data is transformed into 15 features (e.g., NPK ratios, THI).
5. **Inference**: The ML model predicts the crop and calculates confidence probabilities.
6. **Explainability**: SHAP calculates the "why" behind the prediction.
7. **Persistence**: The result, request ID, and user ID are saved to the Database.
8. **Response**: A structured JSON object returns the result to the UI.

### Request–Response Lifecycle
- **Stage 1**: Client Request (POST /api/v1/predict).
- **Stage 2**: Middleware (JWT Verification & Rate Limiting).
- **Stage 3**: Controller (Schema validation & ML preprocessing).
- **Stage 4**: Service Layer (Model prediction & Database commit).
- **Stage 5**: Client Update (State management update & UI rendering).

---

## 3. Folder & File Structure

### Root Directory
- `README.md`: High-level project summary.
- `render.yaml`: Infrastructure as Code (IaC) for one-click cloud deployment.
- `DOCUMENTATION.md`: (This file) Comprehensive technical manual.

### `/crop-recommendation-backend` (Core API)
- `app.py`: **Core**. The entry point. Manages routing, startup logic, and error boundaries. *Breaks the whole system if removed.*
- `auth_utils.py`: **Core Security**. Handles JWT generation, verification, and password hashing. *Breaks authentication if removed.*
- `config.py`: **Core**. Centralized environment variable management. *System fails to connect to DB/ML files if removed.*
- `models.py`: **Core**. Defines the Database Schema (User, Prediction). *Persistence fails if removed.*
- `schemas.py`: **Core**. Pydantic models for request/response validation. *API becomes brittle/insecure if removed.*
- `utils.py`: **Helper**. ML loading and input preparation logic.
- `ml_models/`: **Optional/Auto-generated**. Stores `.pkl` artifacts. *Triggers auto-retrain if missing.*
- `instance/`: **Optional**. Local SQLite database storage.

### `/crop-recommendation-frontend` (UI Layer)
- `app.py`: **Core UI**. Streamlit application logic and page routing.
- `translations.py`: **Feature**. Dictionary-based localization for Multi-language support.
- `utils.py`: **Helper**. Network logic for calling Backend APIs.

---

## 4. Backend Documentation (Flask)

### Startup Flow
1. `app.py` initializes the Flask instance.
2. Loads environment-specific config from `config.py` (Dev vs. Prod).
3. Connects to the Database via SQLAlchemy.
4. **ML Integrity Check**: Attempts to load the `.pkl` model. If missing or library versions mismatch, it triggers an **Emergency Auto-Retrain** via `train_model.py`.
5. Initializes the SHAP explainer with the background dataset.

### Auth System (JWT)
The system uses a **Dual-Token Strategy**:
- **Access Tokens**: Short-lived (1 hour) for daily API interaction.
- **Refresh Tokens**: Long-lived (7 days) to maintain sessions without re-login.

### Error Handling
- **401 Unauthorized**: Missing/expired token.
- **400 Bad Request**: Pydantic validation failure (e.g., Nitrogen < 0).
- **409 Conflict**: Duplicate registration (Email/Username).
- **500 Server Error**: ML integrity failure or DB connection loss.

---

## 5. Authentication & Security

### Security Decisions
- **Bcrypt**: Used for one-way password hashing with salt. Raw passwords are never stored.
- **Statelessness**: JWTs allow the backend to remain stateless, aiding horizontal scaling.
- **Schema Defense**: Pydantic ensures only clean, typed data reaches the ML model.

### Token Payload
```json
{
  "user_id": 1,
  "email": "user@example.com",
  "type": "access",
  "exp": 1700000000,
  "iat": 1699900000
}
```

### Limitations
- **Token Blacklisting**: Currently lacks a logout-blacklist (tokens are valid until expiry).
- **Improvement**: Implement Redis for real-time token revocation.

---

## 6. Machine Learning Pipeline

### Dataset
The system uses the standard Agricultural Crop Recommendation Dataset containing thousands of samples for 22 unique crops.

### Feature Engineering (`feature_engineering.py`)
Moving beyond raw inputs, the system calculates:
- **NPK Ratios**: Identifying nutrient balance.
- **THI (Temperature-Humidity Index)**: Measuring climate stress.
- **GDD (Growing Degree Days)**: Evaluating heat accumulation for crop growth.

### Model Selection
- **Algorithm**: Tuned **Random Forest Classifier**.
- **Rationale**: Best handles non-linear relationships in agricultural data and provides high "Out-of-Bag" (OOB) accuracy.
- **Evaluation**: Achieved >99% accuracy across 5-fold cross-validation.

---

## 7. Database & Storage

### Storage (PostgreSQL/SQLite)
- **User Table**: ID, Email, Username, PasswordHash, Timestamps.
- **Prediction Table**: ID, UserID (FK), Input Features (N, P, K...), PredictedCrop, Confidence, RequestID.

### Resilience
If the database is unavailable, the system still provides real-time predictions but fails to log the history. A `db.session.rollback()` ensures data integrity in case of partial failures.

---

## 8. Frontend (Streamlit)

### UI/UX Design
- **Multi-language**: Built-in support for English, Hindi, and Marathi.
- **Trust Dashboard**: Specifically designed to show SHAP reasons and confidence bars to non-technical users (farmers).
- **State Management**: Uses `st.session_state` to track the JWT token across pages.

### API Integration
Communication is handled by `requests` in a centralized `utils.py` to ensure consistent error handling across all pages.

---

## 9. Testing

### Structure
- `tests/test_auth.py`: Validates registration, login, and token expiry.
- `tests/test_predict.py`: Validates model inference and Pydantic constraints.

### Execution
```bash
cd crop-recommendation-backend
pytest tests/ -v
```

---

## 10. Deployment

### Environment Config
Essential `.env` variables:
- `DATABASE_URL`: Cloud DB connection string.
- `JWT_SECRET_KEY`: High-entropy secret for token signing.
- `FLASK_ENV`: Set to `production` to disable debug mode.

### Cloud Flow (Render)
The `render.yaml` blueprint automates:
1. Provisioning a Python Web Service for the Backend.
2. Provisioning a Python Web Service for the Frontend.
3. Automatically linking the Backend URL to the Frontend environment.

---

## 11. Debugging Guide

| Error | Likely Cause | Solution |
| :--- | :--- | :--- |
| `AttributeError: 'tuple' object...` | ML Library Version Mismatch | Delete `ml_models/*.pkl` and restart server to trigger re-train. |
| `401 Unauthorized` | Expired Token | Clear browser session and log in again. |
| `PostgreSQL Connection Error` | SSL Mode Mismatch | Append `?sslmode=require` to your `DATABASE_URL`. |

---

## 12. Evaluation & Interview Section

### The "2-Minute" Pitch
"This is an AI-powered Decision Support System for agriculture. It's a full-stack Flask/Streamlit application that takes soil and climate data to recommend optimal crops. Unlike simple prototypes, this system implements professional standards like JWT authentication, Pydantic validation, and Explainable AI (SHAP) to tell users *why* a specific crop was chosen. It's fully deployable via Render using infrastructure-as-code."

### Typical Evaluation Questions
- **Q: Why Random Forest?**  
  *A: Agriculture data is multi-modal and non-linear. Random Forest handles these complexities better than linear models and offers feature importance for explainability.*
- **Q: How do you handle security?**  
  *A: We use JWTs for stateless auth and Bcrypt for password hashing. We also use Pydantic on the backend to prevent injection or malformed data from reaching the core logic.*

### Strengths & Weaknesses
- **Strength**: High scientific maturity (XAI, model comparison, cross-validation).
- **Weakness**: History is currently text-based; could be improved with time-series charts for nutrient trends over time.

---

## 13. How to Extend

- **Improve ML**: Add time-series forecasting for rainfall using LSTM.
- **UI Scaling**: Migrate from Streamlit to React (Next.js) for more complex user interactions.
- **Production Hardening**: Add Redis for rate limiting and token blacklisting.

---
**Documentation generated on:** 2026-02-04
