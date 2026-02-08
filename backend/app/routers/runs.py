"""Run test and results API."""

import asyncio
import json
import uuid
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from app.database import get_connection
from app.redis_client import (
    append_run_event,
    enqueue_run,
    init_redis,
    is_redis_available,
    read_run_events,
)
from app.schemas import RunTestRequest, RunTestResponse, TestRunResponse

router = APIRouter(tags=["runs"])


def _row_to_test_run_response(row) -> TestRunResponse:
    """Convert DB row to TestRunResponse."""
    return TestRunResponse(
        id=row["id"],
        test_id=row["test_id"],
        status=row["status"],
        started_at=row["started_at"].isoformat() if row["started_at"] else None,
        completed_at=row["completed_at"].isoformat() if row["completed_at"] else None,
        duration_ms=row["duration_ms"],
        screenshots=dict(row["screenshots"]) if row["screenshots"] else None,
        logs=dict(row["logs"]) if row["logs"] else None,
        step_results=row["step_results"] or [],
        self_healed=row["self_healed"] or False,
        llm_calls=row["llm_calls"] or 0,
        cost_usd=float(row["cost_usd"] or 0),
        error=row["error"],
        error_step=row["error_step"],
        created_at=row["created_at"].isoformat(),
    )


@router.post("/test/run", response_model=RunTestResponse)
async def run_test(payload: RunTestRequest):
    """Create test_run (queued), enqueue job to Redis, return run_id."""
    if not is_redis_available():
        raise HTTPException(
            status_code=503,
            detail="Redis not available (REDIS_URL required)",
        )
    async with get_connection() as conn:
        test_row = await conn.fetchrow(
            "SELECT id FROM tests WHERE id = $1",
            payload.test_id,
        )
    if not test_row:
        raise HTTPException(status_code=404, detail="Test not found")
    run_id = uuid.uuid4()
    async with get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO test_runs (id, test_id, status)
            VALUES ($1, $2, 'queued')
            """,
            run_id,
            payload.test_id,
        )
    await enqueue_run(str(run_id), str(payload.test_id))
    return RunTestResponse(run_id=run_id)


@router.get("/results/{run_id}", response_model=TestRunResponse)
async def get_result(run_id: UUID):
    """Get test run by ID."""
    async with get_connection() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM test_runs WHERE id = $1",
            run_id,
        )
    if not row:
        raise HTTPException(status_code=404, detail="Run not found")
    return _row_to_test_run_response(row)


@router.get("/results/{run_id}/stream")
async def stream_results(run_id: UUID, request: Request):
    """SSE stream of run events. Supports Last-Event-ID for resume."""
    if not is_redis_available():
        raise HTTPException(
            status_code=503,
            detail="Redis not available for event stream",
        )

    async def event_generator():
        last_id = request.headers.get("Last-Event-ID", "0")
        seen_complete = False
        while not seen_complete:
            if await request.is_disconnected():
                return
            events = await read_run_events(str(run_id), after_id=last_id)
            for entry_id, evt in events:
                last_id = entry_id
                data = {
                    "type": evt["type"],
                    "timestamp": evt["timestamp"],
                    "data": evt["data"],
                }
                yield {
                    "event": evt["type"],
                    "id": entry_id,
                    "data": json.dumps(data),
                }
                if evt["type"] == "complete" or evt["type"] == "error":
                    seen_complete = True
                    break
            if not events:
                await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())
