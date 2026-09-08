"""
FastAPI Drift Forecasting and Ocean Intelligence Endpoints.

Routes:
  POST /api/drift/predict
  GET  /api/drift/{forecast_id}
  GET  /api/contacts/{contact_id}/drift
  GET  /api/drift/{forecast_id}/trajectory
  GET  /api/drift/{forecast_id}/uncertainty
  GET  /api/drift/models
  GET  /api/drift/data-status
  GET  /api/drift/metrics
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.schemas.drift import (
    DriftPredictionRequest,
    DriftForecastDetail,
    DriftForecastSummary,
    OceanDataStatusResponse
)
from backend.app.services.drift_service import DriftService
from backend.app.services.ocean_data_service import OceanDataService
from ml.drift.models.registry import ModelRegistry

router = APIRouter(tags=["Ocean Drift Intelligence"])


@router.post("/api/drift/predict", response_model=DriftForecastDetail)
async def predict_drift(
    request: DriftPredictionRequest,
    db: Session = Depends(get_db)
):
    """
    Computes a 24h, 48h, and 72h drift forecast for a ghost-net contact or geographic coordinate.
    Uses Copernicus GLORYS12V1 ocean currents with Runge-Kutta integration and empirical uncertainty.
    """
    service = DriftService(db)
    try:
        forecast = service.predict_drift(request)
        return forecast
    except Exception as exc:
        logger.error("Drift prediction failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Drift prediction failed: {str(exc)}"
        )


@router.get("/api/drift/data-status", response_model=OceanDataStatusResponse)
async def get_ocean_data_status():
    """
    Returns operational availability, date ranges, depth levels, and variables
    for Copernicus Marine Service and INCOIS LAS catalogs.
    """
    return OceanDataService.get_status()


@router.get("/api/drift/models")
async def get_drift_models():
    """
    Returns registered drift models, versions, and current champion model status.
    """
    registry = ModelRegistry()
    return {
        "champion_model": registry.get_champion().get("model_name", "PHYSICS"),
        "models": registry.get_all_models()
    }


@router.get("/api/drift/models/comparison")
@router.get("/api/drift/metrics")
async def get_drift_metrics():
    """
    Returns empirical multi-horizon error comparison table (Persistence vs Physics vs GRU vs LSTM).
    Reports INSUFFICIENT_VALIDATED_DATA honestly if field drifter observations are pending.
    """
    registry = ModelRegistry()
    champ = registry.get_champion().get("model_name", "PHYSICS")
    return {
        "champion_model": champ,
        "comparison_timestamp": registry.data.get("last_updated"),
        "models": registry.get_all_models()
    }


@router.get("/api/contacts/{contact_id}/drift", response_model=List[DriftForecastSummary])
async def get_contact_drift_forecasts(
    contact_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves all historical and operational drift forecasts computed for a specific contact.
    """
    service = DriftService(db)
    return service.get_forecasts_for_contact(contact_id)


@router.get("/api/drift/{forecast_id}", response_model=DriftForecastDetail)
async def get_drift_forecast(
    forecast_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves a specific drift forecast by forecast_id including complete waypoints and GeoJSON.
    """
    service = DriftService(db)
    fc = service.get_forecast(forecast_id)
    if not fc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Forecast '{forecast_id}' not found.")
    return fc


@router.get("/api/drift/{forecast_id}/trajectory")
async def get_drift_trajectory_geojson(
    forecast_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns trajectory GeoJSON FeatureCollection with line string and milestone points.
    """
    service = DriftService(db)
    fc = service.get_forecast(forecast_id)
    if not fc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Forecast '{forecast_id}' not found.")
    return fc.geojson


@router.get("/api/drift/{forecast_id}/uncertainty")
async def get_drift_uncertainty(
    forecast_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns empirical uncertainty polygons for 24h, 48h, and 72h forecast horizons.
    """
    service = DriftService(db)
    fc = service.get_forecast(forecast_id)
    if not fc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Forecast '{forecast_id}' not found.")

    uncertainty_features = [
        f for f in fc.geojson.get("features", [])
        if f.get("properties", {}).get("type") == "uncertainty_polygon"
    ]
    return {
        "forecast_id": forecast_id,
        "uncertainty_features": uncertainty_features
    }
