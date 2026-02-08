#!/usr/bin/env python3
"""Run worker: consumes jobs from runs:queue, executes tests, emits events."""

import asyncio
import os
import sys
import uuid
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()


async def process_job(run_id: str, test_id: str) -> None:
    """Process one run job. Stub: emit start + complete. Full agent in later ticket."""
    from app.database import get_connection
    from app.redis_client import append_run_event

    await append_run_event(run_id, "log", {"message": "Worker started run"})
    await append_run_event(run_id, "log", {"message": "Loading test definition..."})

    async with get_connection() as conn:
        test_row = await conn.fetchrow(
            "SELECT name, url, definition FROM tests WHERE id = $1",
            uuid.UUID(test_id),
        )
    if not test_row:
        await append_run_event(run_id, "error", {"message": "Test not found"})
        return

    await append_run_event(
        run_id,
        "log",
        {"message": f"Running test: {test_row['name']} at {test_row['url']}"},
    )

    # Stub: no Playwright execution yet. Emit complete.
    await append_run_event(
        run_id,
        "complete",
        {"status": "passed", "duration_ms": 0, "message": "Stub run (no Playwright yet)"},
    )

    async with get_connection() as conn:
        await conn.execute(
            """
            UPDATE test_runs
            SET status = 'passed', duration_ms = 0
            WHERE id = $1
            """,
            uuid.UUID(run_id),
        )


async def main() -> None:
    """Main worker loop: poll runs:queue and process jobs."""
    from app.database import init_db
    from app.redis_client import consume_run_job, init_redis

    init_redis()
    await init_db()

    from app.redis_client import is_redis_available

    if not is_redis_available():
        print("ERROR: Redis not configured (REDIS_URL)")
        sys.exit(1)

    from app.redis_client import ensure_consumer_group

    await ensure_consumer_group()
    print("Worker started. Polling runs:queue...")
    while True:
        job = await consume_run_job()
        if job:
            run_id = job["run_id"]
            test_id = job["test_id"]
            print(f"Processing run_id={run_id} test_id={test_id}")
            try:
                await process_job(run_id, test_id)
            except Exception as e:
                print(f"ERROR processing {run_id}: {e}")
                from app.redis_client import append_run_event

                await append_run_event(run_id, "error", {"message": str(e)})
                from app.database import get_connection

                async with get_connection() as conn:
                    await conn.execute(
                        """
                        UPDATE test_runs
                        SET status = 'failed', error = $1
                        WHERE id = $2
                        """,
                        str(e),
                        uuid.UUID(run_id),
                    )
        else:
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
