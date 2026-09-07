"""
Tests for Physics-Based Lagrangian Surface Drift Advection Engine.
"""

from datetime import datetime, timezone
from ml.drift.physics.engine import PhysicsDriftEngine


def test_physics_trajectory_simulation():
    engine = PhysicsDriftEngine()
    now = datetime(2026, 6, 23, 0, 0, tzinfo=timezone.utc)

    traj = engine.compute_trajectory(
        forecast_id="TEST_PHYSICS_001",
        initial_lat=15.0,
        initial_lon=70.0,
        initial_timestamp=now,
        horizon_hours=72,
        step_hours=1.0,
        method="rk2"
    )

    assert len(traj.waypoints) == 73  # step 0 to step 72
    assert "24h" in traj.milestones
    assert "48h" in traj.milestones
    assert "72h" in traj.milestones

    m24 = traj.milestones["24h"]
    m48 = traj.milestones["48h"]
    m72 = traj.milestones["72h"]

    assert m24.distance_from_origin_km > 0.0
    assert m48.distance_from_origin_km > m24.distance_from_origin_km
    assert m72.distance_from_origin_km > m48.distance_from_origin_km

    # Verify uncertainty increases with horizon
    assert m24.uncertainty_radius_km < m48.uncertainty_radius_km < m72.uncertainty_radius_km

    # Verify GeoJSON
    gj = traj.to_geojson()
    assert gj["type"] == "FeatureCollection"
    assert len(gj["features"]) >= 4  # line + 3 points
