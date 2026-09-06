"""
Tests for Acoustic Fusion Model.
"""

import numpy as np
import pytest
from ml.inference.acoustic_fusion import AcousticFusionModel


def test_acoustic_fusion_feature_vector():
    model = AcousticFusionModel()
    context = {
        "shadow_evidence": 0.70,
        "local_contrast": 0.65,
        "aspect_ratio": 2.5,
        "texture_std": 18.0,
        "highlight_intensity": 180.0,
        "edge_density": 0.25,
        "distance_from_nadir": 150.0,
        "object_area_px": 500,
        "bbox_width": 25,
        "bbox_height": 20
    }
    vec = model.extract_feature_vector(context, data_quality=0.9)
    assert len(vec) == 14
    assert isinstance(vec, np.ndarray)


def test_acoustic_fusion_prediction():
    model = AcousticFusionModel()
    context = {
        "shadow_evidence": 0.75,
        "local_contrast": 0.70,
        "aspect_ratio": 2.0,
        "edge_density": 0.30
    }
    res = model.predict(context, detector_confidence=0.80, data_quality=0.85)
    assert "acoustic_probability" in res
    assert "evidence_score" in res
    assert 0.0 <= res["acoustic_probability"] <= 1.0
    assert 0.0 <= res["evidence_score"] <= 1.0
    assert "feature_importance" in res
