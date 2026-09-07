"""
Physics-Based Lagrangian Ocean Surface Drift Simulation Engine.

Integrates ocean surface velocity vector fields (uo, vo) from Copernicus GLORYS12V1
using Runge-Kutta 2nd-order (RK2 / Midpoint) or Euler forward advection.
Computes deterministic trajectories, instantaneous kinematics (speed, heading),
local tangent-plane displacements (Delta E, Delta N), and horizon milestones (24h, 48h, 72h).
"""

import math
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple

from ml.drift.ingestion.copernicus import CopernicusIngestor
from ml.drift.ingestion.common import (
    EARTH_RADIUS_M,
    normalize_longitude,
    latlon_to_tangent_plane,
    calculate_speed_and_heading,
    haversine_distance_km
)
from ml.drift.ingestion.validators import QualityFlag

logger = logging.getLogger(__name__)


@dataclass
class TrajectoryPoint:
    """A single spatial-temporal waypoint along a drift trajectory."""
    step_index: int
    timestamp: datetime
    horizon_hours: float
    latitude: float
    longitude: float
    east_displacement_m: float
    north_displacement_m: float
    distance_from_origin_km: float
    u_velocity: float
    v_velocity: float
    speed_ms: float
    heading_deg: float
    uncertainty_radius_km: float
    model_name: str
    quality_flag: str = "GOOD"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d


@dataclass
class DriftTrajectory:
    """Complete multi-horizon drift trajectory."""
    forecast_id: str
    origin_latitude: float
    origin_longitude: float
    origin_timestamp: datetime
    depth_m: float
    model_name: str
    model_version: str
    integration_method: str
    time_step_hours: float
    total_horizon_hours: float
    waypoints: List[TrajectoryPoint] = field(default_factory=list)
    milestones: Dict[str, TrajectoryPoint] = field(default_factory=dict)  # "24h", "48h", "72h"
    hotspot_score: float = 0.0
    hotspot_evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "forecast_id": self.forecast_id,
            "origin_latitude": self.origin_latitude,
            "origin_longitude": self.origin_longitude,
            "origin_timestamp": self.origin_timestamp.isoformat(),
            "depth_m": self.depth_m,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "integration_method": self.integration_method,
            "time_step_hours": self.time_step_hours,
            "total_horizon_hours": self.total_horizon_hours,
            "hotspot_score": self.hotspot_score,
            "hotspot_evidence": self.hotspot_evidence,
            "milestones": {k: v.to_dict() for k, v in self.milestones.items()},
            "waypoints": [w.to_dict() for w in self.waypoints]
        }

    def to_geojson(self) -> Dict[str, Any]:
        """Converts the trajectory to standard GeoJSON FeatureCollection."""
        coords = [[w.longitude, w.latitude] for w in self.waypoints]
        line_feature = {
            "type": "Feature",
            "properties": {
                "forecast_id": self.forecast_id,
                "model_name": self.model_name,
                "model_version": self.model_version,
                "total_drift_km": round(self.waypoints[-1].distance_from_origin_km, 2) if self.waypoints else 0.0
            },
            "geometry": {
                "type": "LineString",
                "coordinates": coords
            }
        }

        milestone_features = []
        for key, pt in self.milestones.items():
            milestone_features.append({
                "type": "Feature",
                "properties": {
                    "forecast_id": self.forecast_id,
                    "milestone": key,
                    "horizon_hours": pt.horizon_hours,
                    "model_name": self.model_name,
                    "timestamp": pt.timestamp.isoformat(),
                    "speed_ms": round(pt.speed_ms, 2),
                    "heading_deg": round(pt.heading_deg, 1),
                    "distance_km": round(pt.distance_from_origin_km, 2),
                    "uncertainty_radius_km": round(pt.uncertainty_radius_km, 2)
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [pt.longitude, pt.latitude]
                }
            })

        return {
            "type": "FeatureCollection",
            "features": [line_feature, *milestone_features]
        }


class PhysicsDriftEngine:
    """
    Lagrangian particle advection engine using Copernicus ocean currents.
    """

    def __init__(self, copernicus_ingestor: Optional[CopernicusIngestor] = None):
        self.ingestor = copernicus_ingestor or CopernicusIngestor()

    def _get_velocity_fast(
        self,
        lat: float,
        lon: float,
        local_field: Dict[str, Any]
    ) -> Tuple[float, float, QualityFlag]:
        """Fast microsecond velocity query from pre-extracted local field."""
        norm_lon = normalize_longitude(lon)
        u_interp = local_field.get("u_interp")
        v_interp = local_field.get("v_interp")

        if u_interp is None or v_interp is None:
            return 0.0, 0.0, QualityFlag.UNAVAILABLE

        try:
            u_val = float(u_interp((lat, norm_lon)))
            v_val = float(v_interp((lat, norm_lon)))
            if math.isnan(u_val) or math.isnan(v_val):
                return 0.0, 0.0, QualityFlag.LAND_MASKED
            return u_val, v_val, QualityFlag.GOOD
        except Exception:
            return 0.0, 0.0, QualityFlag.OUT_OF_BOUNDS

    def _advect_step_fast(
        self,
        lat: float,
        lon: float,
        dt_seconds: float,
        local_field: Dict[str, Any],
        method: str = "rk2"
    ) -> Tuple[float, float, float, float, QualityFlag]:
        """
        Advects position by dt_seconds using forward Euler or 2nd-order Runge-Kutta.
        
        Returns:
            (new_lat, new_lon, u, v, quality_flag)
        """
        if method == "rk2":
            u1, v1, flag1 = self._get_velocity_fast(lat, lon, local_field)

            dlat1_rad = (v1 * (dt_seconds / 2.0)) / EARTH_RADIUS_M
            mean_lat1 = lat + (math.degrees(dlat1_rad) / 2.0)
            cos_mean1 = max(1e-6, math.cos(math.radians(mean_lat1)))
            dlon1_rad = (u1 * (dt_seconds / 2.0)) / (EARTH_RADIUS_M * cos_mean1)

            mid_lat = lat + math.degrees(dlat1_rad)
            mid_lon = normalize_longitude(lon + math.degrees(dlon1_rad))

            u_mid, v_mid, flag_mid = self._get_velocity_fast(mid_lat, mid_lon, local_field)

            dlat_rad = (v_mid * dt_seconds) / EARTH_RADIUS_M
            mean_lat = lat + (math.degrees(dlat_rad) / 2.0)
            cos_mean = max(1e-6, math.cos(math.radians(mean_lat)))
            dlon_rad = (u_mid * dt_seconds) / (EARTH_RADIUS_M * cos_mean)

            new_lat = lat + math.degrees(dlat_rad)
            new_lon = normalize_longitude(lon + math.degrees(dlon_rad))
            return new_lat, new_lon, u_mid, v_mid, flag_mid
        else:
            u, v, flag = self._get_velocity_fast(lat, lon, local_field)
            dlat_rad = (v * dt_seconds) / EARTH_RADIUS_M
            mean_lat = lat + (math.degrees(dlat_rad) / 2.0)
            cos_mean = max(1e-6, math.cos(math.radians(mean_lat)))
            dlon_rad = (u * dt_seconds) / (EARTH_RADIUS_M * cos_mean)

            new_lat = lat + math.degrees(dlat_rad)
            new_lon = normalize_longitude(lon + math.degrees(dlon_rad))
            return new_lat, new_lon, u, v, flag

    def compute_trajectory(
        self,
        forecast_id: str,
        initial_lat: float,
        initial_lon: float,
        initial_timestamp: datetime,
        horizon_hours: int = 72,
        step_hours: float = 1.0,
        method: str = "rk2"
    ) -> DriftTrajectory:
        """
        Simulates deterministic physics trajectory from initial condition to horizon_hours.
        """
        if initial_timestamp.tzinfo is None:
            initial_timestamp = initial_timestamp.replace(tzinfo=timezone.utc)

        norm_lon = normalize_longitude(initial_lon)
        curr_lat = initial_lat
        curr_lon = norm_lon
        curr_time = initial_timestamp
        dt_seconds = step_hours * 3600.0

        # Pre-extract local vector field around origin (covering up to 4 degrees drift)
        local_field = self.ingestor.get_interpolator(initial_lat, norm_lon, margin_deg=4.0)

        total_steps = int(round(horizon_hours / step_hours))
        waypoints: List[TrajectoryPoint] = []
        milestones: Dict[str, TrajectoryPoint] = {}

        # Initial point (step 0)
        u0, v0, flag0 = self._get_velocity_fast(curr_lat, curr_lon, local_field)
        speed0, heading0 = calculate_speed_and_heading(u0, v0)

        initial_pt = TrajectoryPoint(
            step_index=0,
            timestamp=curr_time,
            horizon_hours=0.0,
            latitude=curr_lat,
            longitude=curr_lon,
            east_displacement_m=0.0,
            north_displacement_m=0.0,
            distance_from_origin_km=0.0,
            u_velocity=u0,
            v_velocity=v0,
            speed_ms=speed0,
            heading_deg=heading0,
            uncertainty_radius_km=0.5,
            model_name="PHYSICS_RK2" if method == "rk2" else "PHYSICS_EULER",
            quality_flag=flag0.value
        )
        waypoints.append(initial_pt)

        for step in range(1, total_steps + 1):
            next_lat, next_lon, u, v, flag = self._advect_step_fast(
                curr_lat, curr_lon, dt_seconds, local_field, method=method
            )
            curr_time = curr_time + timedelta(seconds=dt_seconds)
            h_hours = step * step_hours

            delta_e, delta_n = latlon_to_tangent_plane(next_lat, next_lon, initial_lat, norm_lon)
            dist_km = haversine_distance_km(initial_lat, norm_lon, next_lat, next_lon)
            speed, heading = calculate_speed_and_heading(u, v)

            # Empirical Lagrangian uncertainty growth: sigma(t) = 0.5 + 0.35 * (t^0.8)
            uncertainty_km = 0.5 + 0.35 * (h_hours ** 0.8)

            pt = TrajectoryPoint(
                step_index=step,
                timestamp=curr_time,
                horizon_hours=h_hours,
                latitude=next_lat,
                longitude=next_lon,
                east_displacement_m=delta_e,
                north_displacement_m=delta_n,
                distance_from_origin_km=dist_km,
                u_velocity=u,
                v_velocity=v,
                speed_ms=speed,
                heading_deg=heading,
                uncertainty_radius_km=round(uncertainty_km, 2),
                model_name="PHYSICS_RK2" if method == "rk2" else "PHYSICS_EULER",
                quality_flag=flag.value
            )
            waypoints.append(pt)

            if int(round(h_hours)) == 24 and "24h" not in milestones:
                milestones["24h"] = pt
            elif int(round(h_hours)) == 48 and "48h" not in milestones:
                milestones["48h"] = pt
            elif int(round(h_hours)) == 72 and "72h" not in milestones:
                milestones["72h"] = pt

            curr_lat = next_lat
            curr_lon = next_lon

        # Compute hotspot intelligence score
        final_dist = waypoints[-1].distance_from_origin_km if waypoints else 0.0
        # Retention / convergence heuristic: slower drift + higher current persistence = retention hotspot
        mean_speed = sum(w.speed_ms for w in waypoints) / max(1, len(waypoints))
        retention_score = max(0.0, min(100.0, 100.0 - (mean_speed * 15.0)))

        hotspot_evidence = {
            "mean_current_speed_ms": round(mean_speed, 3),
            "total_drift_displacement_km": round(final_dist, 2),
            "retention_indicator": "HIGH_RETENTION" if mean_speed < 0.2 else "DISPERSIVE",
            "copernicus_mode": "SURFACE_DRIFT_MODE",
            "depth_level_m": 0.494
        }

        trajectory = DriftTrajectory(
            forecast_id=forecast_id,
            origin_latitude=initial_lat,
            origin_longitude=norm_lon,
            origin_timestamp=initial_timestamp,
            depth_m=0.494,
            model_name="PHYSICS_RK2" if method == "rk2" else "PHYSICS_EULER",
            model_version="physics-glorys12v1-v1",
            integration_method=method,
            time_step_hours=step_hours,
            total_horizon_hours=float(horizon_hours),
            waypoints=waypoints,
            milestones=milestones,
            hotspot_score=round(retention_score, 1),
            hotspot_evidence=hotspot_evidence
        )
        return trajectory
