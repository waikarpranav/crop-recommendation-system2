# 🌾 Smart Crop Recommendation System 2.0

Advanced AI-powered Decision Support System (DSS) for precision agriculture.

---

## 📖 Project Documentation

This repository contains a full-stack implementation of a Crop Recommendation System. For a deep dive into the architecture, security, and machine learning pipeline, please see the **[Professional Documentation Guide](file:///e:/PROJECTS/full%20stack%20project/DOCUMENTATION.md)**.

---

## 🚀 Quick Start

### 1. Backend Setup (Flask)
```bash
cd crop-recommendation-backend
python -m venv venv
# Windows: venv\Scripts\activate | Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### 2. Frontend Setup (Streamlit)
```bash
cd crop-recommendation-frontend
python -m venv venv
# Windows: venv\Scripts\activate | Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

---

## 🏗️ Technical Highlights

- **Multi-Algorithm Comparison**: Automated validation of RF, XGBoost, SVM, and more.
- **Explainable AI (XAI)**: SHAP-powered reasoning to explain *why* a crop was recommended.
- **Stateless Auth**: Secure JWT (JSON Web Token) access and refresh token strategy.
- **Domain Engineering**: Custom feature calculation (THI, GDD, NPK ratios).
- **Internationalization**: Full support for English, Hindi, and Marathi.

---

## 🛠️ Tech Stack
*   **Backend**: Flask, SQLAlchemy, Pydantic, PyJWT, Bcrypt
*   **Frontend**: Streamlit, Plotly, Multi-language Support
*   **Machine Learning**: Scikit-Learn, XGBoost, SHAP
*   **DevOps**: Render (Infrastructure-as-Code), GitHub Actions

---
*Built with ❤️ for Sustainable Agriculture.*
