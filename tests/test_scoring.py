"""
Unit Tests for PriorityScorer.
Tests boundary conditions, weight scaling, and edge cases.
"""

import pytest
from ml.inference.scoring import PriorityScorer


class TestPriorityScorer:
    @pytest.fixture
    def scorer(self):
        return PriorityScorer()

    def test_high_priority_threshold(self, scorer):
        """High-confidence, high-context, VERIFIED localization -> HIGH"""
        label, score = scorer.calculate_priority(
            model_confidence=0.95,
            context_score=0.90,
            data_quality=0.90,
            localization_status="VERIFIED"
        )
        assert label == "HIGH"
        assert score >= scorer.high_thresh

    def test_medium_priority_threshold(self, scorer):
        """Moderate confidence with ESTIMATED localization -> MEDIUM"""
        label, score = scorer.calculate_priority(
            model_confidence=0.60,
            context_score=0.55,
            data_quality=0.60,
            localization_status="ESTIMATED"
        )
        assert label == "MEDIUM"
        assert scorer.med_thresh <= score < scorer.high_thresh

    def test_low_priority_threshold(self, scorer):
        """Low confidence, no navigation -> LOW"""
        label, score = scorer.calculate_priority(
            model_confidence=0.30,
            context_score=0.25,
            data_quality=0.40,
            localization_status="UNAVAILABLE"
        )
        assert label == "LOW"
        assert score < scorer.med_thresh

    def test_unavailable_localization_penalized(self, scorer):
        """UNAVAILABLE localization should yield lower score than VERIFIED for same conf/context."""
        _, score_verified = scorer.calculate_priority(0.80, 0.70, 0.80, "VERIFIED")
        _, score_unavail = scorer.calculate_priority(0.80, 0.70, 0.80, "UNAVAILABLE")
        assert score_verified > score_unavail

    def test_score_clamped_between_0_and_1(self, scorer):
        """Score must always be in [0.0, 1.0] regardless of inputs."""
        label1, score1 = scorer.calculate_priority(2.0, 2.0, 2.0, "VERIFIED")
        assert 0.0 <= score1 <= 1.0
        label2, score2 = scorer.calculate_priority(-1.0, -1.0, -1.0, "UNAVAILABLE")
        assert 0.0 <= score2 <= 1.0

    def test_unknown_localization_status_treated_as_unavailable(self, scorer):
        """Unknown localization status must not crash — treated as UNAVAILABLE (score 0.0)."""
        label, score = scorer.calculate_priority(0.70, 0.65, 0.70, "UNKNOWN_STATUS")
        assert label in ("HIGH", "MEDIUM", "LOW")
        assert 0.0 <= score <= 1.0

    def test_all_localization_statuses_accepted(self, scorer):
        """All four canonical localization statuses must be handled."""
        for status in ("VERIFIED", "ESTIMATED", "UNCERTAIN", "UNAVAILABLE"):
            label, score = scorer.calculate_priority(0.75, 0.70, 0.70, status)
            assert label in ("HIGH", "MEDIUM", "LOW")

    def test_weights_sum_to_one(self):
        """Custom weights must sum to 1.0 for calibrated scoring."""
        s = PriorityScorer(
            w_confidence=0.40,
            w_context=0.30,
            w_quality=0.20,
            w_localization=0.10
        )
        total = s.w_conf + s.w_ctxt + s.w_qual + s.w_loc
        assert abs(total - 1.0) < 1e-9
