from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from typing import Dict, Any, Optional

db = SQLAlchemy()


class User(db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Metadata
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationship to predictions
    predictions = db.relationship('Prediction', backref='user', lazy=True)
    
    def set_password(self, password: str) -> None:
        """Hash and set password"""
        from auth_utils import hash_password
        self.password_hash = hash_password(password)
    
    def check_password(self, password: str) -> bool:
        """Verify password against hash"""
        from auth_utils import verify_password
        return verify_password(password, self.password_hash)
    
    def update_last_login(self) -> None:
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
    
    def to_dict(self, include_predictions: bool = False) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active
        }
        
        if include_predictions:
            data['predictions_count'] = len(self.predictions)
        
        return data
    
    def __repr__(self) -> str:
        return f'<User {self.username} ({self.email})>'

class Prediction(db.Model):
    """Store crop predictions"""
    __tablename__ = 'predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # User association (nullable for backward compatibility)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    
    # Input features
    nitrogen = db.Column(db.Float, nullable=False)
    phosphorus = db.Column(db.Float, nullable=False)
    potassium = db.Column(db.Float, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    ph = db.Column(db.Float, nullable=False)
    rainfall = db.Column(db.Float, nullable=False)
    
    # Output
    predicted_crop = db.Column(db.String(50), nullable=False)
    
    # Metadata
    request_id = db.Column(db.String(36), nullable=True)
    confidence = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self, include_user: bool = False) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = {
            'id': self.id,
            'nitrogen': self.nitrogen,
            'phosphorus': self.phosphorus,
            'potassium': self.potassium,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'ph': self.ph,
            'rainfall': self.rainfall,
            'predicted_crop': self.predicted_crop,
            'confidence': self.confidence,
            'request_id': self.request_id,
            'created_at': self.created_at.isoformat()
        }
        
        if include_user and self.user:
            data['user'] = {
                'id': self.user.id,
                'username': self.user.username,
                'email': self.user.email
            }
        
        return data
    
    def __repr__(self):
        return f'<Prediction {self.id}: {self.predicted_crop}>'