"""
Tests for Explainability Engine (ExplainabilityEngine).
"""

import pytest
from ml.inference.explanation import ExplainabilityEngine


def test_explanation_high_confidence_evidence():
    engine = ExplainabilityEngine()
    context = {"shadow_evidence": 0.85, "local_contrast": 0.80, "shadow_length_est": 25.0}

    expl = engine.generate_explanation(
        detector_confidence=0.88,
        acoustic_prob=0.85,
        classifier_confidence=0.82,
        context=context,
        track_persistence=3,
        novelty_score=20.0,
        sonar_quality_score=90.0,
        risk_score=75.0
    )

    assert expl["overall_confidence_label"] == "HIGH CONFIDENCE"
    assert len(expl["positive_evidence"]) >= 3
    assert any("shadow" in p.lower() for p in expl["positive_evidence"])
    assert any("pings" in p.lower() for p in expl["positive_evidence"])


def test_explanation_marginal_detection():
    engine = ExplainabilityEngine()
    context = {"shadow_evidence": 0.05, "local_contrast": 0.15, "shadow_length_est": 0.0}

    expl = engine.generate_explanation(
        detector_confidence=0.35,
        acoustic_prob=0.30,
        classifier_confidence=0.35,
        context=context,
        track_persistence=1,
        novelty_score=70.0,
        sonar_quality_score=35.0,
        risk_score=25.0
    )

    assert expl["overall_confidence_label"] in ("LOW CONFIDENCE", "UNCERTAIN")
    assert len(expl["negative_evidence"]) >= 2
