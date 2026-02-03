import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Get base directory
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # ML Model paths
    MODEL_PATH = os.environ.get('MODEL_PATH', os.path.join(BASE_DIR, 'ml_models', 'crop_recommendation_model.pkl'))
    SCALER_PATH = os.environ.get('SCALER_PATH', os.path.join(BASE_DIR, 'ml_models', 'scaler.pkl'))

    # Signals for Production-Readiness
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    MAX_REQUESTS_PER_MINUTE = int(os.environ.get('RATE_LIMIT', 100))
    ENABLE_EXPLAINABILITY = os.environ.get('ENABLE_SHAP', 'True').lower() == 'true'
    
    # JWT Authentication Settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ALGORITHM = 'HS256'
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 3600))  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', 604800))  # 7 days

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DEV_DATABASE_URL', 
        f'sqlite:///{os.path.join(Config.BASE_DIR, "instance", "predictions.db")}'
    )
    BCRYPT_LOG_ROUNDS = 4  # Faster for development

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    BCRYPT_LOG_ROUNDS = 12  # More secure for production

    # Get DATABASE_URL from environment
    DATABASE_URL = os.getenv("DATABASE_URL")

    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # Use absolute path for SQLite
        db_path = os.path.join(Config.BASE_DIR, 'instance', 'predictions.db')
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"

    # Fix Heroku-style URLs
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://")

# Config dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}