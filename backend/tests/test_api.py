"""
API Integration tests for FastAPI endpoints.
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_root_health_check():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "Quantum Estate X" in data["app"]


def test_get_parcels():
    response = client.get("/api/parcels")
    assert response.status_code == 200
    parcels = response.json()
    assert len(parcels) == 8


def test_get_infrastructure_reports():
    response = client.get("/api/parcels/infrastructure")
    assert response.status_code == 200
    reports = response.json()
    assert len(reports) == 8
    assert "water_demand_lpd" in reports[0]


def test_pune_workflow_endpoint():
    payload = {"budget_crore": 15.0}
    response = client.post("/api/workflow/pune-development", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "parcels_evaluated" in data
    assert "infrastructure_reports" in data
    assert "benchmark" in data
    assert "recommendation" in data
    assert data["recommendation"]["budget_requested_cr"] == 15.0

