"""
Tests for INCOIS LAS Connector and Ferret Listing Parser.
"""

from ml.drift.ingestion.incois_las import IncoisLasConnector
from ml.drift.ingestion.validators import is_bad_value, FERRET_BAD_FLAG


def test_ferret_bad_flag_detection():
    assert is_bad_value(FERRET_BAD_FLAG) is True
    assert is_bad_value(-1.0e34) is True
    assert is_bad_value(None) is True
    assert is_bad_value(float("nan")) is True
    assert is_bad_value(12.5) is False


def test_incois_audit_parsing():
    connector = IncoisLasConnector()
    audit = connector.audit()

    assert audit["source"] == "INCOIS_LAS"
    if audit["status"] == "AVAILABLE":
        assert audit["product_family"] == "Argo Value Added Products"
        assert "D26" in audit["columns"]
        assert audit["contains_currents_uo_vo"] is False
        assert audit["contains_winds"] is False


def test_incois_offline_fallback():
    # Force offline mode with non-existent cache
    connector = IncoisLasConnector(online_mode=False, cache_dir="d:/non_existent_cache")
    audit = connector.audit()
    assert audit["status"] == "INCOIS_SOURCE_UNAVAILABLE"
