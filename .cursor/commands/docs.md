# Update documentation (from branch changes)

## Overview

Look at what changed on the current branch (vs base, e.g. `main`), find existing docs (README and any project convention), then **add**, **update**, or **remove** documentation as needed. One command: you infer whether to add new docs, change existing ones, or delete outdated content.

## When to use

- During Build or before commit, after code or structure changes.
- When new modules, APIs, or flows were added or removed.

## Steps

1. **What changed**
   - Run `git diff base..HEAD --name-only` (and optionally `--stat`) to see changed files and areas. Infer which areas or features changed (e.g. “new API route”, “new component”, “removed helper”).

2. **Where docs live**
   - Find READMEs (e.g. repo root, packages, subfolders the project treats as modules). Check for other conventions (e.g. `docs/`, `*.md` in specific places, or rules in `.cursor/rules/`). Prefer the project’s existing structure.

3. **Decide add / change / delete**
   - **Existing README in a changed area:** Read it. If it’s outdated (wrong API, wrong steps, removed feature), **update** or trim. If a section is no longer true, **remove** it.
   - **Changed or new area with no README:** If the project usually documents such areas (e.g. each package or module has a README), **add** a short README (purpose, how to run/use, main entry points). If the project doesn’t document at that level, suggest only or add a minimal note where it fits (e.g. root README).
   - **Removed code or feature:** If docs still describe it, **remove** or update those parts.

4. **Apply changes**
   - Edit the relevant markdown files. Keep content concise: purpose, how to run or use, and pointers to code. Avoid duplicating the codebase in prose.

5. **Summarize**
   - List what you did: “Updated README in X (section Y). Added README in Z. Removed section W from ….” So the user sees add/change/delete in one place.

## Rules

- Base all decisions on the **actual diff** and **existing doc layout**; don’t invent new doc trees unless the project already uses them.
- One command covers add, change, and delete; no separate “add docs” vs “change docs” commands.
- If the project has a docs style (e.g. in `.cursor/rules/` or CONTRIBUTING), follow it. Use English for docs unless the repo is non-English.
