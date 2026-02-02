import requests
import streamlit as st

def call_prediction_api(url, payload):
    """Call the prediction API endpoint"""
    try:
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
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

def get_history(base_url, limit=10):
    """Fetch prediction history from API"""
    try:
        response = requests.get(
            f"{base_url}/history?limit={limit}",
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    except Exception as e:
        st.error(f"Error fetching history: {str(e)}")
        return None

def get_stats(base_url):
    """Fetch statistics from API"""
    try:
        response = requests.get(
            f"{base_url}/stats",
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    except Exception as e:
        st.error(f"Error fetching stats: {str(e)}")
        return None