# Cleanup branch (before commit)

## Overview

Scan the current branch for debug code, commented-out blocks, and unlinked TODOs; suggest or apply safe cleanups; optionally suggest how to organize commits. Use **before** commit (after Build) so the branch is ready for PR.

## When to use

- After implementing, before you run `/git/commit-git` or open a PR.
- When you want to remove temporary or noisy changes.

## Steps

1. **Scan for debug and noise**
   - **Debug:** `console.log`, `console.debug`, `console.info`, `debugger`, and similar (e.g. `print` left for debugging in Python). Search the changed or relevant files (e.g. `git diff base..HEAD --name-only` then grep). Ignore test files or logging libraries if the project uses them intentionally.
   - **Commented code:** Large blocks of commented-out code (e.g. 5+ lines). Skip short “why” comments or single-line comments.
   - **TODOs / FIXMEs / HACKs:** Find `TODO`, `FIXME`, `HACK`, `TEMP` (or project-specific markers). Note whether they’re linked to an issue (e.g. `TODO(ENG-123):`) or unlinked.

2. **Report**
   - List: file and line (or range) for each finding. Group by kind (debug, commented code, unlinked TODO).
   - For unlinked TODOs: suggest “fix now”, “link to issue (e.g. TODO(XXX):)”, or “remove if obsolete”.

3. **Auto-fix (safe only)**
   - **Debug:** Remove `console.log`/`debugger`/debug `print` in non-test, non-logger code. If the project uses a logger, don’t replace with logger unless the user asked; otherwise just remove.
   - **Commented code:** Propose deletion of large commented blocks; apply if clearly dead code. Don’t remove short explanatory comments.
   - **TODOs:** Don’t auto-remove; only suggest linking or fixing.

4. **Commits (optional)**
   - If the user wants a cleaner history: look at `git log base..HEAD --oneline`. If there are “WIP”, “fix”, “oops” or merge commits, suggest squashing or rewording (e.g. “Consider squashing commits X and Y into one. Use `git rebase -i base`.”). Do not run rebase or amend yourself unless the user explicitly asks.

5. **Summarize**
   - “Removed N debug statements, M commented blocks. K unlinked TODOs: [list]. Next: run `/git/commit-git` when ready.”

## Rules

- Only remove or change what’s clearly debug or dead; when in doubt, suggest and let the user decide.
- Respect project patterns (e.g. allowed `console.error` in app code, or logger in tests). If the repo has a cleanup or lint rule, align with it.
- Don’t run destructive git commands (rebase, reset) unless the user has asked to clean up commits.
