# Lint (and format / typecheck)

## Overview

Run the project’s lint (and, where available, format and typecheck), apply auto-fixes, then report what remains so it can be fixed manually. Use during Build or before commit.

## When to use

- During or after implementing on a branch.
- Before commit or PR so the branch is clean.

## Steps

1. **Discover project setup**
   - Look for `package.json` (e.g. `npm run lint`, `npm run lint:fix`, `npm run format`, `npm run type-check`), `pyproject.toml` (e.g. ruff, mypy), or other config (ESLint, Prettier, Ruff). Run from repo root or the relevant package directory.
   - Prefer scripts the project already defines; avoid inventing commands.

2. **Run lint (and auto-fix if available)**
   - Run the project’s lint command (e.g. `npm run lint`, `pnpm lint`).
   - If there is a dedicated fix command (e.g. `lint:fix`, `eslint --fix`, `ruff check --fix`), run it and report how many issues were fixed.
   - If the project has a format command (e.g. Prettier, `ruff format`), run it so formatting is consistent.

3. **Run typecheck if available**
   - If the project has a type-check step (e.g. `tsc --noEmit`, `npm run type-check`, `mypy`), run it and list type errors.

4. **Report**
   - Summarize: auto-fixed (count or “done”), remaining errors (file:line and rule/message), remaining warnings if relevant.
   - For each remaining error: short suggestion (e.g. “add missing dependency”, “fix type”, “remove unused variable”). Apply straightforward fixes when you can; for the rest, list them clearly so the user can fix or decide to ignore.

5. **Re-run once**
   - After applying fixes, run lint (and typecheck) again and confirm the list of remaining issues or “all clear”.

## Rules

- Use the project’s own lint/format/typecheck commands and config; respect `.eslintignore`, `ruff.toml`, etc.
- Prefer safe auto-fixes (formatting, unused imports, simple rule fixes); for anything ambiguous, suggest rather than change.
- If the repo has multiple packages (e.g. frontend and backend), run lint (and typecheck) in each relevant package and report per package.
