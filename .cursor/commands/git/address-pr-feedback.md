# Address PR feedback

## Overview

Help work through review comments on the current PR (e.g. from CodeRabbit, GitHub code review, or other bots). List open comments, then for each one suggest or apply code changes so you can fix and resolve the conversation on GitHub.

## When to use

- After pushing a PR: CodeRabbit, CI, or reviewers have left comments.
- You want to go through each comment, apply fixes, and be ready to “resolve conversation”.

## Steps

1. **Identify the PR**
   - Current branch: `git branch --show-current`
   - If `gh` is available: `gh pr view` (or `gh pr view --web`) to get PR number and URL. Otherwise ask the user for the PR number or link.

2. **Fetch review comments**
   - If `gh` is available: `gh api repos/OWNER/REPO/pulls/PR_NUMBER/comments` and, if needed, review threads. Alternatively: `gh pr view PR_NUMBER --comments` or `gh pr view PR_NUMBER --json comments,reviews`.
   - If not: ask the user to paste the list of open comments (file, line, body) or share the PR link so you can work from context they provide.
   - Filter to **open / unresolved** comments only (ignore already resolved if the API exposes that).

3. **List and prioritize**
   - Output a short list: file, line (or range), author/source (e.g. CodeRabbit), and summary of the comment.
   - Group by file so fixes can be done file by file.
   - If there are many, suggest doing the most important or blocking first (e.g. “must fix” vs “nit”).

4. **Address each comment (or batch by file)**
   - For each comment: read the relevant code in the repo (file + line).
   - Propose a concrete change (diff or step-by-step edit). If the comment suggests a fix (e.g. CodeRabbit suggestion), consider that and either apply it or adapt it.
   - After applying a change, say: “Fixed; you can resolve this conversation on GitHub.”
   - If a comment is unclear or you disagree: suggest a short reply the user can post (e.g. “Won’t fix because …” or “Done in commit X”).

5. **Remind to push and re-check**
   - When all discussed comments are addressed: “Commit and push (`/git/commit-git` then `/git/git-push`). New commits will show up on the PR. Then resolve each conversation on GitHub (or mark as resolved) and re-run CI if needed.”

## Usage

- `/git/address-pr-feedback` – use current branch to find PR and fetch comments (via `gh` or user input), then go through them.
- `/git/address-pr-feedback 42` – use PR #42 (if your shell or `gh` supports passing the number).

## Rules

- Do not resolve conversations on GitHub for the user (they click “Resolve conversation” themselves).
- Base all suggestions on the **actual** file content and the **exact** comment text.
- If the user says “skip this one” or “won’t fix”, note it and move on; optionally suggest a reply they can post.
