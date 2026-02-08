"""Unit tests for FastAPI app (health endpoint)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200():
    """GET /health returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_expected_body():
    """GET /health returns status, service, database, and redis fields."""
    response = client.get("/health")
    data = response.json()
    assert "status" in data
    assert data["service"] == "agentic-qa-backend"
    assert "database" in data
    assert "redis" in data


def test_health_response_is_json():
    """GET /health has JSON content-type."""
    response = client.get("/health")
    assert "application/json" in response.headers.get("content-type", "")
