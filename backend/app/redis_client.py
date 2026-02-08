"""Redis client for job queue and run events stream (Railway / standard Redis)."""

import asyncio
import json
import time
from typing import Any

from app.config import get_settings

redis_client: Any = None

RUNS_QUEUE = "runs:queue"
CONSUMER_GROUP = "run-workers"


async def close_redis() -> None:
    """Close Redis connection on shutdown."""
    global redis_client
    if redis_client:
        await redis_client.aclose()
        redis_client = None


def init_redis() -> None:
    """Initialize Redis client from REDIS_URL. Skips if not set."""
    global redis_client
    url = get_settings().REDIS_URL
    if not url:
        return
    # Railway Redis proxy: disable cert verification to avoid SSL handshake timeout
    # (proxy uses cert that may not validate from local/hosted clients)
    from urllib.parse import urlparse, urlunparse

    from redis.asyncio import Redis

    parsed = urlparse(url)
    if parsed.scheme == "rediss":
        query = parsed.query or ""
        params = f"ssl_cert_reqs=none&{query}" if query else "ssl_cert_reqs=none"
        url = urlunparse(parsed._replace(query=params))

    redis_client = Redis.from_url(
        url,
        decode_responses=True,
        socket_connect_timeout=30,
        health_check_interval=10,
    )


def _ensure_redis() -> Any:
    if redis_client is None:
        raise RuntimeError("Redis not initialized (REDIS_URL missing)")
    return redis_client


async def enqueue_run(run_id: str, test_id: str) -> str:
    """Add run job to runs:queue. Returns stream entry ID."""
    r = _ensure_redis()
    entry_id = await r.xadd(RUNS_QUEUE, {"run_id": run_id, "test_id": str(test_id)})
    return entry_id or ""


async def ensure_consumer_group() -> None:
    """Create consumer group on runs:queue if not exists."""
    r = _ensure_redis()
    try:
        await r.xgroup_create(RUNS_QUEUE, CONSUMER_GROUP, id="0", mkstream=True)
    except Exception as e:
        if "BUSYGROUP" not in str(e):
            raise


async def consume_run_job(consumer_name: str, block_ms: int = 5000) -> dict | None:
    """
    Consume one job from runs:queue via consumer group.
    Uses blocking XREADGROUP for efficient waiting (no polling).
    Does NOT ack the message; caller must call ack_run_job(msg_id) after successful processing.
    Returns {"run_id": str, "test_id": str, "msg_id": str} or None if no job.
    """
    r = _ensure_redis()
    result = await r.xreadgroup(
        groupname=CONSUMER_GROUP,
        consumername=consumer_name,
        streams={RUNS_QUEUE: ">"},
        count=1,
        block=block_ms,
    )
    if not result:
        return None
    stream_name, entries = result[0]
    if not entries:
        return None
    msg_id, fields = entries[0]
    return {
        "run_id": fields.get("run_id", ""),
        "test_id": fields.get("test_id", ""),
        "msg_id": msg_id,
    }


async def ack_run_job(msg_id: str) -> None:
    """Ack a run job message after successful processing. Call only after process_job completes successfully."""
    r = _ensure_redis()
    await r.xack(RUNS_QUEUE, CONSUMER_GROUP, msg_id)


async def append_run_event(run_id: str, event_type: str, data: dict) -> str:
    """Append event to run_events:{run_id} stream. Returns entry ID."""
    r = _ensure_redis()
    stream_key = f"run_events:{run_id}"
    data_str = json.dumps(data) if isinstance(data, (dict, list)) else str(data)
    entry_id = await r.xadd(
        stream_key,
        {
            "type": event_type,
            "timestamp": str(time.time()),
            "data": data_str,
        },
    )
    return entry_id or ""


async def read_run_events(
    run_id: str, after_id: str = "0", count: int = 100
) -> list[tuple[str, dict]]:
    """
    Read events from run_events:{run_id} after given ID.
    Returns list of (entry_id, {type, timestamp, data}).
    """
    r = _ensure_redis()
    stream_key = f"run_events:{run_id}"
    result = await r.xread(streams={stream_key: after_id}, count=count)
    if not result:
        return []
    events = []
    _, entries = result[0]
    for entry_id, fields in entries:
        raw = fields.get("data", "{}")
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError:
            data = {"raw": raw}
        events.append(
            (
                entry_id,
                {
                    "type": fields.get("type", "log"),
                    "timestamp": float(fields.get("timestamp", 0)),
                    "data": data,
                },
            )
        )
    return events


def is_redis_available() -> bool:
    """Return True if Redis client is initialized."""
    return redis_client is not None


async def redis_ping() -> bool:
    """Verify Redis connectivity with ping. Returns False if uninit or ping fails."""
    if redis_client is None:
        return False
    try:
        await asyncio.wait_for(redis_client.ping(), timeout=2.0)
        return True
    except Exception:
        return False
