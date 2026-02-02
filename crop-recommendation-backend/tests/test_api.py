import pytest
import os
from app import app
from schemas import CropInput

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            from models import db
            db.create_all()
        yield client

def test_health_check(client):
    """Verify system heartbeat"""
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'model_loaded' in data

def test_predict_invalid_json(client):
    """Verify error handling for malformed JSON"""
    response = client.post('/api/v1/predict', json={"invalid": "data"})
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'Validation Failed' in data['error']

def test_predict_out_of_bounds(client):
    """Verify domain-specific validation (Pydantic Field ge/le)"""
    # pH must be <= 10
    payload = {
        "N": 50, "P": 50, "K": 50, 
        "temperature": 25, "humidity": 70, 
        "ph": 11, "rainfall": 100
    }
    response = client.post('/api/v1/predict', json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert 'Validation Failed' in data['error']

def test_history_endpoint(client):
    """Verify history retrieval"""
    response = client.get('/api/v1/history')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'data' in data
