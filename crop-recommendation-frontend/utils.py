import requests
import streamlit as st

def call_prediction_api(url, payload, token=None):
    """Call the prediction API endpoint"""
    try:
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f"Bearer {token}"
            
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            return response.json()
        elif response.status_code == 401:
            st.warning("🔑 Session expired or unauthorized. Please login again.")
            return {"status": "error", "error": "Unauthorized"}
        else:
            st.error(f"API Error: {response.status_code}")
            try:
                return response.json()
            except:
                return {"status": "error", "error": f"HTTP {response.status_code}"}
    
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API. Make sure Flask backend is running!")
        return None
    except requests.exceptions.Timeout:
        st.error("❌ API request timed out")
        return None
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None

def get_history(base_url, token, limit=10):
    """Fetch prediction history from API"""
    try:
        headers = {}
        if token:
            headers['Authorization'] = f"Bearer {token}"
            
        response = requests.get(
            f"{base_url}/api/v1/history?limit={limit}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    
    except Exception as e:
        st.error(f"Error fetching history: {str(e)}")
        return None

def get_stats(base_url, token):
    """Fetch statistics from API"""
    try:
        headers = {}
        if token:
            headers['Authorization'] = f"Bearer {token}"
            
        response = requests.get(
            f"{base_url}/api/v1/stats",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    
    except Exception as e:
        st.error(f"Error fetching stats: {str(e)}")
        return None

def login_user(base_url, email, password):
    """Authenticate user"""
    try:
        response = requests.post(
            f"{base_url}/api/v1/auth/login",
            json={"email": email, "password": password},
            timeout=10
        )
        return response.status_code, response.json()
    except Exception as e:
        return 500, {"error": str(e)}

def register_user(base_url, email, username, password):
    """Register new user"""
    try:
        response = requests.post(
            f"{base_url}/api/v1/auth/register",
            json={"email": email, "username": username, "password": password},
            timeout=10
        )
        return response.status_code, response.json()
    except Exception as e:
        return 500, {"error": str(e)}

def get_model_comparison(base_url):
    # (Remains public for now as in backend)
    try:
        response = requests.get(f"{base_url}/api/v1/model-comparison", timeout=30)
        return response.json() if response.status_code == 200 else None
    except: return None

def get_ml_maturity_report(base_url):
    # (Remains public for now as in backend)
    try:
        response = requests.get(f"{base_url}/api/v1/ml-maturity-report", timeout=120)
        return response.json() if response.status_code == 200 else None
    except: return None