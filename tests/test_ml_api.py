"""
Tests for ML Platform and Analyst API Endpoints.
"""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_api_ml_models():
    res = client.get("/api/ml/models")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "active_stack" in data
    assert "stack_id" in data["active_stack"]


def test_api_ml_metrics():
    res = client.get("/api/ml/metrics")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "total_contacts_analyzed" in data
    assert "pipeline_precision" in str(data).lower() or "estimated_precision" in str(data).lower()


def test_api_anomalies_unknown():
    res = client.get("/api/anomalies/unknown")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_api_active_learning_samples():
    res = client.get("/api/active-learning/samples")
    assert res.status_code == 200
    data = res.json()
    assert "samples" in data


def test_api_analyst_query():
    query_payload = {"query": "show high risk ghost nets", "limit": 10}
    res = client.post("/api/analyst/query", json=query_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["query"] == "show high risk ghost nets"
    assert "filters_applied" in data
    assert isinstance(data["contacts"], list)


def test_api_resurvey_recommendations():
    res = client.get("/api/resurvey/recommendations")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "recommendations" in data
