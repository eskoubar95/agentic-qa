"""Database CRUD tests for tests, test_runs, session_memory tables."""

import os
import uuid

import pytest

from app.database import get_connection

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL required for database tests",
)


@pytest.fixture(scope="module")
async def db_pool():
    """Initialize DB pool for tests. Requires DATABASE_URL in env."""
    from app.database import close_db, init_db, pool

    await init_db()
    yield pool
    await close_db()


@pytest.mark.asyncio
async def test_tests_crud(db_pool):
    """tests table: INSERT, SELECT, UPDATE, DELETE."""
    user_id = uuid.uuid4()
    async with get_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO tests (user_id, name, url, definition, auto_handle_popups)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, name, url, definition
            """,
            user_id,
            "Test CRUD",
            "https://example.com",
            '{"steps": [{"action": "navigate", "instruction": "go"}]}',
            True,
        )
    assert row["name"] == "Test CRUD"
    assert row["url"] == "https://example.com"
    test_id = row["id"]

    async with get_connection() as conn:
        row = await conn.fetchrow("SELECT * FROM tests WHERE id = $1", test_id)
    assert row["name"] == "Test CRUD"

    async with get_connection() as conn:
        await conn.execute("UPDATE tests SET name = $1 WHERE id = $2", "Updated Name", test_id)
    async with get_connection() as conn:
        row = await conn.fetchrow("SELECT name FROM tests WHERE id = $1", test_id)
    assert row["name"] == "Updated Name"

    async with get_connection() as conn:
        await conn.execute("DELETE FROM tests WHERE id = $1", test_id)
    async with get_connection() as conn:
        row = await conn.fetchrow("SELECT id FROM tests WHERE id = $1", test_id)
    assert row is None


@pytest.mark.asyncio
async def test_test_runs_crud(db_pool):
    """test_runs table: INSERT with FK, SELECT, UPDATE, DELETE cascade."""
    user_id = uuid.uuid4()
    async with get_connection() as conn:
        test_row = await conn.fetchrow(
            """
            INSERT INTO tests (user_id, name, url, definition)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            user_id,
            "Run Test",
            "https://example.com",
            "{}",
        )
    test_id = test_row["id"]

    async with get_connection() as conn:
        run_row = await conn.fetchrow(
            """
            INSERT INTO test_runs (test_id, status, step_results)
            VALUES ($1, $2, $3)
            RETURNING id, test_id, status
            """,
            test_id,
            "passed",
            '[{"step": 1, "status": "passed"}]',
        )
    assert run_row["test_id"] == test_id
    assert run_row["status"] == "passed"
    run_id = run_row["id"]

    async with get_connection() as conn:
        await conn.execute("UPDATE test_runs SET status = $1 WHERE id = $2", "failed", run_id)
    async with get_connection() as conn:
        row = await conn.fetchrow("SELECT status FROM test_runs WHERE id = $1", run_id)
    assert row["status"] == "failed"

    async with get_connection() as conn:
        await conn.execute("DELETE FROM tests WHERE id = $1", test_id)
    async with get_connection() as conn:
        row = await conn.fetchrow("SELECT id FROM test_runs WHERE id = $1", run_id)
    assert row is None


@pytest.mark.asyncio
async def test_session_memory_crud(db_pool):
    """session_memory table: INSERT with unique hash, SELECT, UPDATE reliability."""
    import hashlib

    instruction = "Click the submit button"
    instruction_hash = hashlib.sha256(instruction.encode()).hexdigest()
    async with get_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO session_memory (instruction_hash, page_url, instruction, action_data, reliability_score)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (instruction_hash) DO UPDATE SET
                reliability_score = EXCLUDED.reliability_score,
                last_used = NOW()
            RETURNING id, instruction_hash, reliability_score
            """,
            instruction_hash,
            "https://example.com/form",
            instruction,
            '{"selector": "button[type=submit]", "strategy": "dom"}',
            0.95,
        )
    assert row["instruction_hash"] == instruction_hash
    mem_id = row["id"]

    async with get_connection() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM session_memory WHERE instruction_hash = $1", instruction_hash
        )
    assert row["reliability_score"] == 0.95

    async with get_connection() as conn:
        await conn.execute(
            "UPDATE session_memory SET reliability_score = $1 WHERE id = $2",
            0.8,
            mem_id,
        )
    async with get_connection() as conn:
        row = await conn.fetchrow(
            "SELECT reliability_score FROM session_memory WHERE id = $1", mem_id
        )
    assert row["reliability_score"] == 0.8

    async with get_connection() as conn:
        await conn.execute("DELETE FROM session_memory WHERE id = $1", mem_id)
    async with get_connection() as conn:
        row = await conn.fetchrow("SELECT id FROM session_memory WHERE id = $1", mem_id)
    assert row is None


@pytest.mark.asyncio
async def test_jsonb_operations(db_pool):
    """JSONB columns: insert and query complex JSON in definition, step_results."""
    user_id = uuid.uuid4()
    definition = {
        "steps": [
            {"action": "click", "instruction": "Click login", "advanced_selector": "#login"},
            {"action": "fill", "instruction": "Enter email", "target": "email", "value": "x@y.z"},
        ]
    }
    async with get_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO tests (user_id, name, url, definition)
            VALUES ($1, $2, $3, $4)
            RETURNING definition
            """,
            user_id,
            "JSONB Test",
            "https://example.com",
            definition,
        )
    assert row["definition"]["steps"][0]["action"] == "click"
    assert row["definition"]["steps"][1]["target"] == "email"

    async with get_connection() as conn:
        test_row = await conn.fetchrow("SELECT id FROM tests WHERE user_id = $1", user_id)
        test_id = test_row["id"]
        await conn.execute("DELETE FROM tests WHERE id = $1", test_id)
