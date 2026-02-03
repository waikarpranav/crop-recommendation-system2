"""
Authentication utilities for JWT token management and password hashing.
Implements enterprise-grade security with bcrypt and JWT.
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from typing import Dict, Any, Optional, Callable, Tuple
import logging

logger = logging.getLogger(__name__)


# -------------------- PASSWORD HASHING --------------------

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password as string
    """
    rounds = current_app.config.get('BCRYPT_LOG_ROUNDS', 12)
    salt = bcrypt.gensalt(rounds=rounds)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


# -------------------- JWT TOKEN MANAGEMENT --------------------

def generate_token(user_id: int, email: str, token_type: str = 'access') -> str:
    """
    Generate a JWT token for a user.
    
    Args:
        user_id: User's database ID
        email: User's email address
        token_type: 'access' or 'refresh'
        
    Returns:
        Encoded JWT token
    """
    if token_type == 'access':
        expires_delta = current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600)
    else:
        expires_delta = current_app.config.get('JWT_REFRESH_TOKEN_EXPIRES', 604800)
    
    payload = {
        'user_id': user_id,
        'email': email,
        'type': token_type,
        'exp': datetime.utcnow() + timedelta(seconds=expires_delta),
        'iat': datetime.utcnow()
    }
    
    secret_key = current_app.config.get('JWT_SECRET_KEY')
    algorithm = current_app.config.get('JWT_ALGORITHM', 'HS256')
    
    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    return token


def generate_refresh_token(user_id: int, email: str) -> str:
    """
    Generate a refresh token for a user.
    
    Args:
        user_id: User's database ID
        email: User's email address
        
    Returns:
        Encoded JWT refresh token
    """
    return generate_token(user_id, email, token_type='refresh')


def verify_token(token: str, token_type: str = 'access') -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token to verify
        token_type: Expected token type ('access' or 'refresh')
        
    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        secret_key = current_app.config.get('JWT_SECRET_KEY')
        algorithm = current_app.config.get('JWT_ALGORITHM', 'HS256')
        
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        
        # Verify token type
        if payload.get('type') != token_type:
            logger.warning(f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
            return None
            
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None


def extract_token_from_header() -> Optional[str]:
    """
    Extract JWT token from Authorization header.
    
    Returns:
        Token string if found, None otherwise
    """
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return None
    
    # Expected format: "Bearer <token>"
    parts = auth_header.split()
    
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    return parts[1]


# -------------------- DECORATORS --------------------

def token_required(f: Callable) -> Callable:
    """
    Decorator to protect routes that require authentication.
    
    Usage:
        @app.route('/protected')
        @token_required
        def protected_route(current_user):
            return jsonify({'message': f'Hello {current_user["email"]}'})
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = extract_token_from_header()
        
        if not token:
            return jsonify({
                'status': 'error',
                'error': 'Authentication Required',
                'message': 'No token provided. Please include Authorization header.'
            }), 401
        
        payload = verify_token(token, token_type='access')
        
        if not payload:
            return jsonify({
                'status': 'error',
                'error': 'Invalid Token',
                'message': 'Token is invalid or expired. Please login again.'
            }), 401
        
        # Pass user info to the route
        return f(current_user=payload, *args, **kwargs)
    
    return decorated


def optional_token(f: Callable) -> Callable:
    """
    Decorator for routes that work with or without authentication.
    If token is present and valid, user info is passed; otherwise None.
    
    Usage:
        @app.route('/optional')
        @optional_token
        def optional_route(current_user):
            if current_user:
                return jsonify({'message': f'Hello {current_user["email"]}'})
            return jsonify({'message': 'Hello guest'})
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = extract_token_from_header()
        current_user = None
        
        if token:
            payload = verify_token(token, token_type='access')
            if payload:
                current_user = payload
        
        return f(current_user=current_user, *args, **kwargs)
    
    return decorated


# -------------------- UTILITY FUNCTIONS --------------------

def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    # Optional: Check for special characters
    # special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    # if not any(c in special_chars for c in password):
    #     return False, "Password must contain at least one special character"
    
    return True, None
