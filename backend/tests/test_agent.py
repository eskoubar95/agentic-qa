"""Tests for agent executor and actions."""

from unittest.mock import AsyncMock

import pytest

from app.agent.actions import (
    execute_click,
    execute_fill,
    execute_navigate,
    execute_verify,
)
from app.agent.executor import AgentExecutor, _validate_step

# --- Step validation ---


def test_validate_step_missing_action():
    assert _validate_step({}, 0) == "Step 1: missing 'action'"


def test_validate_step_unknown_action():
    assert _validate_step({"action": "foo"}, 0) == "Step 1: unknown action 'foo'"


def test_validate_step_click_missing_selector():
    assert "advanced_selector" in (_validate_step({"action": "click"}, 0) or "")


def test_validate_step_fill_missing_value():
    assert "value" in (_validate_step({"action": "fill", "advanced_selector": "#x"}, 0) or "")


def test_validate_step_verify_missing_expected():
    assert "expected" in (_validate_step({"action": "verify"}, 0) or "")


def test_validate_step_navigate_valid():
    assert _validate_step({"action": "navigate", "target": "https://example.com"}, 0) is None


def test_validate_step_click_valid():
    assert _validate_step({"action": "click", "advanced_selector": "#btn"}, 0) is None


def test_validate_step_fill_valid():
    assert _validate_step({"action": "fill", "advanced_selector": "#x", "value": "y"}, 0) is None


def test_validate_step_verify_valid():
    assert _validate_step({"action": "verify", "expected": "Welcome"}, 0) is None


# --- Action execution (mocked page) ---


@pytest.mark.asyncio
async def test_execute_navigate_success():
    page = AsyncMock()
    page.goto = AsyncMock()
    result = await execute_navigate(page, {"target": "https://example.com"}, "")
    assert result["status"] == "passed"
    page.goto.assert_called_once_with(
        "https://example.com", wait_until="domcontentloaded", timeout=30000
    )


@pytest.mark.asyncio
async def test_execute_navigate_uses_base_url_when_target_empty():
    page = AsyncMock()
    page.goto = AsyncMock()
    result = await execute_navigate(page, {}, "https://fallback.com")
    assert result["status"] == "passed"
    page.goto.assert_called_once_with(
        "https://fallback.com", wait_until="domcontentloaded", timeout=30000
    )


@pytest.mark.asyncio
async def test_execute_click_success():
    page = AsyncMock()
    page.click = AsyncMock()
    result = await execute_click(page, {"advanced_selector": "#submit"})
    assert result["status"] == "passed"
    page.click.assert_called_once_with("#submit", timeout=30000)


@pytest.mark.asyncio
async def test_execute_fill_success():
    page = AsyncMock()
    page.fill = AsyncMock()
    result = await execute_fill(page, {"advanced_selector": "#email", "value": "a@b.com"})
    assert result["status"] == "passed"
    page.fill.assert_called_once_with("#email", "a@b.com", timeout=30000)


@pytest.mark.asyncio
async def test_execute_verify_success():
    page = AsyncMock()
    page.content = AsyncMock(return_value="<html><body>Welcome user</body></html>")
    result = await execute_verify(page, {"expected": "Welcome user"})
    assert result["status"] == "passed"


@pytest.mark.asyncio
async def test_execute_verify_failure():
    page = AsyncMock()
    page.content = AsyncMock(return_value="<html><body>Hello</body></html>")
    result = await execute_verify(page, {"expected": "Goodbye"})
    assert result["status"] == "failed"
    assert "error" in result


# --- Executor integration (requires Redis, DB, Playwright) ---


@pytest.mark.skipif(
    not __import__("os").getenv("DATABASE_URL"),
    reason="DATABASE_URL required",
)
@pytest.mark.skipif(
    not __import__("os").getenv("REDIS_URL"),
    reason="REDIS_URL required",
)
@pytest.mark.asyncio
async def test_executor_navigate_only_integration():
    """Executor runs a simple navigate step without crashing."""
    import uuid
    from pathlib import Path

    from dotenv import load_dotenv

    from app.database import get_connection, init_db
    from app.redis_client import init_redis

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    init_redis()
    await init_db()

    run_id = str(uuid.uuid4())
    test_id = None
    async with get_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO tests (user_id, name, url, definition)
            VALUES ($1, 'Agent test', 'https://example.com',
                    '{"steps": [{"action": "navigate", "instruction": "Go to example", "target": "https://example.com"}]}'::jsonb)
            RETURNING id
            """,
            uuid.UUID("00000000-0000-0000-0000-000000000001"),
        )
        test_id = row["id"]
        await conn.execute(
            "INSERT INTO test_runs (id, test_id, status) VALUES ($1, $2, 'queued')",
            uuid.UUID(run_id),
            test_id,
        )

    executor = AgentExecutor(
        run_id=run_id,
        test_definition={
            "steps": [{"action": "navigate", "instruction": "Go", "target": "https://example.com"}]
        },
        test_url="https://example.com",
        test_name="Agent test",
    )
    result = await executor.execute_test()

    assert result["status"] == "passed"
    assert result["steps_completed"] == 1

    async with get_connection() as conn:
        row = await conn.fetchrow(
            "SELECT status, step_results FROM test_runs WHERE id = $1", uuid.UUID(run_id)
        )
        assert row["status"] == "passed"
        assert len(row["step_results"] or []) == 1
        assert row["step_results"][0]["status"] == "passed"
