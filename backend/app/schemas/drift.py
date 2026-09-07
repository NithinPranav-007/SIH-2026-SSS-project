"""
Pydantic Schemas for Drift Forecasting and Ocean Intelligence.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class DriftPredictionRequest(BaseModel):
    contact_id: Optional[str] = Field(default=None, description="Contact ID to forecast drift for")
    latitude: Optional[float] = Field(default=None, description="Initial latitude if contact_id not provided")
    longitude: Optional[float] = Field(default=None, description="Initial longitude if contact_id not provided")
    timestamp: Optional[datetime] = Field(default=None, description="Detection timestamp (UTC)")
    horizon_hours: int = Field(default=72, ge=1, le=168, description="Forecast horizon in hours (default 72h)")
    model_preference: Optional[str] = Field(default="CHAMPION", description="Model: CHAMPION | PHYSICS | PHYSICS_GRU | PHYSICS_LSTM")


class DriftMilestone(BaseModel):
    horizon_hours: float
    timestamp: str
    latitude: float
    longitude: float
    distance_km: float
    speed_ms: float
    heading_deg: float
    uncertainty_radius_km: float


class DriftForecastSummary(BaseModel):
    forecast_id: str
    contact_id: Optional[str] = None
    initial_latitude: float
    initial_longitude: float
    initial_timestamp: str
    depth_m: float
    model_name: str
    model_version: str
    champion_model: str
    execution_mode: str
    hotspot_score: float
    hotspot_evidence: Dict[str, Any] = Field(default_factory=dict)
    milestones: Dict[str, Any] = Field(default_factory=dict)
    created_at: str


class DriftForecastDetail(DriftForecastSummary):
    geojson: Dict[str, Any]


class OceanDataStatusResponse(BaseModel):
    copernicus: Dict[str, Any]
    incois: Dict[str, Any]
    summary: Dict[str, Any]
    last_checked: str


class DriftMetricsResponse(BaseModel):
    champion_model: str
    comparison_timestamp: str
    models: List[Dict[str, Any]]
