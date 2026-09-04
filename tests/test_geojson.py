"""
Unit Tests for GeoJSON and CSV Export Utilities.
"""

import pytest
import csv
import io
from backend.app.utils.geojson import contacts_to_geojson, contacts_to_csv_string
from backend.app.schemas.contact import Contact, BoundingBox


def make_contact(**kwargs) -> Contact:
    """Factory helper for building test Contact objects."""
    defaults = dict(
        contact_id="TEST_C001",
        survey_id="SURV_TEST",
        class_name="shipwreck",
        confidence=0.88,
        bbox=BoundingBox(x1=100, y1=200, x2=300, y2=400),
        data_quality=0.75,
        shadow_evidence=0.65,
        context_score=0.72,
        priority="HIGH",
        latitude=54.1234,
        longitude=12.6789,
        localization_status="ESTIMATED",
        review_status="AI_CANDIDATE",
        review_note=None,
        model_version="DRISHTI-YOLOv8s-baseline-v1",
        model_score=0.88,
        calibrated_confidence=None,
        location_uncertainty=None
    )
    defaults.update(kwargs)
    return Contact(**defaults)


class TestContactsToGeoJSON:
    def test_geojson_structure(self):
        """Output must be a valid GeoJSON FeatureCollection."""
        contacts = [make_contact()]
        result = contacts_to_geojson(contacts)
        assert result["type"] == "FeatureCollection"
        assert isinstance(result["features"], list)
        assert len(result["features"]) == 1

    def test_feature_has_geometry_when_coords_present(self):
        """Contacts with lat/lon produce Point geometry."""
        c = make_contact(latitude=54.12, longitude=12.67)
        result = contacts_to_geojson([c])
        feat = result["features"][0]
        assert feat["geometry"]["type"] == "Point"
        assert feat["geometry"]["coordinates"] == [12.67, 54.12]

    def test_feature_has_null_geometry_when_no_coords(self):
        """Contacts with UNAVAILABLE localization must have null geometry (valid GeoJSON)."""
        c = make_contact(latitude=None, longitude=None, localization_status="UNAVAILABLE")
        result = contacts_to_geojson([c])
        feat = result["features"][0]
        assert feat["geometry"] is None

    def test_properties_contain_required_fields(self):
        """All required triage fields must appear in GeoJSON properties."""
        c = make_contact()
        result = contacts_to_geojson([c])
        props = result["features"][0]["properties"]
        for field in ("contact_id", "survey_id", "class_name", "confidence",
                      "priority", "localization_status", "review_status"):
            assert field in props, f"Missing property: {field}"

    def test_empty_contact_list_returns_empty_feature_collection(self):
        result = contacts_to_geojson([])
        assert result["type"] == "FeatureCollection"
        assert result["features"] == []

    def test_coordinates_rounded_to_6_decimal_places(self):
        """Coordinates must be rounded to 6dp to keep GeoJSON compact."""
        c = make_contact(latitude=54.123456789, longitude=12.987654321)
        result = contacts_to_geojson([c])
        coords = result["features"][0]["geometry"]["coordinates"]
        # Should be rounded to 6dp
        assert coords[0] == round(12.987654321, 6)
        assert coords[1] == round(54.123456789, 6)


class TestContactsToCSV:
    def test_csv_has_header_row(self):
        """First row must be the header."""
        contacts = [make_contact()]
        csv_str = contacts_to_csv_string(contacts)
        reader = csv.reader(io.StringIO(csv_str))
        header = next(reader)
        assert "contact_id" in header
        assert "class_name" in header
        assert "confidence" in header
        assert "latitude" in header
        assert "longitude" in header

    def test_csv_row_count_matches_contacts(self):
        """CSV must have exactly N data rows for N contacts."""
        contacts = [make_contact(contact_id=f"C{i:03d}") for i in range(5)]
        csv_str = contacts_to_csv_string(contacts)
        reader = list(csv.reader(io.StringIO(csv_str)))
        assert len(reader) == 6  # 1 header + 5 data rows

    def test_empty_lat_lon_when_unavailable(self):
        """Contacts with no coordinates must have empty lat/lon columns in CSV."""
        c = make_contact(latitude=None, longitude=None)
        csv_str = contacts_to_csv_string([c])
        reader = list(csv.reader(io.StringIO(csv_str)))
        # Row index 1 is the first data row
        data = dict(zip(reader[0], reader[1]))
        assert data["latitude"] == ""
        assert data["longitude"] == ""
