import pytest
import os
from app import app
from schemas import CropInput
from models import db, User
from auth_utils import generate_token

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['BCRYPT_LOG_ROUNDS'] = 4  # Faster for testing
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

@pytest.fixture
def test_user(client):
    """Create a test user for authenticated requests"""
    with app.app_context():
        user = User(
            email='test@example.com',
            username='testuser'
        )
        user.set_password('TestPass123')
        db.session.add(user)
        db.session.commit()
        
        return {
            'id': user.id,
            'email': user.email,
            'username': user.username
        }

@pytest.fixture
def auth_headers(test_user):
    """Generate authentication headers for protected routes"""
    with app.app_context():
        token = generate_token(test_user['id'], test_user['email'])
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

def test_health_check(client):
    """Verify system heartbeat (public endpoint)"""
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'model_loaded' in data

def test_predict_invalid_json(client, auth_headers):
    """Verify error handling for malformed JSON"""
    response = client.post('/api/v1/predict', 
                          json={"invalid": "data"},
                          headers=auth_headers)
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'Validation Failed' in data['error']

def test_predict_out_of_bounds(client, auth_headers):
    """Verify domain-specific validation (Pydantic Field ge/le)"""
    # pH must be <= 10
    payload = {
        "N": 50, "P": 50, "K": 50, 
        "temperature": 25, "humidity": 70, 
        "ph": 11, "rainfall": 100
    }
    response = client.post('/api/v1/predict', 
                          json=payload,
                          headers=auth_headers)
    assert response.status_code == 400
    data = response.get_json()
    assert 'Validation Failed' in data['error']

def test_predict_without_auth(client):
    """Verify prediction endpoint requires authentication"""
    payload = {
        "N": 50, "P": 50, "K": 50, 
        "temperature": 25, "humidity": 70, 
        "ph": 6.5, "rainfall": 100
    }
    response = client.post('/api/v1/predict', json=payload)
    assert response.status_code == 401
    data = response.get_json()
    assert data['error'] == 'Authentication Required'

def test_history_endpoint(client, auth_headers):
    """Verify history retrieval (protected endpoint)"""
    response = client.get('/api/v1/history', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'data' in data

def test_history_without_auth(client):
    """Verify history endpoint requires authentication"""
    response = client.get('/api/v1/history')
    assert response.status_code == 401

def test_stats_endpoint(client, auth_headers):
    """Verify stats retrieval (protected endpoint)"""
    response = client.get('/api/v1/stats', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'total_predictions' in data

