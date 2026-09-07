"""
Tests for Spatial, Temporal, and Local Tangent Plane Coordinate Alignment.
"""

import pytest
from ml.drift.ingestion.common import (
    normalize_longitude,
    haversine_distance_km,
    latlon_to_tangent_plane,
    tangent_plane_to_latlon,
    calculate_speed_and_heading
)


def test_normalize_longitude():
    assert normalize_longitude(185.0) == -175.0
    assert normalize_longitude(-190.0) == 170.0
    assert normalize_longitude(0.0) == 0.0
    assert normalize_longitude(180.0) == 180.0
    assert normalize_longitude(-180.0) == -180.0


def test_haversine_distance():
    # 1 degree latitude ~ 111.19 km
    dist = haversine_distance_km(0.0, 0.0, 1.0, 0.0)
    assert 111.0 <= dist <= 112.0

    # Same point distance should be 0
    assert haversine_distance_km(54.0, 12.0, 54.0, 12.0) == 0.0


def test_tangent_plane_roundtrip():
    origin_lat, origin_lon = 15.0, 70.0
    target_lat, target_lon = 15.25, 70.30

    delta_e, delta_n = latlon_to_tangent_plane(target_lat, target_lon, origin_lat, origin_lon)
    rec_lat, rec_lon = tangent_plane_to_latlon(delta_e, delta_n, origin_lat, origin_lon)

    assert rec_lat == pytest.approx(target_lat, abs=1e-5)
    assert rec_lon == pytest.approx(target_lon, abs=1e-5)


def test_speed_and_heading():
    # Flowing purely North (u=0, v=1)
    speed, heading = calculate_speed_and_heading(0.0, 1.0)
    assert speed == pytest.approx(1.0)
    assert heading == pytest.approx(0.0)

    # Flowing purely East (u=1, v=0)
    speed, heading = calculate_speed_and_heading(1.0, 0.0)
    assert speed == pytest.approx(1.0)
    assert heading == pytest.approx(90.0)
