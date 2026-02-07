# Create branch from plan

## Overview

Use **after** you have a plan (e.g. from `/create-plan`) and **before** you run build. From the plan you choose one task (phase) or the whole plan, we classify the work (feature / fix / chore / etc.), then create a dedicated branch so you have a clear branch to work on.

## When to use

- Plan is already created in plan mode.
- You want one branch per task, or one branch for the full plan.

## Steps

1. **Get the plan**
   - Use the plan in the current chat or plan document.
   - If nothing is in context, ask the user to paste the plan or the plan title + phases.

2. **Identify scope: one task vs whole plan**
   - List the plan’s **phases** (Phase 1, Phase 2, …) from the plan.
   - Ask the user (or infer from their message):
     - **Single task:** “Which phase do you want a branch for?” (e.g. Phase 2) → branch covers that phase only.
     - **Whole plan:** “Branch for the entire plan?” → one branch for all phases.
   - If the plan has no phases, treat the whole plan as one “task”.

3. **Classify the work**
   From the chosen scope (task or full plan), decide:
   - **feature** – new capability, new UI/API/flow
   - **fix** – bugfix, regression, incorrect behaviour
   - **chore** – tooling, config, deps, refactor without new behaviour
   - **docs** – only documentation
   - **refactor** – structural code change, no new behaviour

   Use the plan’s **Overview** and **Goal(s)** to choose. If unclear, ask: “Is this a new feature, a bugfix, or a chore/refactor?”

4. **Propose branch name**
   - Format: `<type>/<short-slug>` in kebab-case.
   - Short slug from the phase name or plan title (e.g. “Session memory” → `session-memory`, “SSE CORS” → `sse-cors`).
   - Optional: if the plan references a ticket (e.g. ENG-123), offer: `<ticket>-<type>-<slug>` or `<type>/<ticket>-<slug>` (follow project convention if any).
   - Show the user: “Suggested branch: `feature/session-memory`. Create it? (y/n or suggest another name)”

5. **Create the branch**
   - From a clean state: `git status` (warn if uncommitted changes and suggest commit or stash).
   - Ensure you’re on the right base (e.g. `main` or `develop`): `git branch --show-current`; if the user wants another base, they say so.
   - Create and switch: `git checkout -b <branch-name>`.
   - Confirm: “Branch `feature/session-memory` created. You can start working from the plan.”

## Branch name rules

- **Lowercase, kebab-case:** `feature/add-run-log`, not `Feature/AddRunLog`.
- **Short and clear:** 2–4 words max for the slug.
- **Type prefix:** always `feature/`, `fix/`, `chore/`, `docs/`, or `refactor/`.

## Examples

| Plan scope        | Classification | Example branch        |
|-------------------|----------------|------------------------|
| Phase 1: Add store | feature       | `feature/session-memory-store` |
| Phase 2: Fix SSE   | fix           | `fix/sse-cors-stream`  |
| Whole plan: Tooling | chore        | `chore/ci-lint-setup`  |
| Refactor run worker | refactor     | `refactor/run-worker-deps` |

## Optional: issue key

If the plan references a ticket (e.g. in References or Overview), you may offer a branch name that includes it, e.g. `ENG-123-feature/session-memory` or `feature/ENG-123-session-memory`. Ask the user if they want the ticket in the branch name.
