# Run tests and fix failures

## Overview

Run the project’s test suite, report pass/fail, then for each failure: categorize (assertion, runtime, timeout, setup, mock) and suggest or apply a fix. Use during Build or before commit.

## When to use

- During or after implementing on a branch.
- Before commit or PR to avoid pushing broken tests.

## Steps

1. **Discover test setup**
   - Look for test scripts in `package.json` (e.g. `npm test`, `npm run test:watch`), `pyproject.toml` (pytest), or config (Vitest, Jest, pytest). Run from repo root or the relevant package directory.
   - Use the project’s own test command and config.

2. **Run the full suite**
   - Execute the test command (e.g. `npm test`, `pytest`). Capture output: total run, passed, failed, skipped.

3. **Report result**
   - If all passed: say so and stop.
   - If any failed: list each failed test (name, file, and the failure message or traceback).

4. **Triage failures**
   - For each failure, classify: assertion failure, runtime error (e.g. undefined, TypeError), timeout, setup/teardown, or mock/stub issue.
   - Briefly note likely cause (wrong expectation, missing data, flaky timing, bad mock).

5. **Fix**
   - For each failure: read the relevant test and source code, then propose a concrete fix (code change or test change). Apply simple fixes (e.g. update expectation, add missing mock, fix typo); for complex or ambiguous cases, suggest and let the user decide.
   - After changes, re-run the test suite and repeat until all pass or only known/skipped remain.

## Rules

- Use the project’s test runner and conventions; don’t invent new runners.
- Prefer fixing the implementation over weakening the test unless the test is clearly wrong.
- If the repo has multiple packages (e.g. frontend and backend), run tests in each and report per package. Optionally run the full monorepo test command if one exists.
