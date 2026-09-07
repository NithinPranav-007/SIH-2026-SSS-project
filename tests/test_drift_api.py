"""
Tests for FastAPI Drift Intelligence Endpoints.
"""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_api_drift_data_status():
    res = client.get("/api/drift/data-status")
    assert res.status_code == 200
    data = res.json()
    assert "copernicus" in data
    assert "incois" in data
    assert data["copernicus"]["available"] is True
    assert data["copernicus"]["drift_mode"] == "SURFACE_DRIFT_MODE"


def test_api_drift_models():
    res = client.get("/api/drift/models")
    assert res.status_code == 200
    data = res.json()
    assert data["champion_model"] == "PHYSICS"
    assert len(data["models"]) >= 3


def test_api_drift_metrics():
    res = client.get("/api/drift/metrics")
    assert res.status_code == 200
    data = res.json()
    assert data["champion_model"] == "PHYSICS"


def test_api_drift_predict_and_retrieve():
    # 1. Predict
    req = {
        "latitude": 15.0,
        "longitude": 70.0,
        "horizon_hours": 72,
        "model_preference": "CHAMPION"
    }
    pred_res = client.post("/api/drift/predict", json=req)
    assert pred_res.status_code == 200
    forecast = pred_res.json()
    fc_id = forecast["forecast_id"]

    assert "24h" in forecast["milestones"]
    assert "48h" in forecast["milestones"]
    assert "72h" in forecast["milestones"]
    assert forecast["hotspot_score"] >= 0.0

    # 2. Retrieve forecast detail
    get_res = client.get(f"/api/drift/{fc_id}")
    assert get_res.status_code == 200
    assert get_res.json()["forecast_id"] == fc_id

    # 3. Retrieve trajectory GeoJSON
    traj_res = client.get(f"/api/drift/{fc_id}/trajectory")
    assert traj_res.status_code == 200
    assert traj_res.json()["type"] == "FeatureCollection"

    # 4. Retrieve uncertainty polygons
    unc_res = client.get(f"/api/drift/{fc_id}/uncertainty")
    assert unc_res.status_code == 200
    assert len(unc_res.json()["uncertainty_features"]) == 3
