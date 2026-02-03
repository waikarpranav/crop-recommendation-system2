from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import List, Optional, Dict
from datetime import datetime

class CropInput(BaseModel):
    """Schema for agricultural input features with strict validation"""
    N: float = Field(..., ge=0, le=140, description="Nitrogen content in soil")
    P: float = Field(..., ge=5, le=145, description="Phosphorus content in soil")
    K: float = Field(..., ge=5, le=205, description="Potassium content in soil")
    temperature: float = Field(..., ge=8, le=44, description="Temperature in Celsius")
    humidity: float = Field(..., ge=14, le=100, description="Relative humidity in %")
    ph: float = Field(..., ge=3.5, le=10, description="Soil pH value")
    rainfall: float = Field(..., ge=20, le=300, description="Rainfall in mm")

    @field_validator('*', mode='before')
    @classmethod
    def parse_float(cls, value):
        if isinstance(value, str):
            try:
                return float(value.strip())
            except ValueError:
                return value
        return value

class AlternativeCrop(BaseModel):
    """Schema for individual alternative crop suggestions"""
    crop: str
    suitability: str
    confidence: float

class PredictionResponse(BaseModel):
    """Standardized API response schema"""
    status: str = "success"
    request_id: str
    predicted_crop: str
    confidence: float
    alternatives: List[AlternativeCrop]
    input_data: Dict[str, float]
    reasons: List[str]
    timestamp: datetime = Field(default_factory=datetime.now)

class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str = "healthy"
    model_loaded: bool
    scaler_loaded: bool
    explainer_enabled: bool
    timestamp: datetime = Field(default_factory=datetime.now)


# -------------------- AUTHENTICATION SCHEMAS --------------------

class UserRegister(BaseModel):
    """Schema for user registration"""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=80, description="Username")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username is alphanumeric with underscores"""
        if not v.replace('_', '').isalnum():
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    email: str = Field(..., description="Email or username")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    """Schema for user data response (no password)"""
    id: int
    email: str
    username: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool
    predictions_count: Optional[int] = None


class TokenResponse(BaseModel):
    """Schema for authentication token response"""
    status: str = "success"
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserResponse


class TokenRefresh(BaseModel):
    """Schema for token refresh request"""
    refresh_token: str = Field(..., description="Refresh token")

