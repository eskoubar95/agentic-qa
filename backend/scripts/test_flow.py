#!/usr/bin/env python3
"""End-to-end flow test: create test, run, verify results and SSE."""

import json
import sys

import httpx

BASE = "http://127.0.0.1:8000"


def main():
    # 1. Create test
    payload = {
        "name": "Flow test",
        "url": "https://example.com",
        "definition": {
            "steps": [
                {
                    "action": "navigate",
                    "instruction": "Go to example",
                    "target": "https://example.com",
                },
                {"action": "verify", "instruction": "Check page", "expected": "Example Domain"},
            ]
        },
    }
    r = httpx.post(f"{BASE}/tests", json=payload, timeout=10)
    r.raise_for_status()
    test = r.json()
    test_id = test["id"]
    print(f"Created test: {test_id}")

    # 2. Run test
    r2 = httpx.post(f"{BASE}/test/run", json={"test_id": str(test_id)}, timeout=10)
    r2.raise_for_status()
    run = r2.json()
    run_id = run["run_id"]
    print(f"Started run: {run_id}")

    # 3. Connect to SSE and collect events
    events = []
    with httpx.stream("GET", f"{BASE}/results/{run_id}/stream", timeout=30.0) as r3:
        assert r3.status_code == 200
        assert "text/event-stream" in r3.headers.get("content-type", "")
        current = {}
        for line in r3.iter_lines():
            if line.startswith("event:"):
                current = {"type": line.split(":", 1)[1].strip()}
            elif line.startswith("data:"):
                try:
                    current["data"] = json.loads(line.split(":", 1)[1].strip())
                    events.append(current)
                except json.JSONDecodeError:
                    pass
            if events and events[-1].get("type") in ("complete", "error"):
                break
    print(f"SSE events received: {len(events)}")
    for e in events[:5]:
        print(f"  - {e.get('type')}: {str(e.get('data', {}))[:80]}...")
    if events:
        last = events[-1]
        print(
            f"Last event: {last.get('type')} -> status={last.get('data', {}).get('data', {}).get('status', '?')}"
        )

    # 4. Get result
    r4 = httpx.get(f"{BASE}/results/{run_id}", timeout=10)
    r4.raise_for_status()
    result = r4.json()
    print(f"Result status: {result['status']}")
    step_results = result.get("step_results") or []
    print(f"Step results: {len(step_results)} steps")
    for sr in step_results:
        print(f"  Step {sr.get('step')}: {sr.get('status')}")
    if result.get("screenshots"):
        print(f"Screenshots: {len(result['screenshots'])} captured")

    assert result["status"] == "passed", f"Expected passed, got {result['status']}"
    assert len(step_results) >= 2, f"Expected at least 2 steps, got {len(step_results)}"
    print("Flow test OK")


if __name__ == "__main__":
    main()
    sys.exit(0)
