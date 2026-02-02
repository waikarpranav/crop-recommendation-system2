# 🌾 Smart Crop Recommendation System 2.0

Advanced AI-powered Decision Support System (DSS) for precision agriculture.

## 🚀 The Upgrade Journey: From Prototype to Production

This project evolved through a structured 7-tier upgrade process to reach professional industry standards.

### 🧬 Tier 1: Advanced Feature Engineering
*   **Domain Intelligence**: Added agricultural features like **NPK Ratio**, **Nutrient Balance**, and **Water Stress Index**.
*   **Climate Logic**: Implemented **Growing Degree Days (GDD)** and **Temperature-Humidity Index (THI)**.
*   **Impact**: Increased model precision by providing richer context for soil-climate interactions.

### 🔬 Tier 2: Model Comparison Pipeline
*   **Multi-Algorithm Testing**: Automated evaluation of **Random Forest, XGBoost, SVM, Naive Bayes, and Logistic Regression**.
*   **Systematic Selection**: The system mathematically identifies the top-performing algorithm using 5-fold cross-validation.

### 🔍 Tier 3: Explainability (SHAP) - The Trust Layer
*   **Transparent AI**: Integrated **SHAP (SHapley Additive exPlanations)** to provide top-3 reasons for every prediction.
*   **Performance Optimization**: Implemented **Lazy-Loading** to ensure high-memory AI libraries don't crash the server on limited hardware.

### ⚖️ Tier 4: Confidence & Alternatives
*   **Uncertainty Quantification**: Added **Confidence Percentage** badges (0-100%).
*   **Fallback Logic**: Provides up to 3 **Alternative Recommendations** if the primary match isn't perfect.
*   **Suitability Ranking**: Categorizes crops into High, Moderate, and Low suitability matches.

### 🛡️ Tier 5: Production-Ready API Design
*   **Architectural Rigor**: Implemented **UUID Request IDs** for enterprise-grade troubleshooting.
*   **Centralized Logging**: Real-time monitoring of API traffic, validation failures, and server health.
*   **Robust Validation**: Multi-error feedback loops with strict agricultural domain constraints.

### 📊 Tier 6: Scientific Maturity
*   **Hyperparameter Tuning**: Used **RandomizedSearchCV** to find mathematically optimal model settings.
*   **Advanced Analytics**: Deep insights into model performance through **Confusion Matrices** and **Feature Importance** distributions.
*   **Stability**: 5-fold cross-validation reporting to prevent overfitting and ensure generalization.

### 🏁 Tier 7: Production-Readiness Signals (Final Finish)
*   **API Versioning**: Standardized on `/api/v1/` for professional, future-proof releases.
*   **Health Heartbeat**: Implemented `/api/v1/health` for real-time monitoring of model loading and system health.
*   **Deep Data Capture**: The database now tracks every **Request ID** and **Confidence Score** for advanced auditing.
*   **Security & Sanitization**: Strict input cleaning to ensure system resilience and data integrity.

---

## 🛠️ Tech Stack
*   **Backend**: Flask (Python), PostgreSQL, SQLAlchemy
*   **Frontend**: Streamlit
*   **Machine Learning**: Scikit-Learn, XGBoost
*   **Explainability**: SHAP
*   **DevOps**: Render/Railway, Git, Professional Logging

## 🏃 Quick Start

### 1. Backend Setup
```bash
cd crop-recommendation-backend
pip install -r requirements.txt
python app.py
```

### 2. Frontend Setup
```bash
cd crop-recommendation-frontend
pip install -r requirements.txt
streamlit run app.py
```

## 🛠️ Developer Toolbox (Admin Commands)

Use these commands to maintain, retrain, or evaluate the system locally.

### 🧠 Model Management
| Task | Command | Description |
| :--- | :--- | :--- |
| **Retrain Model** | `python train_model.py` | Rebuilds the model and scaler from scratch. |
| **Deep Evaluation** | `python evaluate_model.py` | Generates the advanced maturity report & metrics. |
| **Algorithm Test** | `python model_comparison.py` | Compares RF, XGBoost, SVM, etc. |

### 🔍 System Maintenance
| Task | Command | Description |
| :--- | :--- | :--- |
| **Check Env** | `pip freeze` | Verify local library versions (NumPy, Scikit-learn). |
| **Reset DB** | `Remove-Item instance/predictions.db` | (Windows) Deletes local history for a fresh start. |
| **Git Push** | `git add . ; git commit -m "Update" ; git push` | Deploy local changes to live server. |

### 🏥 API Verification
| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/api/v1/health` | `GET` | Verify if model/scaler loaded correctly. |
| `/api/v1/predict` | `POST` | Test prediction with JSON payload. |

## ☁️ Cloud Deployment Guide

Follow these steps to host your system live on the web.

### 🔌 Backend (Render.com)
1. **New Web Service**: Connect your GitHub repository.
2. **Root Directory**: `crop-recommendation-backend`
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `gunicorn app:app`
5. **Environment Variables**:
   - `FLASK_ENV`: `production`
   - `DATABASE_URL`: Your PostgreSQL URL (Render provides this).
   - `PYTHON_VERSION`: `3.10.0` or higher.

### 🎨 Frontend (Streamlit Community Cloud)
1. **Deploy app**: Connect your GitHub repository.
2. **Main file path**: `crop-recommendation-frontend/app.py`
3. **Advanced Settings**:
   - Ensure the `API_BASE_URL` in your frontend matches your live Render URL.



## 📈 Model Insights
The system currently utilizes a **Tuned Random Forest** model achieving over **99% test accuracy**, validated by advanced confusion matrix analysis and cross-validation reports.

---
**Build with ❤️ for Sustainable Agriculture.**
