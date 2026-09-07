"""
Comprehensive End-to-End Integration Test Suite for SONAR-INTEL.

Tests full lifecycle across:
- API health & system telemetry
- Swath & navigation ingestion
- DRISHTI anomaly inference & scoring
- Contact verification and human triage
- Mission summary calculation
- GeoJSON and CSV spatial export
- AI Natural Language Sonar Analyst queries
"""

import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestE2EIntegration:
    @pytest.fixture(scope="class")
    @classmethod
    def client(cls):
        return TestClient(app)

    def test_health_probe_returns_extended_telemetry(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "model" in data
        assert "version" in data
        assert "database" in data
        assert "X-Process-Time-Ms" in resp.headers

    def test_full_survey_lifecycle_e2e(self, client):
        sonar_path = REPO_ROOT / "data" / "demo" / "sonar" / "viator_04_test_wreck.png"
        nav_path = REPO_ROOT / "data" / "demo" / "navigation" / "viator_04_nav.csv"

        if not sonar_path.exists() or not nav_path.exists():
            pytest.skip("Demo benchmark files not available")

        # 1. Ingest survey swath
        with open(sonar_path, "rb") as f_img, open(nav_path, "rb") as f_nav:
            upload_resp = client.post(
                "/api/surveys/upload",
                files={
                    "sonar_file": ("viator_04_test_wreck.png", f_img, "image/png"),
                    "nav_file": ("viator_04_nav.csv", f_nav, "text/csv")
                }
            )
        assert upload_resp.status_code in [200, 201], f"Upload failed: {upload_resp.text}"
        survey_data = upload_resp.json()
        survey_id = survey_data["survey_id"]
        assert survey_id.startswith("SURV_")
        assert survey_data["has_navigation"] is True

        # 2. Run analysis
        analyze_resp = client.post(
            f"/api/surveys/{survey_id}/analyze",
            json={"confidence_threshold": 0.15}
        )
        assert analyze_resp.status_code == 200, f"Analysis failed: {analyze_resp.text}"
        analysis_data = analyze_resp.json()
        contacts = analysis_data["contacts"]
        assert len(contacts) > 0

        # 3. Retrieve contacts endpoint
        contacts_resp = client.get(f"/api/surveys/{survey_id}/contacts")
        assert contacts_resp.status_code == 200
        retrieved_contacts = contacts_resp.json()
        assert len(retrieved_contacts) == len(contacts)

        # 4. Review triage workflow
        first_contact = contacts[0]
        cid = first_contact["contact_id"]
        review_resp = client.post(
            f"/api/contacts/{cid}/review",
            json={
                "review_status": "CONFIRMED",
                "review_note": "Verified acoustic highlight with distinct down-range acoustic shadow."
            }
        )
        assert review_resp.status_code == 200
        assert review_resp.json()["review_status"] == "CONFIRMED"

        # 5. Survey summary
        summary_resp = client.get(f"/api/surveys/{survey_id}/summary")
        assert summary_resp.status_code == 200
        summary_data = summary_resp.json()
        assert summary_data["total_contacts"] == len(contacts)
        assert summary_data["reviewed_count"] >= 1

        # 6. GeoJSON export
        geojson_resp = client.get(f"/api/surveys/{survey_id}/geojson")
        assert geojson_resp.status_code == 200
        geojson_data = geojson_resp.json()
        assert geojson_data["type"] == "FeatureCollection"
        assert len(geojson_data["features"]) == len(contacts)

        # 7. CSV export
        csv_resp = client.get(f"/api/surveys/{survey_id}/csv")
        assert csv_resp.status_code == 200
        assert "contact_id,survey_id,class_name" in csv_resp.text

        # 8. AI Analyst natural language query
        analyst_resp = client.post(
            "/api/analyst/query",
            json={"query": "show all confirmed contacts with high priority"}
        )
        assert analyst_resp.status_code == 200
        analyst_data = analyst_resp.json()
        assert "summary_text" in analyst_data
        assert analyst_data["total_matches"] >= 1
