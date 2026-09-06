"""
Tests for Physical Target Measurements (TargetMeasurer).
"""

import pytest
from ml.inference.measurement import TargetMeasurer


def test_measurement_with_verified_navigation():
    measurer = TargetMeasurer(default_cross_track_m_per_px=0.05, default_along_track_m_per_px=0.05)
    bbox = {"x1": 100, "y1": 100, "x2": 200, "y2": 150} # 100 px x 50 px -> 5m x 2.5m
    context = {"shadow_length_est": 80.0, "distance_from_nadir": 120.0}

    meas = measurer.compute_measurements(bbox, context, localization_status="VERIFIED")

    assert meas["length"]["unit"] == "m"
    assert meas["length"]["value"] == 5.0
    assert meas["width"]["value"] == 2.5
    assert meas["area"]["value"] == 12.5
    assert meas["length"]["is_estimated"] is True
    assert meas["length"]["confidence"] >= 0.80
    assert meas["shadow_length"]["value"] == 4.0


def test_measurement_unavailable_navigation():
    measurer = TargetMeasurer()
    bbox = {"x1": 10, "y1": 10, "x2": 50, "y2": 30}
    context = {"shadow_length_est": 0.0, "distance_from_nadir": 50.0}

    meas = measurer.compute_measurements(bbox, context, localization_status="UNAVAILABLE")

    # When nav is unavailable, values are pixel proxies with LOW confidence, not fabricated meters
    assert meas["length"]["is_estimated"] is False
    assert meas["length"]["confidence"] <= 0.30
    assert "PIXEL" in meas["length"]["method"]
