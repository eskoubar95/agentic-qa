# Git push (sync with origin)

## Overview

Push the current branch to origin and optionally sync with the latest base branch (fetch + rebase) so the branch is up to date before opening a PR.

## When to use

- Before opening a PR, after commits are done.
- When you want to update your branch with the latest from `main` (or another base).

## Steps

1. **Check state**
   - Current branch: `git branch --show-current`
   - Uncommitted changes: `git status`
   - If working tree is dirty: suggest `git stash` or commit first, then continue.

2. **Fetch**
   - `git fetch origin`

3. **Optional: rebase onto base**
   - Base branch usually `main` (or ask: `develop`).
   - If current branch is not the base: `git rebase origin/main` (or `origin/develop`).
   - If rebase has conflicts: stop and tell the user to resolve; do not force.

4. **Push**
   - First push for this branch: `git push -u origin HEAD`
   - Later pushes: `git push`
   - If push is rejected (remote has new commits): suggest `git pull --rebase origin <branch>` then `git push` again.

5. **Force push**
   - Only if the user explicitly asks after a rebase: `git push --force-with-lease`. Warn that this rewrites history on the remote.

## Rules

- Prefer rebase over merge for a linear history when updating the branch.
- Do not force push unless the user has agreed.
- If rebase fails, report clearly and let the user fix conflicts.
