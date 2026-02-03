"""
Tests for authentication endpoints and JWT functionality.
"""

import pytest
import json
from app import app, db
from models import User, Prediction
from auth_utils import generate_token, verify_token, hash_password


@pytest.fixture
def client():
    """Create test client"""
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
    """Create a test user"""
    with app.app_context():
        user = User(
            email='test@example.com',
            username='testuser'
        )
        user.set_password('TestPass123')
        db.session.add(user)
        db.session.commit()
        
        # Return user data
        return {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'password': 'TestPass123'
        }


@pytest.fixture
def auth_headers(test_user):
    """Generate authentication headers"""
    with app.app_context():
        token = generate_token(test_user['id'], test_user['email'])
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }


# -------------------- REGISTRATION TESTS --------------------

def test_register_success(client):
    """Test successful user registration"""
    response = client.post('/api/v1/auth/register', json={
        'email': 'newuser@example.com',
        'username': 'newuser',
        'password': 'SecurePass123'
    })
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'access_token' in data
    assert 'refresh_token' in data
    assert data['user']['email'] == 'newuser@example.com'
    assert data['user']['username'] == 'newuser'


def test_register_duplicate_email(client, test_user):
    """Test registration with duplicate email"""
    response = client.post('/api/v1/auth/register', json={
        'email': test_user['email'],
        'username': 'differentuser',
        'password': 'SecurePass123'
    })
    
    assert response.status_code == 409
    data = json.loads(response.data)
    assert data['error'] == 'Email Already Registered'


def test_register_duplicate_username(client, test_user):
    """Test registration with duplicate username"""
    response = client.post('/api/v1/auth/register', json={
        'email': 'different@example.com',
        'username': test_user['username'],
        'password': 'SecurePass123'
    })
    
    assert response.status_code == 409
    data = json.loads(response.data)
    assert data['error'] == 'Username Already Taken'


def test_register_weak_password(client):
    """Test registration with weak password"""
    response = client.post('/api/v1/auth/register', json={
        'email': 'weak@example.com',
        'username': 'weakuser',
        'password': 'weak'
    })
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == 'Validation Failed'


def test_register_invalid_email(client):
    """Test registration with invalid email"""
    response = client.post('/api/v1/auth/register', json={
        'email': 'not-an-email',
        'username': 'testuser',
        'password': 'SecurePass123'
    })
    
    assert response.status_code == 400


def test_register_invalid_username(client):
    """Test registration with invalid username (special chars)"""
    response = client.post('/api/v1/auth/register', json={
        'email': 'test@example.com',
        'username': 'test@user!',
        'password': 'SecurePass123'
    })
    
    assert response.status_code == 400


# -------------------- LOGIN TESTS --------------------

def test_login_success(client, test_user):
    """Test successful login"""
    response = client.post('/api/v1/auth/login', json={
        'email': test_user['email'],
        'password': test_user['password']
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'access_token' in data
    assert 'refresh_token' in data
    assert data['user']['email'] == test_user['email']


def test_login_with_username(client, test_user):
    """Test login using username instead of email"""
    response = client.post('/api/v1/auth/login', json={
        'email': test_user['username'],  # Using username in email field
        'password': test_user['password']
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'


def test_login_wrong_password(client, test_user):
    """Test login with wrong password"""
    response = client.post('/api/v1/auth/login', json={
        'email': test_user['email'],
        'password': 'WrongPassword123'
    })
    
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data['error'] == 'Invalid Credentials'


def test_login_nonexistent_user(client):
    """Test login with non-existent user"""
    response = client.post('/api/v1/auth/login', json={
        'email': 'nonexistent@example.com',
        'password': 'SomePassword123'
    })
    
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data['error'] == 'Invalid Credentials'


# -------------------- TOKEN TESTS --------------------

def test_get_current_user(client, test_user, auth_headers):
    """Test getting current user profile"""
    response = client.get('/api/v1/auth/me', headers=auth_headers)
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['user']['email'] == test_user['email']
    assert data['user']['username'] == test_user['username']


def test_get_current_user_no_token(client):
    """Test getting current user without token"""
    response = client.get('/api/v1/auth/me')
    
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data['error'] == 'Authentication Required'


def test_get_current_user_invalid_token(client):
    """Test getting current user with invalid token"""
    headers = {
        'Authorization': 'Bearer invalid_token_here',
        'Content-Type': 'application/json'
    }
    response = client.get('/api/v1/auth/me', headers=headers)
    
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data['error'] == 'Invalid Token'


def test_refresh_token(client, test_user):
    """Test token refresh"""
    with app.app_context():
        from auth_utils import generate_refresh_token
        refresh_token = generate_refresh_token(test_user['id'], test_user['email'])
    
    response = client.post('/api/v1/auth/refresh', json={
        'refresh_token': refresh_token
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'access_token' in data


def test_refresh_token_invalid(client):
    """Test token refresh with invalid token"""
    response = client.post('/api/v1/auth/refresh', json={
        'refresh_token': 'invalid_refresh_token'
    })
    
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data['error'] == 'Invalid Refresh Token'


# -------------------- PROTECTED ROUTE TESTS --------------------

def test_predict_with_auth(client, test_user, auth_headers):
    """Test prediction endpoint with authentication"""
    prediction_data = {
        'N': 90,
        'P': 42,
        'K': 43,
        'temperature': 20.8,
        'humidity': 82,
        'ph': 6.5,
        'rainfall': 202.9
    }
    
    response = client.post('/api/v1/predict', 
                          json=prediction_data,
                          headers=auth_headers)
    
    # May return 500 if model not loaded in test environment
    # But should not return 401 (authentication error)
    assert response.status_code != 401


def test_predict_without_auth(client):
    """Test prediction endpoint without authentication"""
    prediction_data = {
        'N': 90,
        'P': 42,
        'K': 43,
        'temperature': 20.8,
        'humidity': 82,
        'ph': 6.5,
        'rainfall': 202.9
    }
    
    response = client.post('/api/v1/predict', json=prediction_data)
    
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data['error'] == 'Authentication Required'


def test_history_with_auth(client, test_user, auth_headers):
    """Test history endpoint with authentication"""
    response = client.get('/api/v1/history', headers=auth_headers)
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'data' in data


def test_history_without_auth(client):
    """Test history endpoint without authentication"""
    response = client.get('/api/v1/history')
    
    assert response.status_code == 401


def test_stats_with_auth(client, test_user, auth_headers):
    """Test stats endpoint with authentication"""
    response = client.get('/api/v1/stats', headers=auth_headers)
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'total_predictions' in data


def test_stats_without_auth(client):
    """Test stats endpoint without authentication"""
    response = client.get('/api/v1/stats')
    
    assert response.status_code == 401


# -------------------- PASSWORD UTILITY TESTS --------------------

def test_password_hashing():
    """Test password hashing and verification"""
    with app.app_context():
        password = 'TestPassword123'
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        
        from auth_utils import verify_password
        assert verify_password(password, hashed) is True
        assert verify_password('WrongPassword', hashed) is False


def test_token_generation_and_verification():
    """Test JWT token generation and verification"""
    with app.app_context():
        user_id = 1
        email = 'test@example.com'
        
        # Generate token
        token = generate_token(user_id, email)
        assert token is not None
        assert len(token) > 0
        
        # Verify token
        payload = verify_token(token)
        assert payload is not None
        assert payload['user_id'] == user_id
        assert payload['email'] == email
        assert payload['type'] == 'access'


def test_user_model_password_methods():
    """Test User model password methods"""
    with app.app_context():
        user = User(
            email='test@example.com',
            username='testuser'
        )
        
        password = 'SecurePass123'
        user.set_password(password)
        
        assert user.password_hash is not None
        assert user.password_hash != password
        assert user.check_password(password) is True
        assert user.check_password('WrongPassword') is False
