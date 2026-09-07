"""
Tests for Multi-Ping Tracking (SonarPingTracker).
"""

from ml.tracking.ping_tracker import SonarPingTracker


def test_empty_detections_tracking():
    tracker = SonarPingTracker()
    tracks = tracker.associate_detections([])
    assert tracks == {}


def test_consecutive_ping_association():
    tracker = SonarPingTracker(max_ping_gap=30)
    # Simulate a shipwreck or shipping container spanning 3 consecutive sonar ping intervals
    dets = [
        {"bbox": {"x1": 200, "y1": 50, "x2": 260, "y2": 70}, "confidence": 0.85},
        {"bbox": {"x1": 202, "y1": 75, "x2": 258, "y2": 95}, "confidence": 0.88},
        {"bbox": {"x1": 205, "y1": 100, "x2": 262, "y2": 120}, "confidence": 0.82},
        # Separate unrelated detection far away in cross-track
        {"bbox": {"x1": 500, "y1": 50, "x2": 520, "y2": 65}, "confidence": 0.50}
    ]
    track_map = tracker.associate_detections(dets, survey_id="SURVEY_TEST")

    # First three detections should share the same track_id
    obs0 = track_map[0]
    obs1 = track_map[1]
    obs2 = track_map[2]
    obs3 = track_map[3]

    assert obs0.track_id == obs1.track_id == obs2.track_id
    assert obs0.observation_count == 3
    assert obs0.track_stability > 0.40
    # Unrelated detection should have its own track
    assert obs3.track_id != obs0.track_id
    assert obs3.observation_count == 1
