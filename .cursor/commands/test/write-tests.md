# Write unit tests

## Overview

Generate unit tests for a given file, module, or feature. Use when you’ve added or changed code and want tests that follow the project’s conventions. Complements `/test/test` (which runs and fixes existing tests).

## When to use

- During Build, after implementing a new function, component, or module.
- When you or the plan say “add tests for this” and no tests exist yet.
- On demand: “write tests for `path/to/file.ts`” or “write tests for the session memory lookup”.

## Steps

1. **Identify scope**
   - From user message or context: which file(s), function(s), or feature to test. If unclear, ask or infer from recent changes (`git diff base..HEAD --name-only`).
   - Read the source: public API, inputs, outputs, edge cases, and dependencies (mocks needed).

2. **Discover project test setup**
   - Find test runner and config (Vitest, Jest, pytest, etc.) and where tests live (e.g. `*.test.ts` next to source, `__tests__/`, `tests/`). Use the project’s existing pattern.
   - Note conventions: naming (describe/it, test_), structure (AAA), mocking style, and any rules in `.cursor/rules/` or CONTRIBUTING.

3. **Generate tests**
   - Cover: happy path, main error paths, and important edge cases (empty input, boundaries, null). Prefer behavior over implementation details.
   - For components: render, user interaction, and accessibility where relevant. For functions/services: inputs and return values or side effects (mocked).
   - Use the project’s test runner and assertions; add mocks for external deps (API, DB, etc.). Keep tests focused and readable.

4. **Place and verify**
   - Write tests in the correct path (same package/module as source). Run the test command for that file or package and fix any failures (imports, types, mocks).
   - If the project has coverage goals, mention whether the new tests help meet them.

## Rules

- Follow existing test style and file layout; don’t introduce a new runner or structure.
- Test the public API or behavior; avoid testing internals or implementation details.
- One test file per source file (or per module) if that’s the project convention; otherwise follow the repo’s pattern.
