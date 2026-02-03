import unittest
import json
import os
from app import app, db
from models import User

class BasicTests(unittest.TestCase):
    def setUp(self):
        """Setup a fresh test client and in-memory database for every test."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['BCRYPT_LOG_ROUNDS'] = 4
        self.client = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_1_health(self):
        """Verify API is alive and ML model is initialized."""
        response = self.client.get('/api/v1/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['model_loaded'])
        print("\nHealth & ML Status: PASSED")

    def test_2_registration(self):
        """Verify a new user can register successfully."""
        payload = {
            "email": "student@sinhgad.edu",
            "username": "sinhgad_student",
            "password": "SecurePassword123!"
        }
        response = self.client.post('/api/v1/auth/register', json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data.get('status'), 'success')
        print("User Registration: PASSED")

    def test_3_login(self):
        """Verify user can login and receive a valid JWT."""
        # 1. Register
        self.client.post('/api/v1/auth/register', json={
            "email": "test@test.com", "username": "tester", "password": "Password123!"
        })
        # 2. Login
        response = self.client.post('/api/v1/auth/login', json={
            "email": "tester", "password": "Password123!"
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('access_token', data)
        print("Login & JWT Issuance: PASSED")

    def test_4_prediction(self):
        """Verify an authenticated user can get a prediction."""
        # 1. Register & Login
        self.client.post('/api/v1/auth/register', json={
            "email": "farmer@example.com", "username": "farmer1", "password": "Password123!"
        })
        login_res = self.client.post('/api/v1/auth/login', json={
            "email": "farmer1", "password": "Password123!"
        })
        token_data = login_res.get_json()
        token = token_data['access_token']
        
        # 2. Predict
        payload = {
            "N": 90, "P": 40, "K": 40,
            "temperature": 25, "humidity": 80,
            "ph": 5, "rainfall": 200
        }
        headers = {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
        response = self.client.post('/api/v1/predict', json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertIn('predicted_crop', data)
        print("Authenticated Prediction Flow: PASSED")

if __name__ == '__main__':
    unittest.main()
