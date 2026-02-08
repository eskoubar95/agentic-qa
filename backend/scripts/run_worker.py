#!/usr/bin/env python3
"""Run worker: consumes jobs from runs:queue, executes tests, emits events."""

import asyncio
import json
import os
import sys
import time
import uuid
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()


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
    from app.database import init_db
    from app.redis_client import consume_run_job, init_redis

    init_redis()
    await init_db()

    from app.redis_client import is_redis_available

    if not is_redis_available():
        print("ERROR: Redis not configured (REDIS_URL)")
        sys.exit(1)

    from app.redis_client import ensure_consumer_group

    consumer_name = os.getenv(
        "REDIS_CONSUMER_NAME",
        f"worker-{os.getpid()}-{uuid.uuid4().hex[:8]}",
    )

    await ensure_consumer_group()
    print("Worker started. Polling runs:queue...")
    while True:
        job = await consume_run_job(consumer_name)
        if job:
            run_id = job["run_id"]
            test_id = job["test_id"]
            print(f"Processing run_id={run_id} test_id={test_id}")
            job_start = time.perf_counter()
            try:
                await process_job(run_id, test_id)
            except Exception as e:
                print(f"ERROR processing {run_id}: {e}")
                from app.redis_client import append_run_event

                await append_run_event(run_id, "error", {"message": str(e)})
                from app.database import get_connection

                duration_ms = int((time.perf_counter() - job_start) * 1000)
                async with get_connection() as conn:
                    await conn.execute(
                        """
                        UPDATE test_runs
                        SET status = 'failed', error = $1,
                            completed_at = NOW(), duration_ms = $2
                        WHERE id = $3
                        """,
                        str(e),
                        duration_ms,
                        uuid.UUID(run_id),
                    )
        else:
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
