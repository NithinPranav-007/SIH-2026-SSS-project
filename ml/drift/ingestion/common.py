"""
Canonical Ocean Observation Models and Geodetic Utilities.

Defines the universal representation for oceanographic and drift measurements,
along with mathematically rigorous local tangent-plane conversions (East/North),
WGS84 spherical geodesics, antimeridian wrapping, and temporal normalization.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
import math

from ml.drift.ingestion.validators import QualityFlag, validate_coordinates

# Earth mean radius (WGS-84 volumetric radius in meters)
EARTH_RADIUS_M = 6371000.0


def normalize_longitude(lon: float) -> float:
    """Normalizes longitude to the range [-180, 180]."""
    while lon > 180.0:
        lon -= 360.0
    while lon < -180.0:
        lon += 360.0
    return lon


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes great-circle distance between two geographic coordinates in meters.
    Uses Haversine formula, stable for all distances including antipodal points.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(normalize_longitude(lon2 - lon1))

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_M * c


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Returns Haversine distance in kilometers."""
    return haversine_distance_m(lat1, lon1, lat2, lon2) / 1000.0


def latlon_to_tangent_plane(lat: float, lon: float, origin_lat: float, origin_lon: float) -> Tuple[float, float]:
    """
    Converts (lat, lon) to Local Tangent Plane coordinates (East, North) in meters
    relative to a reference origin (origin_lat, origin_lon).
    
    Returns:
        (delta_e, delta_n) in meters.
    """
    phi0 = math.radians(origin_lat)
    phi = math.radians(lat)
    dphi = phi - phi0
    dlambda = math.radians(normalize_longitude(lon - origin_lon))

    # Mean latitude for projection factor
    mean_phi = (phi + phi0) / 2.0
    delta_e = EARTH_RADIUS_M * math.cos(mean_phi) * dlambda
    delta_n = EARTH_RADIUS_M * dphi
    return delta_e, delta_n


def tangent_plane_to_latlon(delta_e: float, delta_n: float, origin_lat: float, origin_lon: float) -> Tuple[float, float]:
    """
    Inverse projection: converts Local Tangent Plane (East, North) in meters
    back to (latitude, longitude) relative to reference origin.
    
    Returns:
        (lat, lon) in decimal degrees.
    """
    dphi = delta_n / EARTH_RADIUS_M
    lat = origin_lat + math.degrees(dphi)

    mean_phi = math.radians((origin_lat + lat) / 2.0)
    cos_mean = math.cos(mean_phi)
    if abs(cos_mean) < 1.0e-7:
        cos_mean = 1.0e-7

    dlambda = delta_e / (EARTH_RADIUS_M * cos_mean)
    lon = normalize_longitude(origin_lon + math.degrees(dlambda))
    return lat, lon


def calculate_speed_and_heading(u: float, v: float) -> Tuple[float, float]:
    """
    Calculates scalar speed (m/s) and meteorological/oceanographic heading (degrees).
    Heading is the direction towards which the current flows, 0 = North, 90 = East.
    """
    speed = math.sqrt(u * u + v * v)
    # math.atan2(u, v) gives angle clockwise from North (Y axis = North, X axis = East)
    heading_deg = (math.degrees(math.atan2(u, v)) + 360.0) % 360.0
    return speed, heading_deg


@dataclass
class OceanObservation:
    """
    Canonical, normalized representation of ocean environmental state at a point.
    
    SCIENTIFIC INTEGRITY RULE:
    Variables not present in source datasets are left as None.
    They are NEVER fabricated or defaulted to zero.
    """
    timestamp: datetime
    latitude: float
    longitude: float
    depth: float
    source: str
    quality_flag: QualityFlag = QualityFlag.GOOD

    # Ocean physical variables (populated only if genuinely observed/modeled)
    uo: Optional[float] = None              # Eastward current velocity (m/s)
    vo: Optional[float] = None              # Northward current velocity (m/s)
    temperature: Optional[float] = None     # Potential temperature (°C)
    salinity: Optional[float] = None        # Practical salinity (psu / 1e-3)
    zos: Optional[float] = None             # Sea surface height above geoid (m)
    mlotst: Optional[float] = None          # Mixed layer depth (m)
    bottomT: Optional[float] = None         # Sea floor temperature (°C)
    D26: Optional[float] = None             # 26-degree isotherm depth (m)

    # Atmospheric & Wave variables (populated only if available)
    wind_u: Optional[float] = None          # Eastward 10m wind (m/s)
    wind_v: Optional[float] = None          # Northward 10m wind (m/s)
    wave_height: Optional[float] = None     # Significant wave height (m)
    wave_period: Optional[float] = None     # Peak wave period (s)

    # Derived kinematic attributes
    current_speed: Optional[float] = None   # Speed (m/s)
    current_heading: Optional[float] = None # Heading (deg 0-360)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Ensure UTC timezone
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)
        else:
            self.timestamp = self.timestamp.astimezone(timezone.utc)

        # Normalize coordinates
        self.latitude, self.longitude, coord_flag = validate_coordinates(self.latitude, self.longitude)
        if coord_flag != QualityFlag.GOOD:
            self.quality_flag = coord_flag

        # Compute speed and heading if currents are present
        if self.uo is not None and self.vo is not None:
            self.current_speed, self.current_heading = calculate_speed_and_heading(self.uo, self.vo)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        d["quality_flag"] = self.quality_flag.value
        return d
