# Refactor code

## Overview

Improve structure, readability, and maintainability of a file or area **without changing behavior**. Use on demand when you ask to refactor something (e.g. “refactor this file”, “simplify this function”). This is **not** the same as code review: code review produces a report; refactor applies concrete changes (extract function, rename, reduce nesting, etc.).

## When to use

- When you explicitly ask to refactor (e.g. “refactor `lib/session-memory.ts`”, “clean up this component”).
- When a file or function is hard to follow, too long, or duplicated and you want it improved.
- On demand; not a required step in the PR workflow.

## Steps

1. **Identify scope**
   - From user message: which file(s), function(s), or module. Read the code and any tests.

2. **Refactor in small steps**
   - Prefer one or a few refactorings per pass: e.g. extract function, extract component, rename for clarity, reduce nesting (early returns), remove duplication, introduce a small type or parameter object. Avoid changing behavior or public API unless the user asked.
   - Follow project conventions (`.cursor/rules/`, existing patterns). Keep the same behavior so existing tests still pass.

3. **Verify**
   - Run the project’s tests for the touched area (or full suite). Run lint/typecheck. If something breaks, revert the step that caused it and try a smaller change.

4. **Summarize**
   - Short list: “Extracted X, renamed Y, simplified Z. Tests and lint pass.”

## Rules

- No behavior change: same inputs → same outputs and side effects. If the user asked for a behavior change, do that separately or label it clearly.
- Prefer small, reviewable steps. One logical refactor per commit is fine.
- If the project has a refactor or style rule, follow it.
