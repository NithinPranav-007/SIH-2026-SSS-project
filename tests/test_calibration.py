"""
Tests for Confidence Calibration.
"""

import pytest
from ml.inference.calibration import ConfidenceCalibrator


def test_confidence_calibration_scaling():
    calibrator = ConfidenceCalibrator(temperature=1.2)
    # High confidence should be smoothly calibrated
    cal = calibrator.calibrate(0.95, data_quality=1.0)
    assert 0.0 < cal < 1.0


def test_confidence_calibration_quality_attenuation():
    calibrator = ConfidenceCalibrator()
    # High confidence on very low quality data must be scaled down
    cal_high_quality = calibrator.calibrate(0.90, data_quality=1.0)
    cal_low_quality = calibrator.calibrate(0.90, data_quality=0.30)
    assert cal_low_quality < cal_high_quality
