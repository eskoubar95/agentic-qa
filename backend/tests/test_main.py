"""Unit tests for FastAPI app (health endpoint)."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200():
    """GET /health returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_expected_body():
    """GET /health returns healthy status and service name."""
    response = client.get("/health")
    data = response.json()
    assert data == {"status": "healthy", "service": "agentic-qa-backend"}


def test_health_response_is_json():
    """GET /health has JSON content-type."""
    response = client.get("/health")
    assert "application/json" in response.headers.get("content-type", "")
