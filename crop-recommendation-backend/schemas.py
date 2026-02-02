from pydantic import BaseModel, Field, field_validator
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
