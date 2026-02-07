# Create implementation plan (plan mode)

You create a clear, actionable implementation plan **as the main deliverable** in this chat. The plan is the document we use in Cursor plan mode before development starts. Do not write the plan to a separate docs folder—output the full plan here so it can be used directly in the plan.

**When to use:** Features or changes that are multi-step, touch several components, or need alignment before coding (e.g. >~400 LOC or cross-stack).

---

## How to run

**With context:**  
`/create-plan [ticket-fil eller kort beskrivelse]`  
Example: `/create-plan Add session memory for self-healing`

**With Traycer AI handoff:**  
Paste the content from Traycer’s “Handoff to Cursor” into the chat and run `/create-plan`. The command will convert it into Cursor plan format (phases, success criteria, valid Mermaid, references) so the agent and Build understand it.

**Without context:**  
`/create-plan`  
Then you ask for: (1) opgaven/ticket, (2) krav eller acceptance criteria, (3) begrænsninger eller tekniske overvejelser.

**From Traycer AI (Handoff to Cursor):**  
User pastes content from Traycer’s “Handoff to Cursor”. Run the **Traycer → Cursor** conversion below, then output the plan in Cursor format.

---

## When input is from Traycer AI (Handoff to Cursor)

If the user’s message contains a plan that was handed off from **Traycer AI** (e.g. Plan Specification, Runtime Instructions, Key Files Reference, Implementation Steps, TICKETS like T1/T2, and/or a Mermaid architecture diagram), do the following **before** or **instead of** the normal Step 1–4 flow:

1. **Recognize Traycer structure**  
   Typical signs: “Plan Specification”, “Runtime Instructions”, “Documentation Requirements”, “Implementation Steps”, “Key Files Reference”, ticket labels (T1, T2, …), “Technical Plan”, Mermaid code block.

2. **Convert into Cursor plan format**
   - **Overview** ← from Traycer’s intro/observations/approach (1–2 sentences).
   - **Current state** ← from “Observations” or similar; add what’s missing from `.cursor/rules` if needed.
   - **Desired end state** ← from acceptance criteria / verification steps.
   - **What we’re NOT doing** ← infer from scope or add “Out of scope for this ticket”.
   - **Approach** ← from Traycer’s “Approach” or strategy.
   - **Phases** ← from “Implementation Steps” or TICKETS: each major step or ticket becomes a Phase with **Goal**, **Changes** (file/area + what to do), and **Success criteria** (Automated + Manual). Map “Runtime Instructions” and “Verification Steps” into Automated/Manual success criteria per phase where they fit.
   - **References** ← from “Key Files Reference”: list `.cursor/rules/*.mdc`, `.cursor/skills/*/SKILL.md`, and code paths. Use project paths (e.g. `.cursor/rules/architecture.mdc`) so the agent can resolve them.

3. **Fix Mermaid diagrams**  
   Traycer-pasted Mermaid often triggers “Invalid mermaid syntax”. Check the diagram block: fix or simplify invalid syntax (e.g. node IDs, quotes, arrows, subgraphs). Output only valid Mermaid so Cursor can render it without errors.

4. **Output the full plan**  
   Emit the result in the **same structure** as Step 3 (Overview, Current state, Findings, Desired end state, What we’re NOT doing, Approach, Phase 1…N with Goal/Changes/Success criteria, Testing, References). So the agent and Cursor plan mode / Build get one consistent, Cursor-style plan.

If both Traycer content and other context (e.g. a ticket file) are present, prefer Traycer as the main source and merge in only what’s missing from the other context.

---

## Process (4 steps)

### Step 1: Context and scope

1. **If the user gave a path or reference:** Read that file fully (no limit/offset). If they gave a short description, treat it as the task summary.
2. **Use project context:**  
   - `.cursor/rules/diagrams.mdc` – flows, data model, deployment  
   - `.cursor/rules/architecture.mdc` – stack, constraints, key decisions  
   - Relevant rules in `.cursor/rules/` (frontend-nextjs, backend-fastapi, data-model, ux-flows, agent-executor).
3. **Search the codebase** for existing patterns, similar features, and integration points (e.g. `codebase_search`, `grep` for key terms).
4. **Summarise and ask only what you cannot decide from code/docs:**  
   - “Based on [ticket/description] and the codebase, we need to [summary]. I’ve found: [relevant files/patterns]. Open questions: [list].”

Do not continue with the full plan until scope and open questions are resolved.

---

### Step 2: Research and structure

1. **Find similar behaviour** in the repo (same flow, same layer: e.g. run worker, SSE, test CRUD).
2. **Note conventions:** file layout, naming, how Next.js talks to FastAPI, how workers use Redis/Neon.
3. **Propose phases** (e.g. 3–5), each with a clear outcome and optional size hint (e.g. “Phase 2 ~200 LOC”).
4. **Get quick confirmation:** “Proposed phases: 1) … 2) … 3) … Does this order and granularity work?”

---

### Step 3: Write the plan (output in this chat)

Produce the **full plan below** so it can be used directly in Cursor plan mode. Do not create a separate file in a docs folder.

Use this structure:

```markdown
# [Feature / task name] – Implementation plan

## Overview
[1–2 sætninger: hvad og hvorfor]

## Current state
[What exists today, what’s missing, constraints from architecture/rules]

### Findings
- [File:line or component] – [what we reuse or must respect]
- [Pattern or limitation]

## Desired end state
[Concrete outcome and how we verify it]

## What we’re NOT doing
[Explicit out-of-scope to avoid scope creep]

## Approach
[High-level strategy]

---

## Phase 1: [Name]

### Goal
[What this phase achieves]

### Changes
- **File/area:** `path` – [what to add/change]
- (Repeat as needed, with short code snippets if helpful)

### Success criteria

**Automated**
- [ ] e.g. `npm run build` / `pytest` / migrations
- [ ] Lint/typecheck

**Manual**
- [ ] e.g. “Run test from UI and see result in /results”
- [ ] Edge cases you’ll check

**→ Pause after Phase 1** – confirm manually before Phase 2.

---

## Phase 2: [Name]
(Same structure: Goal, Changes, Automated + Manual criteria, Pause)

---

## Phase N: …

---

## Testing
- Unit: [what to test]
- Integration: [scenarios]
- Manual: [steps]

## References
- Ticket/description: [reference]
- Rules: `.cursor/rules/architecture.mdc`, `diagrams.mdc`, …
- Code: [key files]
```

---

### Step 4: Review and refine

1. **Present the plan:** “Plan is above. Use it in plan mode as-is or copy into your plan doc.”
2. **Ask for:** phase scope, missing edge cases, stricter/looser success criteria.
3. **Iterate** on the plan text in this chat until the user is satisfied. Do not add “save to docs” steps—the plan lives here and in Cursor plan mode.

---

## Rules

- **Skeptical:** Question vague requirements; verify against code and rules.
- **Interactive:** Get alignment on phases before writing the full plan; allow changes after.
- **Concrete:** File paths, line references, and clear automated vs manual checks.
- **Bounded:** “What we’re NOT doing” is mandatory.
- **No open questions in the final plan:** Resolve or document assumptions so the plan is actionable.
- **Success criteria:** Always split into **Automated** (commands, tests, lint) and **Manual** (UI, behaviour, edge cases).

---

## Project-specific

- **Stack:** Next.js 15 (App Router), FastAPI, Neon, Upstash Redis, Playwright, OpenRouter. See `.cursor/rules/architecture.mdc` and `diagrams.mdc`.
- **Skills:** Prefer `.cursor/skills/nextjs-app-router-patterns`, `fastapi-templates`, `python-performance-optimization` when suggesting patterns.
- **No auth/teams/scheduled runs** (MVP). Self-healing and real-time results are in scope; keep screenshots for last 20 runs per test.
