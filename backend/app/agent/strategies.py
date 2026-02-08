"""Strategy classes for agent action execution: selector, DOM, vision fallback chain."""

import logging
from typing import Any

logger = logging.getLogger(__name__)

STEP_TIMEOUT_MS = 30_000

# Action verbs to strip when extracting target text from instructions
ACTION_VERBS = {"click", "fill", "enter", "type", "select", "choose"}
ARTICLES = {"the", "a", "an"}


def extract_target_text(instruction: str) -> str:
    """Remove action verbs and articles, strip quotes and extra whitespace."""
    if not instruction or not isinstance(instruction, str):
        return ""
    text = instruction.strip()
    words = text.split()
    filtered = [w for w in words if w.lower() not in ACTION_VERBS and w.lower() not in ARTICLES]
    result = " ".join(filtered).strip()
    result = result.strip("\"'").strip()
    return result


def determine_element_type(instruction: str) -> tuple[str, str]:
    """Return (locator_type, role) e.g. ('role', 'button'), ('label', ''), ('text', '')."""
    if not instruction or not isinstance(instruction, str):
        return ("text", "")
    lower = instruction.lower()
    if "button" in lower:
        return ("role", "button")
    if "input" in lower or "field" in lower:
        return ("label", "")
    if "link" in lower:
        return ("role", "link")
    return ("text", "")


class SelectorStrategy:
    """Execute action using advanced_selector. Returns result dict or None on failure."""

    @staticmethod
    async def try_execute(page: Any, step: dict, action: str, value: str = "") -> dict | None:
        selector = (step.get("advanced_selector") or "").strip()
        if not selector:
            return None
        try:
            if action == "click":
                await page.click(selector, timeout=STEP_TIMEOUT_MS)
            elif action == "fill":
                await page.fill(selector, str(value), timeout=STEP_TIMEOUT_MS)
            else:
                return None
            return {
                "success": True,
                "strategy": "selector",
                "self_healed": False,
            }
        except Exception as e:
            logger.debug("SelectorStrategy failed: %s", e)
            return None


class DOMStrategy:
    """Execute action using Playwright semantic locators (get_by_text, get_by_role, get_by_label)."""

    @staticmethod
    async def try_execute(page: Any, step: dict, action: str, value: str = "") -> dict | None:
        instruction = (step.get("instruction") or "").strip()
        if not instruction:
            return None
        text = extract_target_text(instruction)
        if not text:
            return None
        locator_type, role = determine_element_type(instruction)
        try:
            if locator_type == "role":
                locator = page.get_by_role(role, name=text)
            elif locator_type == "label":
                locator = page.get_by_label(text)
            else:
                locator = page.get_by_text(text)
            if action == "click":
                await locator.click(timeout=STEP_TIMEOUT_MS)
            elif action == "fill":
                await locator.fill(str(value), timeout=STEP_TIMEOUT_MS)
            else:
                return None
            dom_method = f"{locator_type}:{role}" if role else locator_type
            return {
                "success": True,
                "strategy": "dom",
                "self_healed": True,
                "dom_method": dom_method,
            }
        except Exception as e:
            logger.debug("DOMStrategy failed: %s", e)
            return None


class VisionStrategy:
    """Placeholder for T8: OpenRouter/Claude screenshot analysis. Returns None for now."""

    @staticmethod
    async def try_execute(page: Any, step: dict, action: str, value: str = "") -> dict | None:
        # TODO(T8): Implement using OpenRouter/Claude for screenshot analysis; return coordinates.
        return None
