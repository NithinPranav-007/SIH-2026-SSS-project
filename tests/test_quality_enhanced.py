"""
Tests for Enhanced Sonar Quality Assessment.
"""

import numpy as np
from ml.preprocessing.quality import compute_image_quality


def test_quality_empty_image():
    res = compute_image_quality(None)
    assert res["quality_score"] == 0.0
    assert not res["is_usable"]
    assert len(res["warnings"]) > 0


def test_quality_synthetic_sonar_image():
    # Create realistic synthetic sonar waterfall swath: 400x800
    # Center nadir stripe + seabed backscatter + shadow zone + highlight target
    np.random.seed(42)
    img = np.random.normal(loc=110, scale=25, size=(400, 800)).clip(0, 255).astype(np.uint8)

    # Add bright center nadir stripe
    img[:, 390:410] = np.clip(img[:, 390:410] + 60, 0, 255)

    # Add highlight object
    img[150:180, 200:230] = 235

    # Add acoustic shadow deficit behind object
    img[150:180, 140:190] = 20

    report = compute_image_quality(img)

    assert "quality_score" in report
    assert 0.0 <= report["quality_score"] <= 100.0
    assert "quality_score_normalized" in report
    assert 0.0 <= report["quality_score_normalized"] <= 1.0

    # Test all enhanced indicators
    assert "contrast_score" in report
    assert "shadow_visibility" in report
    assert "nadir_interference" in report
    assert "dropout_ratio" in report
    assert "saturation_ratio" in report
    assert "speckle_index" in report
    assert "usable_area_ratio" in report
    assert isinstance(report["warnings"], list)


def test_quality_severe_saturation_and_dropout():
    img = np.zeros((200, 200), dtype=np.uint8)
    # 50% dead rows
    img[:100, :] = 0
    # 50% saturated pixels
    img[100:, :] = 255

    report = compute_image_quality(img)
    assert report["dropout_ratio"] > 0.4
    assert report["saturation_ratio"] > 0.4
    assert any("DROPOUT" in w for w in report["warnings"])
    assert any("SATURATION" in w for w in report["warnings"])
