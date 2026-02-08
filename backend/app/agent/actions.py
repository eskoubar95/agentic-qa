"""Action execution functions for Playwright steps."""

import logging
from typing import Any

logger = logging.getLogger(__name__)

STEP_TIMEOUT_MS = 30_000


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
    """Execute click action. Requires step['advanced_selector']."""
    selector = step.get("advanced_selector") or ""
    if not selector.strip():
        return {"status": "failed", "error": "click requires 'advanced_selector'"}
    try:
        await page.click(selector, timeout=STEP_TIMEOUT_MS)
        return {"status": "passed"}
    except Exception as e:
        logger.exception("Click failed: %s", e)
        return {"status": "failed", "error": str(e)}


async def execute_fill(page: Any, step: dict) -> dict:
    """Execute fill action. Requires step['advanced_selector'] and step['value']."""
    selector = step.get("advanced_selector") or ""
    value = step.get("value", "")
    if not selector.strip():
        return {"status": "failed", "error": "fill requires 'advanced_selector'"}
    try:
        await page.fill(selector, str(value), timeout=STEP_TIMEOUT_MS)
        return {"status": "passed"}
    except Exception as e:
        logger.exception("Fill failed: %s", e)
        return {"status": "failed", "error": str(e)}


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
