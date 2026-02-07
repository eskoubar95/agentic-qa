# Merge PR (squash and merge)

## Overview

When the PR is approved and CI is green, check status and then **squash and merge** the PR. Use after you’ve addressed review feedback (e.g. with `/git/address-pr-feedback`) and everything is ready.

## When to use

- Review comments are resolved (or accepted).
- CI / CD and any required checks are passing (or you’re OK merging with known failures).
- You want to squash and merge into the base branch.

## Steps

1. **Identify the PR**
   - Current branch: `git branch --show-current`
   - If `gh` is available: `gh pr view` to get PR number, state (OPEN/MERGED), base branch, and mergeable status.

2. **Pre-merge checks (report, do not block unless critical)**
   - **Mergeable:** `gh pr view PR_NUMBER --json mergeable,mergeStateStatus` (or similar). If there are conflicts, say: “There are merge conflicts; resolve them locally and push, then try again.”
   - **CI / checks:** If possible, `gh pr checks PR_NUMBER` or `gh pr view --json statusCheckRollup`. Summarize: “Checks: …” (e.g. “all green” / “1 failed”). If the user said “merge anyway”, you may still proceed; otherwise suggest fixing red checks first.
   - **Unresolved conversations:** If you can fetch review comments, mention whether there are open threads. If the user has said they’re done with feedback, you can proceed.

3. **Confirm**
   - Short summary: “PR #N: … (base: main). Checks: … . Ready to squash and merge?”
   - If conflicts or required checks failed and the user hasn’t said to ignore: stop and tell them to fix first.

4. **Squash and merge**
   - If `gh` is available: `gh pr merge PR_NUMBER --squash --delete-branch` (or `--squash` only if you want to keep the branch). Prefer `--squash` so the PR becomes one commit on the base.
   - If not: output the exact steps: “On GitHub: open the PR → click ‘Squash and merge’ → confirm. Optionally delete the branch after merge.”

5. **After merge**
   - “PR merged. Update your local main: `git checkout main && git pull`.”
   - If the remote branch was deleted, suggest: `git branch -d <branch>` locally to remove the local branch.

## Usage

- `/git/merge-pr` – use current branch to find PR, run checks, then squash and merge (or output steps).
- `/git/merge-pr --no-delete-branch` – if using `gh`, merge without `--delete-branch` (keep remote branch).

## Rules

- Prefer **squash** merge so the PR is one commit on the base.
- Do not merge if there are merge conflicts; tell the user to resolve and push first.
- If CI is red, either stop and report or proceed only if the user has explicitly said to merge anyway.
