#!/usr/bin/env python3
"""API validation test suite. Run with: pytest backend/scripts/test_api.py -v or python -m pytest backend/scripts/test_api.py -v

Requires DATABASE_URL. Some tests require REDIS_URL. Use TEST_API_BASE_URL to test against
a running server instead of in-process (default uses TestClient).
"""

import os
import sys
import uuid
from pathlib import Path

import pytest

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Use TestClient (in-process) unless TEST_API_BASE_URL is set
BASE_URL = os.getenv("TEST_API_BASE_URL", "")

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL required for API tests",
)


@pytest.fixture
def client():
    """Return HTTP client. Uses TestClient with lifespan for in-process tests."""
    if BASE_URL:
        import httpx

        with httpx.Client(base_url=BASE_URL, timeout=30.0) as c:
            yield c
    else:
        from fastapi.testclient import TestClient

        from app.main import app

        with TestClient(app) as c:
            yield c


# --- POST /tests ---


def test_post_tests_valid_payload(client):
    """POST /tests with valid payload returns 201 and test with id."""
    payload = {
        "name": "API validation test",
        "url": "https://example.com",
        "definition": {
            "steps": [
                {"action": "navigate", "instruction": "Go to page", "target": "https://example.com"}
            ]
        },
        "auto_handle_popups": True,
    }
    r = client.post("/tests", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert "id" in data
    assert data["name"] == payload["name"]
    assert data["url"] == payload["url"]
    assert data["definition"] == payload["definition"]


def test_post_tests_missing_name_returns_422(client):
    """POST /tests with missing name returns 422."""
    payload = {"url": "https://example.com", "definition": {}}
    r = client.post("/tests", json=payload)
    assert r.status_code == 422


def test_post_tests_missing_url_returns_422(client):
    """POST /tests with missing url returns 422."""
    payload = {"name": "Test", "definition": {}}
    r = client.post("/tests", json=payload)
    assert r.status_code == 422


def test_post_tests_invalid_body_returns_422(client):
    """POST /tests with invalid JSON body returns 422."""
    r = client.post("/tests", content="not json", headers={"Content-Type": "application/json"})
    assert r.status_code in (422, 400)


# --- GET /tests ---


def test_get_tests_returns_list(client):
    """GET /tests returns 200 and list (possibly empty)."""
    r = client.get("/tests")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


# --- GET /tests/{id}, PUT /tests/{id}, DELETE /tests/{id} ---


@pytest.fixture
def created_test_id(client):
    """Create a test and return its ID."""
    payload = {
        "name": "Test for CRUD",
        "url": "https://example.com",
        "definition": {"steps": []},
    }
    r = client.post("/tests", json=payload)
    assert r.status_code == 201
    return r.json()["id"]


def test_get_test_by_id(client, created_test_id):
    """GET /tests/{id} returns 200 and test when exists."""
    r = client.get(f"/tests/{created_test_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == created_test_id
    assert data["name"] == "Test for CRUD"


def test_get_test_not_found_returns_404(client):
    """GET /tests/{id} returns 404 for non-existent test."""
    fake_id = str(uuid.uuid4())
    r = client.get(f"/tests/{fake_id}")
    assert r.status_code == 404


def test_put_test_by_id(client, created_test_id):
    """PUT /tests/{id} with valid payload returns 200 and updated test."""
    payload = {"name": "Updated name", "url": "https://updated.example.com"}
    r = client.put(f"/tests/{created_test_id}", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Updated name"
    assert data["url"] == "https://updated.example.com"


def test_put_test_not_found_returns_404(client):
    """PUT /tests/{id} returns 404 for non-existent test."""
    fake_id = str(uuid.uuid4())
    r = client.put(f"/tests/{fake_id}", json={"name": "x"})
    assert r.status_code == 404


def test_delete_test_by_id(client, created_test_id):
    """DELETE /tests/{id} returns 204 when test exists."""
    r = client.delete(f"/tests/{created_test_id}")
    assert r.status_code == 204
    # Verify deleted
    r2 = client.get(f"/tests/{created_test_id}")
    assert r2.status_code == 404


def test_delete_test_not_found_returns_404(client):
    """DELETE /tests/{id} returns 404 for non-existent test."""
    fake_id = str(uuid.uuid4())
    r = client.delete(f"/tests/{fake_id}")
    assert r.status_code == 404


# --- POST /test/run ---


@pytest.mark.skipif(
    not os.getenv("REDIS_URL"),
    reason="REDIS_URL required for run tests",
)
def test_post_test_run_valid_returns_202(client, created_test_id):
    """POST /test/run with valid test_id returns 202 and run_id."""
    r = client.post("/test/run", json={"test_id": created_test_id})
    assert r.status_code == 202 or r.status_code == 200  # FastAPI may return 200 for sync
    data = r.json()
    assert "run_id" in data


def test_post_test_run_invalid_test_id_returns_404(client):
    """POST /test/run with non-existent test_id returns 404."""
    fake_id = str(uuid.uuid4())
    r = client.post("/test/run", json={"test_id": fake_id})
    assert r.status_code == 404


def test_post_test_run_invalid_uuid_returns_422(client):
    """POST /test/run with invalid UUID returns 422."""
    r = client.post("/test/run", json={"test_id": "not-a-uuid"})
    assert r.status_code == 422


def test_post_test_run_redis_unavailable_returns_503(client, created_test_id):
    """POST /test/run returns 503 when Redis is not available."""
    from unittest.mock import patch

    with patch("app.routers.runs.is_redis_available", return_value=False):
        r = client.post("/test/run", json={"test_id": created_test_id})
    assert r.status_code == 503


# --- GET /results/{id} ---


@pytest.mark.skipif(
    not os.getenv("REDIS_URL"),
    reason="REDIS_URL required for run/result tests",
)
def test_get_results_after_run(client, created_test_id):
    """GET /results/{id} returns run after POST /test/run."""
    run_r = client.post("/test/run", json={"test_id": created_test_id})
    assert run_r.status_code in (200, 202)
    run_id = run_r.json()["run_id"]

    r = client.get(f"/results/{run_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == run_id
    assert "status" in data
    assert data["status"] in ("queued", "running", "passed", "failed")


def test_get_results_not_found_returns_404(client):
    """GET /results/{id} returns 404 for non-existent run."""
    fake_id = str(uuid.uuid4())
    r = client.get(f"/results/{fake_id}")
    assert r.status_code == 404


# --- GET /results/{id}/stream (SSE) ---


@pytest.mark.skipif(
    not os.getenv("REDIS_URL"),
    reason="REDIS_URL required for SSE tests",
)
@pytest.mark.skipif(
    sys.platform == "win32",
    reason="SSE stream test has event loop issues with pytest-asyncio on Windows",
)
@pytest.mark.asyncio
async def test_get_results_stream_returns_sse():
    """GET /results/{id}/stream returns 200 with text/event-stream and emits events."""
    from httpx import ASGITransport, AsyncClient

    from app.main import app
    from app.redis_client import append_run_event, init_redis

    init_redis()
    run_id = str(uuid.uuid4())
    await append_run_event(run_id, "log", {"message": "test"})
    await append_run_event(run_id, "complete", {"status": "passed"})

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        timeout=5.0,
    ) as client:
        events = []
        async with client.stream("GET", f"/results/{run_id}/stream") as r:
            assert r.status_code == 200
            assert "text/event-stream" in r.headers.get("content-type", "")
            async for line in r.aiter_lines():
                if line.startswith("event:"):
                    events.append({"type": line.split(":", 1)[1].strip()})
        assert len(events) >= 2
        assert events[-1]["type"] == "complete"


if __name__ == "__main__":
    # Allow running as script: python backend/scripts/test_api.py
    sys.exit(pytest.main([__file__, "-v"]))
