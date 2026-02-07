# Create PR (full flow)

## Overview

**Single entry point for opening a PR.** Runs in order: pre-check → size analyze → if size OK, generate description and create one PR; if too large or risky, suggest how to split and do **not** create a PR until the user has split and runs this command again for each part.

## When to use

- You have committed (and ideally pushed) your branch and want to open a PR.
- You want one command that handles size, description, and creation.

## Flow (run in this order)

### 1. Pre-checks

- Current branch: `git branch --show-current`
- Base branch: default `main` (or `--base develop` if user specifies).
- Unpushed commits: `git log origin/<branch>..HEAD` (or `git status`). If branch is not pushed or has unpushed commits, tell the user to push first (e.g. `/git/git-push`) and stop.

### 2. Size analyze (always)

- Compare to base: `git diff base..HEAD --shortstat` and `git diff base..HEAD --name-only` (and optionally `--numstat` for per-file).
- Thresholds: Good &lt; 400 LOC and &lt; 20 files; Large 400–800 or 20–40; Too large &gt; 800 or &gt; 40. Use repo limits if documented (e.g. CONTRIBUTING, .cursor).
- Output: branch vs base, LOC +/-, file count, verdict (Good / Large / Too large).

### 3. If size is **Too large** or **Large** and risky

- **Do not create a PR.** Output:
  - Verdict and numbers again.
  - A concrete **split suggestion**: e.g. “PR 1: backend/types (files A, B). PR 2: API (C, D). PR 3: UI (E, F). Merge order: 1 → 2 → 3.”
  - Short rationale per part (e.g. “Foundation first”, “UI depends on API”).
- Tell the user: “Split your work into separate branches (e.g. from the suggestion above). When the first part is on its own branch and pushed, run `/git/create-pr` again to create that PR; repeat for the next part.”
- Do **not** create branches or multiple PRs automatically (too error-prone).

### 4. If size is **Good** (or **Large** but user accepts risk)

- **Generate title:** from commits and scope, format `<type>(<scope>): <short summary>`. Optionally add issue/ticket if in branch or commits (e.g. `(ENG-123)` or `Closes #42`).
- **Generate description:** use `.github/pull_request_template.md` if present, else standard template (What, Why, How, Tests, Screenshots if UI, Rollback, Checklist). Fill from the actual diff and commits.
- **Create PR:** if `gh` is available, run (or output) `gh pr create --title "..." --body "..."` or `--body-file <file>`. If not, output the title and full body so the user can paste into GitHub. Support `--draft` if the user asked for draft.

### 5. Confirm

- If PR was created: “PR created: &lt;url&gt;. You can push more commits to this branch and they’ll appear in the PR.”
- If body was only output: “Paste the title and body above into GitHub when opening the PR.”

## Usage

- `/git/create-pr` – base `main`, full flow (analyze → describe → create one PR or suggest split).
- `/git/create-pr --base develop` – same with base `develop`.
- `/git/create-pr --draft` – create as draft when using `gh pr create --draft`.

## Rules

- Do not push for the user unless they ask; only remind to push and stop if needed.
- Do not auto-create multiple branches or multiple PRs; only suggest a split and ask the user to create branches and run `/git/create-pr` again per part.
- Use “Closes #N” or ticket IDs only if present in branch name or commits or user input.
