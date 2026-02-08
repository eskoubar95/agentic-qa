"""Tests for agent executor and actions."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agent.actions import (
    execute_click,
    execute_fill,
    execute_navigate,
    execute_verify,
)
from app.agent.executor import AgentExecutor, _validate_step
from app.agent.strategies import (
    DOMStrategy,
    SelectorStrategy,
    VisionStrategy,
    determine_element_type,
    extract_target_text,
)

# --- Step validation ---


def test_validate_step_missing_action():
    assert _validate_step({}, 0) == "Step 1: missing 'action'"


def test_validate_step_unknown_action():
    assert _validate_step({"action": "foo"}, 0) == "Step 1: unknown action 'foo'"


def test_validate_step_click_missing_selector_and_instruction():
    err = _validate_step({"action": "click"}, 0)
    assert err is not None
    assert "advanced_selector" in err and "instruction" in err


def test_validate_step_fill_missing_value():
    assert "value" in (_validate_step({"action": "fill", "instruction": "Fill email"}, 0) or "")


def test_validate_step_verify_missing_expected():
    assert "expected" in (_validate_step({"action": "verify"}, 0) or "")


def test_validate_step_navigate_valid():
    assert _validate_step({"action": "navigate", "target": "https://example.com"}, 0) is None


def test_validate_step_click_valid():
    assert _validate_step({"action": "click", "instruction": "Click submit"}, 0) is None


def test_validate_step_click_valid_selector_only():
    assert _validate_step({"action": "click", "advanced_selector": "#btn"}, 0) is None


def test_validate_step_click_valid_with_selector():
    assert (
        _validate_step({"action": "click", "instruction": "Submit", "advanced_selector": "#btn"}, 0)
        is None
    )


def test_validate_step_fill_valid():
    assert _validate_step({"action": "fill", "instruction": "Email field", "value": "y"}, 0) is None


def test_validate_step_fill_valid_selector_only():
    assert _validate_step({"action": "fill", "advanced_selector": "#email", "value": "y"}, 0) is None


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
    result = await execute_click(page, {"instruction": "Submit", "advanced_selector": "#submit"})
    assert result["status"] == "passed"
    assert result["strategy"] == "selector"
    assert result["self_healed"] is False
    assert result["attempts"] == 1
    page.click.assert_called_once_with("#submit", timeout=30000)


@pytest.mark.asyncio
async def test_execute_fill_success():
    page = AsyncMock()
    page.fill = AsyncMock()
    result = await execute_fill(
        page, {"instruction": "Email", "advanced_selector": "#email", "value": "a@b.com"}
    )
    assert result["status"] == "passed"
    assert result["strategy"] == "selector"
    assert result["self_healed"] is False
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


# --- Strategy helpers ---


def test_extract_target_text():
    assert extract_target_text("click the Submit button") == "Submit button"
    assert extract_target_text("fill the email field") == "email field"
    assert extract_target_text("enter username") == "username"
    assert extract_target_text("") == ""
    assert extract_target_text("  the  link  ") == "link"


def test_determine_element_type():
    assert determine_element_type("click the button") == ("role", "button")
    assert determine_element_type("fill the input field") == ("label", "")
    assert determine_element_type("click the link") == ("role", "link")
    assert determine_element_type("click Submit") == ("text", "")


# --- Strategy classes ---


@pytest.mark.asyncio
async def test_selector_strategy_success():
    page = AsyncMock()
    page.click = AsyncMock()
    result = await SelectorStrategy.try_execute(
        page, {"advanced_selector": "#btn", "instruction": "Click"}, "click", ""
    )
    assert result is not None
    assert result["success"] is True
    assert result["strategy"] == "selector"
    assert result["self_healed"] is False
    page.click.assert_called_once_with("#btn", timeout=30000)


@pytest.mark.asyncio
async def test_selector_strategy_no_selector_returns_skipped():
    page = AsyncMock()
    result = await SelectorStrategy.try_execute(page, {"instruction": "Click button"}, "click", "")
    assert result is not None and result.get("skipped") is True


@pytest.mark.asyncio
async def test_selector_strategy_failure_returns_none():
    page = AsyncMock()
    page.click = AsyncMock(side_effect=Exception("not found"))
    result = await SelectorStrategy.try_execute(
        page, {"advanced_selector": "#missing", "instruction": "Click"}, "click", ""
    )
    assert result is None


@pytest.mark.asyncio
async def test_dom_strategy_button():
    page = MagicMock()
    locator = AsyncMock()
    locator.click = AsyncMock()
    page.get_by_role = MagicMock(return_value=locator)
    result = await DOMStrategy.try_execute(
        page, {"instruction": "click the Submit button"}, "click", ""
    )
    assert result is not None
    assert result["success"] is True
    assert result["strategy"] == "dom"
    assert result["self_healed"] is True
    page.get_by_role.assert_called_once_with("button", name="Submit button")
    locator.click.assert_called_once_with(timeout=30000)


@pytest.mark.asyncio
async def test_dom_strategy_label():
    page = MagicMock()
    locator = AsyncMock()
    locator.fill = AsyncMock()
    page.get_by_label = MagicMock(return_value=locator)
    result = await DOMStrategy.try_execute(
        page, {"instruction": "fill the email field", "value": "a@b.com"}, "fill", "a@b.com"
    )
    assert result is not None
    assert result["strategy"] == "dom"
    assert result["self_healed"] is True
    page.get_by_label.assert_called_once_with("email field")
    locator.fill.assert_called_once_with("a@b.com", timeout=30000)


@pytest.mark.asyncio
async def test_dom_strategy_text():
    page = MagicMock()
    locator = AsyncMock()
    locator.click = AsyncMock()
    page.get_by_text = MagicMock(return_value=locator)
    result = await DOMStrategy.try_execute(page, {"instruction": "click Welcome"}, "click", "")
    assert result is not None
    assert result["strategy"] == "dom"
    page.get_by_text.assert_called_once_with("Welcome")


@pytest.mark.asyncio
async def test_vision_strategy_placeholder_returns_none():
    page = AsyncMock()
    result = await VisionStrategy.try_execute(page, {"instruction": "click thing"}, "click", "")
    assert result is None


@pytest.mark.asyncio
async def test_execute_click_fallback_selector_fails_dom_succeeds():
    """Wrong selector fails; DOM strategy with instruction succeeds."""
    page = MagicMock()
    page.click = AsyncMock(side_effect=Exception("selector failed"))
    locator = AsyncMock()
    locator.click = AsyncMock()
    page.get_by_role = MagicMock(return_value=locator)
    result = await execute_click(
        page,
        {"instruction": "click the Submit button", "advanced_selector": "#wrong"},
    )
    assert result["status"] == "passed"
    assert result["strategy"] == "dom"
    assert result["self_healed"] is True
    assert result["attempts"] == 2


@pytest.mark.asyncio
async def test_execute_click_instruction_only_dom_succeeds():
    """Step with only instruction (no selector) can succeed via DOM."""
    page = MagicMock()
    locator = AsyncMock()
    locator.click = AsyncMock()
    page.get_by_text = MagicMock(return_value=locator)
    result = await execute_click(page, {"instruction": "click Login"})
    assert result["status"] == "passed"
    assert result["strategy"] == "dom"
    assert result["self_healed"] is False  # no prior attempt failed (selector was skipped)
    assert result["attempts"] == 1  # only DOM ran (selector skipped)


@pytest.mark.asyncio
async def test_execute_click_all_strategies_fail():
    page = MagicMock()
    page.click = AsyncMock(side_effect=Exception("fail"))
    locator = AsyncMock()
    locator.click = AsyncMock(side_effect=Exception("fail"))
    page.get_by_text = MagicMock(return_value=locator)
    result = await execute_click(page, {"instruction": "click Nonexistent"})
    assert result["status"] == "failed"
    assert "All strategies failed" in (result.get("error") or "")
    assert result["attempts"] == 2  # selector skipped; DOM and vision ran and failed


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
