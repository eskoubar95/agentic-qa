#!/usr/bin/env python3
"""Quick API test: create test, run, get result."""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

BASE = "http://localhost:8000"


def req(method: str, path: str, body: dict | None = None) -> dict:
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req_obj = urllib.request.Request(url, data=data, method=method)
    req_obj.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req_obj, timeout=10) as r:
        return json.loads(r.read().decode()) if r.length else {}


# Create test
test = req("POST", "/tests", {"name": "API test", "url": "https://example.com", "definition": {"steps": [{"action": "navigate", "instruction": "Go to page"}]}, "auto_handle_popups": True})
test_id = test["id"]
print(f"Created test: {test_id}")

# Run test
run = req("POST", "/test/run", {"test_id": str(test_id)})
run_id = run["run_id"]
print(f"Started run: {run_id}")

# Wait and get result
time.sleep(3)
result = req("GET", f"/results/{run_id}")
print(f"Result status: {result['status']}")
print("OK")
