"""
Ocean Observation Validation and Quality Flagging.

Enforces physical boundaries, unit consistency, bad-flag detection,
and scientific data integrity across ocean and drift datasets.
"""

from enum import Enum
from typing import Optional, Dict, Any, Tuple
import math


class QualityFlag(str, Enum):
    GOOD = "GOOD"
    SUSPECT = "SUSPECT"
    OUT_OF_BOUNDS = "OUT_OF_BOUNDS"
    LAND_MASKED = "LAND_MASKED"
    UNAVAILABLE = "UNAVAILABLE"


# Physical bounds for oceanographic variables (Earth limits)
VARIABLE_PHYSICAL_BOUNDS: Dict[str, Tuple[float, float, str]] = {
    "uo": (-10.0, 10.0, "m s-1"),
    "vo": (-10.0, 10.0, "m s-1"),
    "speed": (0.0, 15.0, "m s-1"),
    "thetao": (-4.0, 45.0, "degrees_C"),
    "temperature": (-4.0, 45.0, "degrees_C"),
    "so": (0.0, 50.0, "1e-3"),
    "salinity": (0.0, 50.0, "1e-3"),
    "zos": (-5.0, 5.0, "m"),
    "mlotst": (0.0, 2500.0, "m"),
    "bottomT": (-4.0, 45.0, "degrees_C"),
    "D26": (0.0, 1000.0, "m"),
    "wind_u": (-100.0, 100.0, "m s-1"),
    "wind_v": (-100.0, 100.0, "m s-1"),
    "wave_height": (0.0, 40.0, "m"),
    "wave_period": (0.0, 40.0, "s"),
}

FERRET_BAD_FLAG = -1.0e34


def is_bad_value(val: Any) -> bool:
    """Detects NaNs, infinities, and Ferret/LAS bad flags."""
    if val is None:
        return True
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return True
        if abs(f - FERRET_BAD_FLAG) < 1.0e30 or f <= -1.0e33:
            return True
        return False
    except (ValueError, TypeError):
        return True


def validate_variable(var_name: str, value: Optional[float], unit: Optional[str] = None) -> Tuple[Optional[float], QualityFlag, Optional[str]]:
    """
    Validates an environmental measurement against physical bounds and expected units.
    
    Returns:
        (sanitized_value, quality_flag, warning_message)
    """
    if is_bad_value(value):
        return None, QualityFlag.UNAVAILABLE, f"{var_name} missing or bad flag"

    fval = float(value)

    if var_name in VARIABLE_PHYSICAL_BOUNDS:
        vmin, vmax, expected_unit = VARIABLE_PHYSICAL_BOUNDS[var_name]
        if fval < vmin or fval > vmax:
            return fval, QualityFlag.OUT_OF_BOUNDS, (
                f"{var_name} value {fval:.3f} outside physical range [{vmin}, {vmax}]"
            )
        if unit and expected_unit:
            # Allow common representations
            u_clean = unit.strip().lower()
            exp_clean = expected_unit.strip().lower()
            if u_clean != exp_clean and not (u_clean in ("mts", "m", "meters") and exp_clean in ("m", "mts")):
                # Check degree variations
                if not ("deg" in u_clean and "deg" in exp_clean):
                    return fval, QualityFlag.SUSPECT, f"Unit mismatch: expected {expected_unit}, got {unit}"

    return fval, QualityFlag.GOOD, None


def validate_coordinates(lat: float, lon: float) -> Tuple[float, float, QualityFlag]:
    """
    Validates latitude and longitude, checking WGS84 boundaries [-90, 90] and [-180, 180].
    """
    if is_bad_value(lat) or is_bad_value(lon):
        return 0.0, 0.0, QualityFlag.OUT_OF_BOUNDS

    lat_f = float(lat)
    lon_f = float(lon)

    if lat_f < -90.0 or lat_f > 90.0:
        return lat_f, lon_f, QualityFlag.OUT_OF_BOUNDS

    # Normalize longitude to [-180, 180]
    while lon_f > 180.0:
        lon_f -= 360.0
    while lon_f < -180.0:
        lon_f += 360.0

    return lat_f, lon_f, QualityFlag.GOOD
