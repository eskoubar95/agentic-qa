"""Action execution functions for Playwright steps."""

import logging
from typing import Any

from app.agent.constants import STEP_TIMEOUT_MS
from app.agent.strategies import DOMStrategy, SelectorStrategy, VisionStrategy

logger = logging.getLogger(__name__)

STRATEGY_CHAIN = [
    ("selector", SelectorStrategy),
    ("dom", DOMStrategy),
    ("vision", VisionStrategy),
]


async def _execute_with_fallback(
    page: Any, step: dict, action: str, value: str = ""
) -> dict:
    """Try each strategy in order; return on first success. Count only actual attempts; self_healed only when a prior attempt failed."""
    errors = []
    attempts = 0
    prior_attempted_and_failed = False
    for strategy_name, strategy_cls in STRATEGY_CHAIN:
        result = await strategy_cls.try_execute(page, step, action, value)
        if result and result.get("skipped"):
            continue
        if result and result.get("success"):
            attempts += 1
            return {
                "status": "passed",
                "strategy": result.get("strategy", strategy_name),
                "self_healed": prior_attempted_and_failed,
                "attempts": attempts,
                "error": None,
            }
        if result is None:
            prior_attempted_and_failed = True
        attempts += 1
        errors.append(f"{strategy_name}: failed")
    return {
        "status": "failed",
        "strategy": "unknown",
        "self_healed": False,
        "attempts": attempts,
        "error": "All strategies failed: " + "; ".join(errors),
    }


async def execute_navigate(page: Any, step: dict, base_url: str = "") -> dict:
    """Execute navigate action. Uses step['target'] or base_url if empty."""
    target = (step.get("target") or "").strip() or base_url
    if not target:
        return {"status": "failed", "error": "navigate requires 'target' or test url"}
    try:
        await page.goto(target, wait_until="domcontentloaded", timeout=STEP_TIMEOUT_MS)
        return {"status": "passed"}
    except Exception as e:
        logger.exception("Navigate failed: %s", e)
        return {"status": "failed", "error": str(e)}


async def execute_click(page: Any, step: dict) -> dict:
    """Execute click via strategy fallback chain."""
    return await _execute_with_fallback(page, step, "click", "")


async def execute_fill(page: Any, step: dict) -> dict:
    """Execute fill via strategy fallback chain."""
    return await _execute_with_fallback(page, step, "fill", step.get("value", ""))


async def execute_verify(page: Any, step: dict) -> dict:
    """Execute verify action. Requires step['expected']. Checks if expected text exists in page."""
    expected = step.get("expected") or ""
    if not expected.strip():
        return {"status": "failed", "error": "verify requires 'expected'"}
    try:
        content = await page.content()
        if expected in content:
            return {"status": "passed"}
        return {
            "status": "failed",
            "error": f"Expected text '{expected[:50]}...' not found in page",
        }
    except Exception as e:
        logger.exception("Verify failed: %s", e)
        return {"status": "failed", "error": str(e)}


async def execute_action(action: str, page: Any, step: dict, base_url: str = "") -> dict:
    """Dispatch to the appropriate action handler."""
    if action == "navigate":
        return await execute_navigate(page, step, base_url)
    if action == "click":
        return await execute_click(page, step)
    if action == "fill":
        return await execute_fill(page, step)
    if action == "verify":
        return await execute_verify(page, step)
    return {"status": "failed", "error": f"Unknown action: {action}"}
