# Commit unstaged files

## Overview

Review unstaged changes, stage them, and create a short, focused commit message.

## Steps

1. **Review unstaged changes**
   - Run `git status` to see modified/untracked files
   - Run `git diff` to see the actual changes
   - Understand what changed and why

2. **Optional: issue key**
   - Check branch name for an issue key (Linear, Jira, GitHub issue, etc.)
   - If the user wants one and it’s not in context, optionally ask
   - Commits are fine without an issue key

3. **Stage the changes**
   - `git add -A` (all unstaged) or `git add <path>` for specific paths
   - Confirm with `git status` that the right files are staged

4. **Create commit message and commit**
   Goal: Create a concise commit message from staged changes

   Context:
   - Use `.github/commit-template.txt` structure
   - Conventional Commit types: feat | fix | chore | docs | test | refactor | perf | build | ci
   - Keep summary ≤ 72 chars; imperative mood

   Inputs:
   - scope (optional): {{scope}}
   - issue id (optional): BS-{{id}}
   - key changes (bullets): {{bullets}}

   Output format:
   <type>(<scope>): <short summary>

   WHY:
   - <why change is needed>

   HOW:
   - <key changes>

   NOTES:
   - <breaking changes, risks, follow-ups>


## Template

- `git commit -m "<type>(<scope>): <short summary>"`
- With issue key: `git commit -m "<issue-key>: <type>(<scope>): <short summary>"`

**Types:** fix, feat, add, update, refactor, docs, chore, test, style

## Rules

- **Length:** ≤ 72 characters for the subject line
- **Imperative:** Use "fix", "add", "update" (not "fixed", "added", "updated")
- **Capitalize:** First letter of the summary
- **No period** at the end of the subject
- **Describe why** when useful, not only what changed

## Examples

- `feat(tests): add self-healing step result to run events`
- `fix(api): proxy SSE CORS for FastAPI stream`
- `PROJ-42: chore(deps): bump Next.js to 15.5`
