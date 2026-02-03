# 🌾 Crop Recommendation System (ML + Full Stack)

A professional, full-stack decision support system that recommends the most suitable crop based on soil chemistry and environmental parameters.  
Built with a **Flask API**, **Streamlit Frontend**, and **Random Forest (99% Acc)**, featuring enterprise-grade security and explainable AI.

---

## 🚀 Project Overview

Choosing the right crop is critical for maximizing yield and minimizing resource waste. This project bridges the gap between raw agricultural data and actionable intelligence using:
- **High-Precision ML**: Random Forest model tuned for 99% accuracy.
- **Security**: Robust JWT-based authentication (Access/Refresh strategy).
- **Explainability**: SHAP integration to tell farmers *why* a crop was recommended.
- **Scalability**: Decoupled frontend/backend architecture ready for cloud deployment.

---

## 🧠 System Architecture

```mermaid
graph LR
    User([Farmer]) --> UI[Streamlit Frontend]
    UI -->|JWT Auth| API[Flask REST API]
    API -->|Validation| Pydantic[Pydantic Schemas]
    Pydantic -->|Inference| ML[Random Forest + SHAP]
    ML -->|Audit| DB[(PostgreSQL)]
    API -->|JSON| UI
```

---

## 🛠️ Tech Stack

- **Machine Learning:** Scikit-learn (Random Forest), XGBoost, SHAP (Explainability)
- **Backend:** Flask, Flask-SQLAlchemy, PyJWT, Bcrypt, Pydantic
- **Frontend:** Streamlit, Plotly (Localized in English, Hindi, Marathi)
- **Database:** PostgreSQL (Cloud) / SQLite (Local)
- **Deployment:** Render (Infrastructure-as-Code), Gunicorn

---

## 📊 Machine Learning Pipeline

**Input Features:**
- Soil: Nitrogen (N), Phosphorus (P), Potassium (K), pH
- Climate: Temperature, Humidity, Rainfall
- **Engineered**: NPK Ratios, THI (Climate Stress), GDD (Heat Units)

**Pipeline:**
- Preprocessing: `StandardScaler` for feature normalization.
- Model: **Tuned Random Forest Classifier** (Cross-validated).
- Explainability: **SHAP** values providing the top-3 factors for every prediction.

---

## 🔐 Authentication & Security

- **Stateless Auth**: JWT-based tokens with distinct Access and Refresh lifecycles.
- **Data Protection**: Bcrypt password hashing and user-isolated history.
- **Schema Defense**: Strict Pydantic input validation to prevent malformed requests.
- **Audit Ready**: Request ID tracking for every API transaction.

---

## 📁 Project Structure

```bash
├── crop-recommendation-backend/   # Flask API Core
│   ├── app.py                     # Entry point & Routes
│   ├── auth_utils.py              # JWT & Security logic
│   ├── models.py                  # Database Schemas
│   ├── schemas.py                 # Pydantic Validation
│   └── ml_models/                 # Model Artifacts (.pkl)
├── crop-recommendation-frontend/  # Streamlit Dashboard
│   ├── app.py                     # UI logic & State mgmt
│   └── translations.py            # Multi-language support
├── render.yaml                    # Cloud Orchestration (IaC)
└── DOCUMENTATION.md               # Deep Technical Manual
```

---

## ▶️ Run Locally

```bash
# 1. Setup Backend
cd crop-recommendation-backend
pip install -r requirements.txt
python app.py

# 2. Setup Frontend
cd crop-recommendation-frontend
pip install -r requirements.txt
streamlit run app.py
```

---

## ☁️ Deployment

* **Architecture**: Hosted as two separate services (API + UI) on Render.
* **Orchestration**: Managed via `render.yaml` for one-click setup.
* **Security**: SSL/TLS encryption for all data in transit.

---

## 🧪 Learning & Engineering Standards

This project follows a **tiered upgrade path** to demonstrate senior-level maturity:
1. **Explainable AI**: Moving from "Black Box" to SHAP-powered transparency.
2. **Enterprise Security**: Implementing industry-standard JWT auth workflows.
3. **API Rigor**: Versioned endpoints, health checks, and standardized error responses.
4. **DevOps**: Infrastructure as Code and automated database migrations.

---

## 👨💻 Author

**Pranav Waikar**  
Engineering Student | Full-Stack & ML Specialist

---

⭐ If you find this project useful, feel free to star the repository!
