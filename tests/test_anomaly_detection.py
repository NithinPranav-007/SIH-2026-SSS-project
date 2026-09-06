"""
Tests for Unknown Acoustic Anomaly Detection (UnknownAnomalyDetector).
"""

import numpy as np
import pytest
from ml.inference.anomaly import UnknownAnomalyDetector


def test_anomaly_detector_known_prototype_match():
    detector = UnknownAnomalyDetector()
    # Test with prototype vector itself -> novelty score should be near 0
    proto = list(detector.prototypes.values())[0]

    res = detector.compute_novelty(proto, detector_confidence=0.85, data_quality=0.90)

    assert res["novelty_score"] < 15.0
    assert res["anomaly_type"] == "KNOWN_OBJECT"
    assert not res["is_confident_anomaly"]


def test_anomaly_detector_distant_vector():
    detector = UnknownAnomalyDetector()
    # Construct synthetic vector pointing in negative direction / far from positive prototypes
    distant = np.zeros(37, dtype=np.float32)
    distant[0] = -1.0
    distant[5] = -1.0
    distant = distant / np.linalg.norm(distant)

    res = detector.compute_novelty(distant, detector_confidence=0.80, data_quality=0.85)

    assert res["novelty_score"] >= detector.novelty_threshold
    assert res["anomaly_type"] == "UNKNOWN_ANOMALY"
    assert res["is_confident_anomaly"] is True
