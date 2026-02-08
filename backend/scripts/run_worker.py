#!/usr/bin/env python3
"""Run worker: consumes jobs from runs:queue, executes tests, emits events."""

import asyncio
import json
import logging
import os
import signal
import socket
import sys
import time
import uuid
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

# Graceful shutdown: set by signal handlers so loop exits cleanly
shutdown_event: asyncio.Event | None = None

# Worker stats for health monitoring
jobs_processed = 0
jobs_failed = 0
total_processing_time_ms = 0.0
worker_start_time = 0.0
last_heartbeat_time = 0.0
last_health_log_time = 0.0

# Config from env (used by recovery and main loop)
STUCK_RUN_TIMEOUT_MINUTES = int(os.getenv("STUCK_RUN_TIMEOUT_MINUTES", os.getenv("STUCK_RUN_TIMEOUT_MIN", "10")))
RECOVERY_CHECK_INTERVAL_SECONDS = int(os.getenv("RECOVERY_CHECK_INTERVAL_SECONDS", "300"))  # 5 min default
HEARTBEAT_IDLE_SECONDS = 30
HEALTH_LOG_INTERVAL_SECONDS = 300

logger = logging.getLogger("worker")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)


def handle_shutdown(signum: int | None, frame: object | None) -> None:
    """Signal handler: set shutdown event so loop exits cleanly."""
    if shutdown_event is not None:
        shutdown_event.set()
    sig_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
    logger.info("Shutdown requested via %s", sig_name)


async def recover_stuck_runs() -> None:
    """One pass: find test_runs stuck in 'running' > timeout, mark failed, emit error event."""
    from app.database import get_connection
    from app.redis_client import append_run_event

    timeout_min = int(os.getenv("STUCK_RUN_TIMEOUT_MINUTES", "10"))
    interval_sec = timeout_min * 60
    async with get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT id FROM test_runs
            WHERE status = 'running'
              AND started_at < NOW() - ($1::text || ' seconds')::interval
            """,
            interval_sec,
        )
        for row in rows:
            await conn.execute(
                """
                UPDATE test_runs
                SET status = 'failed', error = 'Stuck - timeout', completed_at = NOW()
                WHERE id = $1
                """,
                row["id"],
            )
            await append_run_event(
                str(row["id"]),
                "error",
                {"message": "Stuck run recovered - timeout"},
            )
            logger.warning("Recovered stuck run run_id=%s", row["id"])


async def recover_stuck_runs_periodically(interval_sec: int = 300) -> None:
    """Loop: call recover_stuck_runs() then sleep(interval_sec) until shutdown."""
    try:
        while shutdown_event is not None and not shutdown_event.is_set():
            await recover_stuck_runs()
            await asyncio.sleep(interval_sec)
    except asyncio.CancelledError:
        pass


def _is_transient_error(exc: BaseException) -> bool:
    """Return True if the exception is a transient DB/Redis connection error."""
    try:
        import asyncpg
        from redis import exceptions as redis_exc
    except ImportError:
        return False
    return isinstance(
        exc,
        (
            asyncpg.InterfaceError,
            asyncpg.ConnectionDoesNotExistError,
            asyncpg.ConnectionFailureError,
            OSError,
            redis_exc.ConnectionError,
            redis_exc.TimeoutError,
        ),
    )


async def process_job(run_id: str, test_id: str) -> None:
    """Process one run job: fetch test, run AgentExecutor with Playwright."""
    from app.agent.executor import AgentExecutor
    from app.database import get_connection
    from app.redis_client import append_run_event

    async with get_connection() as conn:
        test_row = await conn.fetchrow(
            "SELECT name, url, definition FROM tests WHERE id = $1",
            uuid.UUID(test_id),
        )
    if not test_row:
        await append_run_event(run_id, "error", {"message": "Test not found"})
        async with get_connection() as conn:
            await conn.execute(
                """
                UPDATE test_runs
                SET status = 'failed', error = $1, completed_at = NOW(), duration_ms = 0
                WHERE id = $2
                """,
                "Test not found",
                uuid.UUID(run_id),
            )
        return

    definition = test_row["definition"]
    if isinstance(definition, str):
        try:
            definition = json.loads(definition) if definition else {}
        except json.JSONDecodeError:
            definition = {}
    elif definition is None:
        definition = {}

    executor = AgentExecutor(
        run_id=run_id,
        test_definition=definition,
        test_url=test_row["url"] or "",
        test_name=test_row["name"] or "Test",
    )
    await executor.execute_test()


async def main() -> None:
    """Main worker loop: poll runs:queue and process jobs."""
    global shutdown_event, worker_start_time, last_heartbeat_time, last_health_log_time
    global jobs_processed, jobs_failed, total_processing_time_ms
    shutdown_event = asyncio.Event()
    from app.database import close_db, init_db
    from app.redis_client import (
        CONSUMER_GROUP,
        RUNS_QUEUE,
        _ensure_redis,
        close_redis,
        consume_run_job,
        ensure_consumer_group,
        init_redis,
    )

    init_redis()
    await init_db()

    from app.redis_client import is_redis_available

    if not is_redis_available():
        logger.error("Redis not configured (REDIS_URL)")
        sys.exit(1)

    # Consumer name: hostname-pid-uuid for multi-worker uniqueness
    hostname = os.getenv("HOSTNAME") or socket.gethostname()
    consumer_name = os.getenv(
        "REDIS_CONSUMER_NAME",
        f"worker-{hostname}-{os.getpid()}-{uuid.uuid4().hex[:8]}",
    )

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handle_shutdown)

    # Ensure consumer group (Phase 5) with error handling
    try:
        await ensure_consumer_group()
    except Exception as e:
        logger.exception("Failed to ensure consumer group: %s", e)
        sys.exit(1)

    # Startup logging (Phase 4)
    worker_start_time = time.monotonic()
    last_heartbeat_time = worker_start_time
    last_health_log_time = worker_start_time
    has_redis = bool(os.getenv("REDIS_URL"))
    has_db = bool(os.getenv("DATABASE_URL"))
    logger.info(
        "Worker started. consumer=%s redis_configured=%s database_configured=%s",
        consumer_name,
        has_redis,
        has_db,
    )
    logger.info(
        "Config: STUCK_RUN_TIMEOUT_MINUTES=%s RECOVERY_CHECK_INTERVAL_SECONDS=%s",
        STUCK_RUN_TIMEOUT_MINUTES,
        RECOVERY_CHECK_INTERVAL_SECONDS,
    )

    # Start stuck run recovery task (runs every 300s / RECOVERY_CHECK_INTERVAL_SECONDS)
    recovery_task = asyncio.create_task(
        recover_stuck_runs_periodically(RECOVERY_CHECK_INTERVAL_SECONDS)
    )

    try:
        while not shutdown_event.is_set():
            job = await consume_run_job(consumer_name)
            if job:
                run_id = job["run_id"]
                test_id = job["test_id"]
                logger.info("Processing run_id=%s test_id=%s", run_id, test_id)
                job_start = time.perf_counter()
                last_heartbeat_time = time.monotonic()

                # Phase 3: broad try/except, retry for transient errors, always update DB on failure
                last_exc: BaseException | None = None
                failure_handled_in_loop = False
                for attempt in range(3):
                    try:
                        await process_job(run_id, test_id)
                        jobs_processed += 1
                        total_processing_time_ms += (time.perf_counter() - job_start) * 1000
                        r = _ensure_redis()
                        await r.xack(RUNS_QUEUE, CONSUMER_GROUP, job["msg_id"])
                        break
                    except Exception as e:
                        last_exc = e
                        if attempt < 2 and _is_transient_error(e) and not shutdown_event.is_set():
                            delay = 2**attempt
                            logger.warning(
                                "Transient error run_id=%s attempt=%s: %s; retry in %ss",
                                run_id,
                                attempt + 1,
                                e,
                                delay,
                            )
                            await asyncio.sleep(delay)
                        else:
                            break
                else:
                    # Exhausted 3 attempts (all transient)
                    if last_exc:
                        logger.error(
                            "run_id=%s test_id=%s failed after 3 attempts: %s",
                            run_id,
                            test_id,
                            last_exc,
                            exc_info=True,
                        )
                        from app.redis_client import append_run_event

                        await append_run_event(run_id, "error", {"message": str(last_exc)})
                        duration_ms = int((time.perf_counter() - job_start) * 1000)
                        from app.database import get_connection

                        async with get_connection() as conn:
                            await conn.execute(
                                """
                                UPDATE test_runs
                                SET status = 'failed', error = $1,
                                    completed_at = NOW(), duration_ms = $2
                                WHERE id = $3
                                """,
                                str(last_exc),
                                duration_ms,
                                uuid.UUID(run_id),
                            )
                        jobs_failed += 1
                        failure_handled_in_loop = True

                # Non-transient failure on attempt 0 or 1 (broke out before exhausting retries)
                if last_exc and not failure_handled_in_loop and not _is_transient_error(last_exc):
                    logger.error(
                        "run_id=%s test_id=%s error: %s",
                        run_id,
                        test_id,
                        last_exc,
                        exc_info=True,
                    )
                    from app.redis_client import append_run_event

                    await append_run_event(run_id, "error", {"message": str(last_exc)})
                    duration_ms = int((time.perf_counter() - job_start) * 1000)
                    from app.database import get_connection

                    try:
                        async with get_connection() as conn:
                            await conn.execute(
                                """
                                UPDATE test_runs
                                SET status = 'failed', error = $1,
                                    completed_at = NOW(), duration_ms = $2
                                WHERE id = $3
                                """,
                                str(last_exc),
                                duration_ms,
                                uuid.UUID(run_id),
                            )
                    except Exception as db_err:
                        logger.exception("Failed to update test_runs on error: %s", db_err)
                    jobs_failed += 1
            else:
                now = time.monotonic()
                # Idle heartbeat every 30s (Phase 4)
                if now - last_heartbeat_time >= HEARTBEAT_IDLE_SECONDS:
                    logger.info("Worker idle heartbeat")
                    last_heartbeat_time = now
                # Health log every 5 min
                if now - last_health_log_time >= HEALTH_LOG_INTERVAL_SECONDS:
                    uptime_sec = int(now - worker_start_time)
                    avg_ms = int(total_processing_time_ms / jobs_processed) if jobs_processed else 0
                    logger.info(
                        "Health uptime_sec=%s jobs_processed=%s jobs_failed=%s avg_ms=%s",
                        uptime_sec,
                        jobs_processed,
                        jobs_failed,
                        avg_ms,
                    )
                    last_health_log_time = now
                await asyncio.sleep(1)
    finally:
        recovery_task.cancel()
        try:
            await recovery_task
        except asyncio.CancelledError:
            pass
        logger.info("Shutting down: closing database and Redis connections")
        try:
            await close_db()
        except Exception:
            logger.exception("Error closing database")
        try:
            await close_redis()
        except Exception:
            logger.exception("Error closing Redis")
        logger.info("Worker stopped")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
