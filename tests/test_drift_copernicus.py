"""
Tests for Copernicus GLORYS12V1 NetCDF Ingestion and Data Auditing.
"""

import pytest
from datetime import datetime, timezone
from ml.drift.ingestion.copernicus import CopernicusIngestor
from ml.drift.ingestion.validators import QualityFlag


def test_copernicus_audit():
    ingestor = CopernicusIngestor()
    audit = ingestor.audit()

    assert audit["source"] == "COPERNICUS_MARINE_SERVICE"
    assert audit["drift_mode"] == "SURFACE_DRIFT_MODE"
    assert audit["spatial_resolution_deg"] == pytest.approx(0.08333333333333333, rel=1e-3)
    assert audit["time_steps_count"] == 1
    assert "uo" in audit["variables"]
    assert "vo" in audit["variables"]
    assert "thetao" in audit["variables"]
    assert "so" in audit["variables"]

    # Verify units are preserved accurately
    uo_var = audit["variables"]["uo"]
    assert uo_var["units"] == "m s-1"
    assert uo_var["missing_pct"] > 25.0  # Land mask


def test_copernicus_sample_environment():
    ingestor = CopernicusIngestor()
    t = datetime(2026, 6, 23, 0, 0, tzinfo=timezone.utc)

    # Open ocean coordinate in the Arabian Sea
    obs = ingestor.sample_environment(15.0, 70.0, t)
    assert obs.quality_flag == QualityFlag.GOOD
    assert obs.uo is not None
    assert obs.vo is not None
    assert obs.current_speed is not None
    assert 0.0 <= obs.current_heading <= 360.0
    assert obs.depth == pytest.approx(0.494, abs=0.01)


def test_copernicus_land_mask_handling():
    ingestor = CopernicusIngestor()
    t = datetime(2026, 6, 23, 0, 0, tzinfo=timezone.utc)

    # Point on land (e.g. inland India)
    obs = ingestor.sample_environment(20.0, 78.0, t)
    assert obs.quality_flag == QualityFlag.LAND_MASKED
    assert obs.uo is None
    assert obs.vo is None


def test_copernicus_fast_interpolator():
    ingestor = CopernicusIngestor()
    field = ingestor.get_interpolator(15.0, 70.0, margin_deg=2.0)
    assert field["u_interp"] is not None
    assert field["v_interp"] is not None

    u_val = float(field["u_interp"]((15.0, 70.0)))
    v_val = float(field["v_interp"]((15.0, 70.0)))
    assert isinstance(u_val, float) and isinstance(v_val, float)
