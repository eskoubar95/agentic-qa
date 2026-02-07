# Code review (self-review before PR)

## Overview

Review the **current branch’s changes** against project standards and a short checklist. Produces a report and concrete suggestions so you can fix issues before opening the PR. Use after cleanup, before or instead of waiting for reviewer feedback. This is **self-review**, not handling others’ comments (use `/git/address-pr-feedback` for that).

## When to use

- Before opening a PR (after `/git/cleanup-branch`, before `/git/create-pr`).
- When you want a quality pass on your own diff without a human reviewer yet.

## Steps

1. **Get the diff**
   - `git diff base..HEAD` (and optionally `--stat`). Identify changed files and the kind of work (frontend, backend, API, config, tests).

2. **Apply a short checklist**
   - Use project rules (e.g. `.cursor/rules/`) and common quality criteria. Check for:
     - **Structure:** Single responsibility, file/function size, naming (intention-revealing, no generic `data`/`info`).
     - **Safety:** No secrets or PII in code/logs; input validation; no obvious SQL/command injection or XSS.
     - **Tests:** Critical paths covered; new code has or is covered by tests.
     - **Docs:** README or comments updated where behavior or API changed.
     - **Consistency:** Matches existing patterns in the repo (imports, error handling, typing).
   - Don’t invent new rules; stick to what’s in the repo’s rules or CONTRIBUTING.

3. **Report**
   - **Summary:** “X files changed, mainly … (e.g. API + tests).”
   - **Critical:** Must-fix items (e.g. secret in code, missing validation) with file and line or snippet.
   - **Suggestions:** Nice-to-have (e.g. extract function, add test, clarify name) with short rationale.
   - **Positive:** What already looks good (optional).

4. **Suggest next steps**
   - “Fix the N critical items, then run `/test/lint` and `/test/test`; optionally address suggestions. Then `/git/create-pr`.”

## Rules

- Base the review only on the **current branch diff** vs base (e.g. `main`).
- Be concise; use file:line or short snippets so the user can act quickly.
- This command does not apply fixes; it only reports and suggests. The user (or follow-up commands) applies changes.
