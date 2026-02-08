"""Redis queue and run-events stream tests."""

import os
import uuid
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

pytestmark = pytest.mark.skipif(
    not os.getenv("REDIS_URL"),
    reason="REDIS_URL required for Redis tests",
)


@pytest.fixture
async def redis_init():
    """Initialize Redis client for tests. Requires REDIS_URL in env."""
    from app.redis_client import close_redis, init_redis

    init_redis()
    yield
    await close_redis()


@pytest.mark.asyncio
async def test_ensure_consumer_group_idempotence(redis_init):
    """ensure_consumer_group can be called multiple times without error."""
    from app.redis_client import ensure_consumer_group

    await ensure_consumer_group()
    await ensure_consumer_group()


@pytest.mark.asyncio
async def test_enqueue_run_and_consume_run_job(redis_init):
    """enqueue_run adds job; consume_run_job returns it."""
    from app.redis_client import consume_run_job, enqueue_run

    run_id = str(uuid.uuid4())
    test_id = str(uuid.uuid4())
    entry_id = await enqueue_run(run_id, test_id)
    assert entry_id

    consumer = f"test-{uuid.uuid4().hex[:8]}"
    job = await consume_run_job(consumer, block_ms=2000)
    assert job is not None
    assert job["run_id"] == run_id
    assert job["test_id"] == test_id
    assert "msg_id" in job


@pytest.mark.asyncio
async def test_consume_run_job_empty_queue(redis_init):
    """consume_run_job returns None when queue is empty (after drain or no jobs)."""
    from app.redis_client import consume_run_job

    consumer = f"test-empty-{uuid.uuid4().hex[:8]}"
    # Short block; queue may have pending jobs from other tests, so we drain once
    job = await consume_run_job(consumer, block_ms=100)
    # If we got a job, drain until empty
    while job:
        job = await consume_run_job(consumer, block_ms=100)
    # Now queue should be empty
    job = await consume_run_job(consumer, block_ms=100)
    assert job is None


@pytest.mark.asyncio
async def test_append_run_event_and_read_run_events(redis_init):
    """append_run_event adds events; read_run_events returns them in order."""
    from app.redis_client import append_run_event, read_run_events

    run_id = str(uuid.uuid4())
    await append_run_event(run_id, "log", {"message": "first"})
    await append_run_event(run_id, "log", {"message": "second"})
    await append_run_event(run_id, "complete", {"status": "passed"})

    events = await read_run_events(run_id, after_id="0")
    assert len(events) == 3
    assert events[0][1]["type"] == "log"
    assert events[0][1]["data"]["message"] == "first"
    assert events[1][1]["data"]["message"] == "second"
    assert events[2][1]["type"] == "complete"
    assert events[2][1]["data"]["status"] == "passed"


@pytest.mark.asyncio
async def test_read_run_events_empty(redis_init):
    """read_run_events returns empty list for non-existent run."""
    from app.redis_client import read_run_events

    run_id = str(uuid.uuid4())
    events = await read_run_events(run_id)
    assert events == []


@pytest.mark.asyncio
async def test_read_run_events_after_id(redis_init):
    """read_run_events respects after_id for incremental reads."""
    from app.redis_client import append_run_event, read_run_events

    run_id = str(uuid.uuid4())
    await append_run_event(run_id, "log", {"n": 1})
    await append_run_event(run_id, "log", {"n": 2})

    events = await read_run_events(run_id, after_id="0")
    first_id = events[0][0]
    after_events = await read_run_events(run_id, after_id=first_id)
    assert len(after_events) == 1
    assert after_events[0][1]["data"]["n"] == 2


@pytest.mark.asyncio
async def test_results_stream_sse_emits_events_and_terminates_on_complete(redis_init):
    """GET /results/{run_id}/stream emits SSE events in order and terminates on complete."""
    import json

    from httpx import ASGITransport, AsyncClient

    from app.main import app
    from app.redis_client import append_run_event

    run_id = str(uuid.uuid4())
    await append_run_event(run_id, "log", {"message": "step 1"})
    await append_run_event(run_id, "log", {"message": "step 2"})
    await append_run_event(run_id, "complete", {"status": "passed"})

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        events = []
        current = {}
        async with client.stream("GET", f"/results/{run_id}/stream") as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")
            async for line in response.aiter_lines():
                if line.startswith("event:"):
                    current = {"type": line.split(":", 1)[1].strip()}
                elif line.startswith("data:"):
                    current["data"] = json.loads(line.split(":", 1)[1].strip())
                    events.append(current)
        assert len(events) == 3
        assert events[0]["type"] == "log"
        assert events[0]["data"]["data"]["message"] == "step 1"
        assert events[1]["type"] == "log"
        assert events[1]["data"]["data"]["message"] == "step 2"
        assert events[2]["type"] == "complete"
        assert events[2]["data"]["data"]["status"] == "passed"
