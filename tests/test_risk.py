"""
Tests for Calibrated Risk Scoring (RiskScorer).
"""

import pytest
from ml.inference.risk import RiskScorer


def test_risk_ordnance_critical():
    scorer = RiskScorer()
    res = scorer.compute_risk(class_name="ordnance", confidence=0.95, acoustic_prob=0.90)
    assert res["risk_level"] in ("CRITICAL", "HIGH")
    assert res["risk_score"] >= 70.0


def test_risk_unknown_not_auto_critical():
    scorer = RiskScorer()
    # Scientific domain rule: an unknown anomaly with normal confidence should NOT be auto-elevated to CRITICAL
    res = scorer.compute_risk(
        class_name="unknown_acoustic_anomaly",
        confidence=0.50,
        acoustic_prob=0.50,
        novelty_score=65.0,
        is_unknown=True
    )
    assert res["risk_level"] in ("MEDIUM", "LOW", "HIGH")
    assert res["risk_level"] != "CRITICAL"


def test_risk_massive_hazard_obstruction():
    scorer = RiskScorer()
    measurements = {"length": {"value": 35.0, "unit": "m"}}
    res = scorer.compute_risk(
        class_name="shipwreck",
        confidence=0.85,
        acoustic_prob=0.85,
        measurements=measurements
    )
    assert res["risk_score"] >= 65.0
    assert "hazard" in res["risk_label"].lower() or "navigation" in res["risk_label"].lower()
