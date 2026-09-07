"""
Tests for SonarCropClassifier (Second-Stage FP Reduction).
"""

from ml.inference.classifier import SonarCropClassifier


def test_classifier_null_crop():
    clf = SonarCropClassifier()
    res = clf.classify_crop(None)
    assert res["label"] in ("REAL_TARGET", "SONAR_CLUTTER")
    assert res["probability"] == 0.50
    assert "fallback" in res["method"]


def test_classifier_high_contrast_shadow_target():
    clf = SonarCropClassifier()
    # High shadow and high contrast features
    feats = {
        "shadow_evidence": 0.85,
        "local_contrast": 0.80,
        "geom_score": 0.80,
        "edge_density": 0.35,
        "aspect_ratio": 2.2
    }
    res = clf.classify_crop(None, acoustic_features=feats)
    assert res["label"] == "REAL_TARGET"
    assert res["probability"] > 0.65


def test_classifier_clutter_signature():
    clf = SonarCropClassifier()
    # Low contrast, negligible shadow (classic seabed reverberation clutter)
    feats = {
        "shadow_evidence": 0.05,
        "local_contrast": 0.10,
        "geom_score": 0.30,
        "edge_density": 0.05,
        "aspect_ratio": 1.0
    }
    res = clf.classify_crop(None, acoustic_features=feats)
    assert res["label"] == "SONAR_CLUTTER"
    assert res["probability"] < 0.40
