"""AgentExecutor: runs test definitions via Playwright."""

import base64
import json
import logging
import time
import uuid
from datetime import datetime, timezone

from playwright.async_api import async_playwright

from app.agent.actions import execute_action
from app.database import get_connection
from app.redis_client import append_run_event

logger = logging.getLogger(__name__)

TOTAL_TIMEOUT_SEC = 300
STEP_TIMEOUT_SEC = 60
VIEWPORT = {"width": 1280, "height": 720}


def _validate_step(step: dict, idx: int) -> str | None:
    """Validate step. Returns error message or None if valid."""
    action = step.get("action")
    if not action:
        return f"Step {idx + 1}: missing 'action'"
    if action not in ("navigate", "click", "fill", "verify"):
        return f"Step {idx + 1}: unknown action '{action}'"
    if action == "navigate":
        pass  # target optional - executor uses test_url if empty
    elif action == "click":
        sel = step.get("advanced_selector")
        if not sel or not str(sel).strip():
            return f"Step {idx + 1}: click requires 'advanced_selector'"
    elif action == "fill":
        sel = step.get("advanced_selector")
        if not sel or not str(sel).strip():
            return f"Step {idx + 1}: fill requires 'advanced_selector'"
        if "value" not in step:
            return f"Step {idx + 1}: fill requires 'value'"
    elif action == "verify":
        exp = step.get("expected")
        if not exp or not str(exp).strip():
            return f"Step {idx + 1}: verify requires 'expected'"
    return None


class AgentExecutor:
    """Executes test definitions using Playwright browser automation."""

    def __init__(self, run_id: str, test_definition: dict, test_url: str, test_name: str = ""):
        self.run_id = run_id
        self.test_definition = test_definition or {}
        self.test_url = test_url or ""
        self.test_name = test_name or "Test"

    async def execute_test(self) -> dict:
        """Execute the test definition with Playwright."""
        steps = self.test_definition.get("steps") or []
        if not steps:
            await append_run_event(self.run_id, "error", {"message": "No steps in test definition"})
            await self._update_db_failed("No steps in test definition", None)
            return {"status": "failed", "error": "No steps"}

        for i, step in enumerate(steps):
            err = _validate_step(step, i)
            if err:
                await append_run_event(self.run_id, "error", {"message": err, "step": i})
                await self._update_db_failed(err, i)
                return {"status": "failed", "error": err}

        started_at = datetime.now(timezone.utc)
        total_start = time.perf_counter()

        await append_run_event(
            self.run_id,
            "log",
            {"message": "Starting test execution", "test_name": self.test_name},
        )

        async with get_connection() as conn:
            await conn.execute(
                """
                UPDATE test_runs
                SET status = 'running', started_at = $1
                WHERE id = $2
                """,
                started_at,
                uuid.UUID(self.run_id),
            )

        screenshots: list[dict] = []
        step_results: list[dict] = []
        failed_step: int | None = None
        final_error: str | None = None

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                try:
                    context = await browser.new_context(
                        viewport=VIEWPORT,
                        user_agent=None,
                        ignore_https_errors=True,
                    )
                    context.set_default_timeout(60_000)
                    page = await context.new_page()

                    for i, step in enumerate(steps):
                        if (time.perf_counter() - total_start) > TOTAL_TIMEOUT_SEC:
                            final_error = "Total test timeout (5 min) exceeded"
                            failed_step = i
                            break

                        action = step.get("action", "")
                        instruction = step.get("instruction", action)

                        await append_run_event(
                            self.run_id,
                            "log",
                            {
                                "step": i,
                                "message": f"Executing {action}: {instruction}",
                            },
                        )

                        step_start = time.perf_counter()
                        result = await execute_action(action, page, step, self.test_url)
                        duration_ms = int((time.perf_counter() - step_start) * 1000)

                        step_result = {
                            "step": i,
                            "status": result["status"],
                            "strategy": "selector",
                            "self_healed": False,
                            "duration_ms": duration_ms,
                            "attempts": 1,
                            "error": result.get("error"),
                        }
                        step_results.append(step_result)

                        await append_run_event(
                            self.run_id,
                            "log",
                            {
                                "step": i,
                                "message": "Step completed"
                                if result["status"] == "passed"
                                else f"Step failed: {result.get('error', '')}",
                                "duration_ms": duration_ms,
                                "status": result["status"],
                            },
                        )

                        screenshot_data = await self._capture_screenshot(page, i)
                        if screenshot_data:
                            screenshots.append(screenshot_data)
                            await append_run_event(
                                self.run_id,
                                "screenshot",
                                {"step": i, "data_url": screenshot_data["data_url"]},
                            )

                        if result["status"] == "failed":
                            failed_step = i
                            final_error = result.get("error", "Step failed")
                            break

                    await page.close()
                    await context.close()
                finally:
                    await browser.close()

        except Exception as e:
            logger.exception("Executor error: %s", e)
            final_error = str(e)
            if failed_step is None:
                failed_step = len(step_results)

        total_duration_ms = int((time.perf_counter() - total_start) * 1000)
        completed_at = datetime.now(timezone.utc)
        status = "passed" if not final_error else "failed"

        await append_run_event(
            self.run_id,
            "complete",
            {
                "status": status,
                "duration_ms": total_duration_ms,
                "steps_completed": len(step_results),
                "message": final_error or "Test completed",
            },
        )

        await self._update_db_complete(
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=total_duration_ms,
            screenshots=screenshots,
            step_results=step_results,
            error=final_error,
            error_step=failed_step,
        )

        return {
            "status": status,
            "duration_ms": total_duration_ms,
            "steps_completed": len(step_results),
            "error": final_error,
        }

    async def _capture_screenshot(self, page, step_num: int) -> dict | None:
        """Capture full page screenshot as base64 data URL."""
        try:
            png = await page.screenshot(type="png", full_page=True)
            b64 = base64.b64encode(png).decode("ascii")
            data_url = f"data:image/png;base64,{b64}"
            return {
                "step": step_num,
                "data_url": data_url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "compressed": False,
            }
        except Exception as e:
            logger.warning("Screenshot failed: %s", e)
            return None

    async def _update_db_failed(self, error: str, error_step: int | None) -> None:
        """Update test_runs with failed status."""
        async with get_connection() as conn:
            await conn.execute(
                """
                UPDATE test_runs
                SET status = 'failed', error = $1, error_step = $2,
                    completed_at = NOW(), duration_ms = 0
                WHERE id = $3
                """,
                error,
                error_step,
                uuid.UUID(self.run_id),
            )

    async def _update_db_complete(
        self,
        status: str,
        started_at,
        completed_at,
        duration_ms: int,
        screenshots: list,
        step_results: list,
        error: str | None,
        error_step: int | None,
    ) -> None:
        """Update test_runs with final results."""
        async with get_connection() as conn:
            await conn.execute(
                """
                UPDATE test_runs
                SET status = $1, started_at = $2, completed_at = $3,
                    duration_ms = $4, screenshots = $5::jsonb, step_results = $6::jsonb,
                    error = $7, error_step = $8
                WHERE id = $9
                """,
                status,
                started_at,
                completed_at,
                duration_ms,
                json.dumps(screenshots),
                json.dumps(step_results),
                error,
                error_step,
                uuid.UUID(self.run_id),
            )
