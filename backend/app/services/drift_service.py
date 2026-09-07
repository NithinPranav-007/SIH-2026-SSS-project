"""
Drift Forecasting Service.

Orchestrates:
1. Contact coordinate resolution (e.g. ghost net contacts)
2. Lagrangian physics trajectory integration
3. ML residual error evaluation (Physics vs GRU vs LSTM)
4. Empirical uncertainty boundaries (GeoJSON polygons)
5. PostGIS / SQLite persistence and retrieval
"""

import math
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from backend.app.database.models import (
    DriftForecastModel,
    DriftTrajectoryPointModel,
    DriftUncertaintyModel,
    ContactModel
)
from backend.app.schemas.drift import (
    DriftPredictionRequest,
    DriftForecastDetail,
    DriftForecastSummary
)
from ml.drift.physics.engine import PhysicsDriftEngine
from ml.drift.models.registry import ModelRegistry
from ml.drift.ingestion.common import (
    tangent_plane_to_latlon,
    haversine_distance_km
)

logger = logging.getLogger(__name__)


def generate_uncertainty_polygon(center_lat: float, center_lon: float, radius_km: float, num_points: int = 16) -> Dict[str, Any]:
    """
    Generates a GeoJSON Polygon representing a circular uncertainty buffer of radius_km.
    """
    coords = []
    radius_m = radius_km * 1000.0

    for i in range(num_points):
        angle = 2.0 * math.pi * i / num_points
        delta_e = radius_m * math.cos(angle)
        delta_n = radius_m * math.sin(angle)
        p_lat, p_lon = tangent_plane_to_latlon(delta_e, delta_n, center_lat, center_lon)
        coords.append([round(p_lon, 6), round(p_lat, 6)])

    # Close the polygon loop
    coords.append(coords[0])

    return {
        "type": "Polygon",
        "coordinates": [coords]
    }


class DriftService:
    """Core domain service for ghost-net drift forecasting."""

    def __init__(self, db: Session):
        self.db = db
        self.registry = ModelRegistry()
        self.physics_engine = PhysicsDriftEngine()

    def predict_drift(self, request: DriftPredictionRequest) -> DriftForecastDetail:
        """
        Executes drift simulation for a given contact or initial coordinate.
        """
        initial_lat = request.latitude
        initial_lon = request.longitude
        initial_time = request.timestamp

        # If contact_id provided, fetch ground truth coordinates from contact record
        contact = None
        if request.contact_id:
            contact = self.db.query(ContactModel).filter(ContactModel.contact_id == request.contact_id).first()
            if contact:
                if initial_lat is None and contact.latitude is not None:
                    initial_lat = contact.latitude
                if initial_lon is None and contact.longitude is not None:
                    initial_lon = contact.longitude
                if initial_time is None and contact.created_at is not None:
                    initial_time = contact.created_at

        if initial_lat is None or initial_lon is None:
            # Fallback to realistic coastal maritime coordinates (Baltic or Indian Ocean)
            initial_lat = 15.0
            initial_lon = 70.0
            logger.info("Using default coordinates (15.0, 70.0) as none were specified.")

        if initial_time is None:
            initial_time = datetime.now(timezone.utc)
        elif initial_time.tzinfo is None:
            initial_time = initial_time.replace(tzinfo=timezone.utc)

        forecast_id = f"FC_{uuid.uuid4().hex[:12].upper()}"
        horizon_hours = request.horizon_hours or 72

        # Model resolution
        champion_meta = self.registry.get_champion()
        champion_name = champion_meta.get("model_name", "PHYSICS")

        requested_model = request.model_preference or "CHAMPION"
        if requested_model == "CHAMPION":
            effective_model = champion_name
        else:
            effective_model = requested_model

        # 1. Execute deterministic Physics trajectory
        trajectory = self.physics_engine.compute_trajectory(
            forecast_id=forecast_id,
            initial_lat=initial_lat,
            initial_lon=initial_lon,
            initial_timestamp=initial_time,
            horizon_hours=horizon_hours,
            step_hours=1.0,
            method="rk2"
        )

        # 2. Check if ML residual correction is requested and trained
        ml_status_note = "Using Physics baseline."
        if "GRU" in effective_model or "LSTM" in effective_model:
            model_entry = self.registry.data.get("models", {}).get(effective_model, {})
            if model_entry.get("metrics", {}).get("status") != "VALIDATED":
                effective_model = "PHYSICS"
                ml_status_note = (
                    f"Selected model {requested_model} does not yet have validated weights on empirical trajectories. "
                    "Operating with Physics baseline (GLORYS12V1)."
                )

        # 3. Create database records
        forecast_record = DriftForecastModel(
            forecast_id=forecast_id,
            contact_id=request.contact_id,
            initial_latitude=initial_lat,
            initial_longitude=initial_lon,
            initial_timestamp=initial_time,
            depth=0.494,
            model_name=effective_model,
            model_version=trajectory.model_version,
            data_version="GLORYS12V1-SURFACE-DAILY",
            status="COMPLETED",
            execution_mode="REANALYSIS_ESTIMATE",
            hotspot_score=trajectory.hotspot_score,
            hotspot_evidence={
                **trajectory.hotspot_evidence,
                "model_selection_note": ml_status_note,
                "champion_model": champion_name
            },
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(forecast_record)

        # Add trajectory points
        for wp in trajectory.waypoints:
            pt_record = DriftTrajectoryPointModel(
                forecast_id=forecast_id,
                step_index=wp.step_index,
                timestamp=wp.timestamp,
                horizon_hours=wp.horizon_hours,
                latitude=wp.latitude,
                longitude=wp.longitude,
                east_displacement=wp.east_displacement_m,
                north_displacement=wp.north_displacement_m,
                uncertainty_radius=wp.uncertainty_radius_km,
                model=effective_model,
                speed=wp.speed_ms,
                heading=wp.heading_deg
            )
            self.db.add(pt_record)

        # Add uncertainty polygon regions
        uncertainty_polygons = {}
        for h_str, ms in trajectory.milestones.items():
            poly_geojson = generate_uncertainty_polygon(
                center_lat=ms.latitude,
                center_lon=ms.longitude,
                radius_km=ms.uncertainty_radius_km
            )
            uncertainty_polygons[h_str] = poly_geojson
            unc_record = DriftUncertaintyModel(
                forecast_id=forecast_id,
                horizon_hours=ms.horizon_hours,
                uncertainty_radius_km=ms.uncertainty_radius_km,
                polygon_geojson=poly_geojson
            )
            self.db.add(unc_record)

        self.db.commit()

        # Build combined GeoJSON
        geojson = trajectory.to_geojson()
        for h_str, poly in uncertainty_polygons.items():
            geojson["features"].append({
                "type": "Feature",
                "properties": {
                    "forecast_id": forecast_id,
                    "milestone": h_str,
                    "type": "uncertainty_polygon",
                    "radius_km": trajectory.milestones[h_str].uncertainty_radius_km
                },
                "geometry": poly
            })

        return DriftForecastDetail(
            forecast_id=forecast_id,
            contact_id=request.contact_id,
            initial_latitude=initial_lat,
            initial_longitude=initial_lon,
            initial_timestamp=initial_time.isoformat(),
            depth_m=0.494,
            model_name=effective_model,
            model_version=trajectory.model_version,
            champion_model=champion_name,
            execution_mode="REANALYSIS_ESTIMATE",
            hotspot_score=trajectory.hotspot_score,
            hotspot_evidence=forecast_record.hotspot_evidence,
            milestones={
                k: {
                    "horizon_hours": v.horizon_hours,
                    "timestamp": v.timestamp.isoformat(),
                    "latitude": round(v.latitude, 6),
                    "longitude": round(v.longitude, 6),
                    "distance_km": round(v.distance_from_origin_km, 2),
                    "speed_ms": round(v.speed_ms, 2),
                    "heading_deg": round(v.heading_deg, 1),
                    "uncertainty_radius_km": round(v.uncertainty_radius_km, 2)
                }
                for k, v in trajectory.milestones.items()
            },
            geojson=geojson,
            created_at=forecast_record.created_at.isoformat()
        )

    def get_forecast(self, forecast_id: str) -> Optional[DriftForecastDetail]:
        """Retrieves forecast with trajectory points and GeoJSON."""
        fc = self.db.query(DriftForecastModel).filter(DriftForecastModel.forecast_id == forecast_id).first()
        if not fc:
            return None

        points = self.db.query(DriftTrajectoryPointModel).filter(
            DriftTrajectoryPointModel.forecast_id == forecast_id
        ).order_by(DriftTrajectoryPointModel.step_index.asc()).all()

        uncertainties = self.db.query(DriftUncertaintyModel).filter(
            DriftUncertaintyModel.forecast_id == forecast_id
        ).all()

        coords = [[p.longitude, p.latitude] for p in points]
        line_feature = {
            "type": "Feature",
            "properties": {
                "forecast_id": fc.forecast_id,
                "model_name": fc.model_name
            },
            "geometry": {
                "type": "LineString",
                "coordinates": coords
            }
        }

        milestones = {}
        milestone_features = []
        for p in points:
            h = int(round(p.horizon_hours))
            if h in (24, 48, 72) and f"{h}h" not in milestones:
                key = f"{h}h"
                dist_km = haversine_distance_km(fc.initial_latitude, fc.initial_longitude, p.latitude, p.longitude)
                milestones[key] = {
                    "horizon_hours": p.horizon_hours,
                    "timestamp": p.timestamp.isoformat() if hasattr(p.timestamp, "isoformat") else str(p.timestamp),
                    "latitude": round(p.latitude, 6),
                    "longitude": round(p.longitude, 6),
                    "distance_km": round(dist_km, 2),
                    "speed_ms": round(p.speed or 0.0, 2),
                    "heading_deg": round(p.heading or 0.0, 1),
                    "uncertainty_radius_km": round(p.uncertainty_radius, 2)
                }
                milestone_features.append({
                    "type": "Feature",
                    "properties": {
                        "forecast_id": fc.forecast_id,
                        "milestone": key,
                        "horizon_hours": p.horizon_hours,
                        "uncertainty_radius_km": p.uncertainty_radius
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [p.longitude, p.latitude]
                    }
                })

        unc_features = [
            {
                "type": "Feature",
                "properties": {
                    "forecast_id": fc.forecast_id,
                    "horizon_hours": u.horizon_hours,
                    "type": "uncertainty_polygon",
                    "radius_km": u.uncertainty_radius_km
                },
                "geometry": u.polygon_geojson
            }
            for u in uncertainties if u.polygon_geojson
        ]

        geojson = {
            "type": "FeatureCollection",
            "features": [line_feature, *milestone_features, *unc_features]
        }

        champ_meta = self.registry.get_champion()
        return DriftForecastDetail(
            forecast_id=fc.forecast_id,
            contact_id=fc.contact_id,
            initial_latitude=fc.initial_latitude,
            initial_longitude=fc.initial_longitude,
            initial_timestamp=fc.initial_timestamp.isoformat() if hasattr(fc.initial_timestamp, "isoformat") else str(fc.initial_timestamp),
            depth_m=fc.depth,
            model_name=fc.model_name,
            model_version=fc.model_version,
            champion_model=champ_meta.get("model_name", "PHYSICS"),
            execution_mode=fc.execution_mode,
            hotspot_score=fc.hotspot_score or 0.0,
            hotspot_evidence=fc.hotspot_evidence or {},
            milestones=milestones,
            geojson=geojson,
            created_at=fc.created_at.isoformat() if hasattr(fc.created_at, "isoformat") else str(fc.created_at)
        )

    def get_forecasts_for_contact(self, contact_id: str) -> List[DriftForecastSummary]:
        """Lists drift forecasts for a specific contact."""
        forecasts = self.db.query(DriftForecastModel).filter(
            DriftForecastModel.contact_id == contact_id
        ).order_by(DriftForecastModel.created_at.desc()).all()

        champ = self.registry.get_champion().get("model_name", "PHYSICS")
        return [
            DriftForecastSummary(
                forecast_id=f.forecast_id,
                contact_id=f.contact_id,
                initial_latitude=f.initial_latitude,
                initial_longitude=f.initial_longitude,
                initial_timestamp=f.initial_timestamp.isoformat() if hasattr(f.initial_timestamp, "isoformat") else str(f.initial_timestamp),
                depth_m=f.depth,
                model_name=f.model_name,
                model_version=f.model_version,
                champion_model=champ,
                execution_mode=f.execution_mode,
                hotspot_score=f.hotspot_score or 0.0,
                hotspot_evidence=f.hotspot_evidence or {},
                milestones={},
                created_at=f.created_at.isoformat() if hasattr(f.created_at, "isoformat") else str(f.created_at)
            )
            for f in forecasts
        ]
