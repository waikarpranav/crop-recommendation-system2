# Deployment Guide

This guide will walk you through deploying your Crop Recommendation System.

## Use Case 1: Deploying Backend to Render
Render is a great platform for hosting Python web services.

1.  **Sign Up/Log In**: Go to [render.com](https://render.com) and create an account.
2.  **New Web Service**: Click "New +" and select "Web Service".
3.  **Connect Repository**: Connect your GitHub account and select your repository (`waikarpranav/crop-recommendation-system2`).
4.  **Configure Service**:
    *   **Name**: `crop-recommendation-backend` (or similar)
    *   **Root Directory**: `crop-recommendation-backend` (Important!)
    *   **Runtime**: `Python 3`
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `gunicorn app:app` (This uses the Procfile we verified)
5.  **Environment Variables**:
    *   Add `FLASK_ENV` with value `production`.
6.  **Create Web Service**: Click the button to create. Render will build and deploy your backend.
7.  **Copy URL**: Once deployed, copy the URL (e.g., `https://crop-backend.onrender.com`). You will need this for the frontend.

## Use Case 2: Deploying Frontend to Streamlit Cloud
Streamlit Cloud is the easiest way to host Streamlit apps.

1.  **Sign Up/Log In**: Go to [streamlit.io/cloud](https://streamlit.io/cloud) and sign up with GitHub.
2.  **New App**: Click "New app".
3.  **Select Repository**: Choose your repository (`waikarpranav/crop-recommendation-system2`).
4.  **Configure App**:
    *   **Main file path**: `crop-recommendation-frontend/app.py`
5.  **Advanced Settings** (Crucial):
    *   Click "Advanced settings..."
    *   **Environment Variables**:
        *   Key: `API_URL`
        *   Value: `https://your-backend-url.onrender.com` (Paste the Render URL from Step 1)
6.  **Deploy**: Click "Deploy!".

---

## Alternative: Deploying Frontend to Render
If you prefer to keep everything on Render:

1.  **New Web Service**: Select "Web Service" on Render.
2.  **Connect Repository**: Select same repo.
3.  **Configure**:
    *   **Name**: `crop-recommendation-frontend`
    *   **Root Directory**: `crop-recommendation-frontend`
    *   **Runtime**: `Python 3`
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0` (Or just let it use the Procfile we created).
4.  **Environment Variables**:
    *   Key: `API_URL`
    *   Value: `https://your-backend-url.onrender.com`
    *   Key: `PYTHON_VERSION`
    *   Value: `3.9.0` (Optional, if you face version issues)
5.  **Create Web Service**.
