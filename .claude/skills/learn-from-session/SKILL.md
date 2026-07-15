---
name: learn-from-session
description: >
  Mine the current session for durable preferences and corrections, then propose
  confidence-ranked skill edits — propose-first, applied only on approval. Fires on:
  "learn from this session", "what did you learn", "mine this session", "update the
  skill with what I told you", or any session-end review request.
---

Preference mining is the propose-first half of the dual improvement loop. Error-annealing
(`improve-skill`) runs autonomously because behavior is observable and git rollback is the safety
net; preference mining is judgment, so it is **PROPOSE-FIRST with human approval** — you apply
nothing until the user says so. Where the harness supports session-end hooks, this may run
automatically at session end; on-request invocation is the portable path.

## Protocol

### 1. Scan the session
Look only at skills that were **active** this session. Collect two signal types:
- **Corrections** — the user changed, redirected, or fixed skill-produced output.
- **Repeated preferences** — the same direction expressed 2+ times (format, tone, structure,
  ordering, tool choice).

### 2. Quality-filter
Keep a signal only if it is:
- **Durable** — would apply next time, not a one-off for this task.
- **New** — not already encoded in the skill. **Read the target skill before proposing** (see
  Gotchas).
- **Safe** — drop anything secret-shaped: keys, tokens, client-confidential specifics.

Drop one-off phrasings, task-specific details, and restatements of existing content.

### 3. Attribute
Map each surviving signal to the **one** skill responsible for the output being corrected.

### 4. Propose, ranked by confidence
Apply NOTHING yet. Present every surviving signal as a proposal, ranked:
- **HIGH** — 2+ explicit same-direction corrections.
- **MEDIUM** — 1 explicit correction, or a strong repeated pattern.
- **LOW** — an inferred preference.

Each proposal shows: the **verbatim quoted signal(s)** from the session, the **target skill**, and
the **exact edit** (before → after, or the new line to add).

### 5. Apply only approved edits
The user approves selectively — all, some, or none. For each approved edit:
- One commit, path-scoped staging of that skill's folder only (silent-git contract — never a
  repo-wide add, never push, never rewrite history).
- Add a CHANGELOG.md line: `[YYYY-MM-DD] Learned from session: <what>`.

**Declined signals are discarded** — never queued, never re-proposed from memory.

### 6. Static skills
A skill with `static: true` in its frontmatter still gets proposals here (proposals are proposals by
definition), and **approved edits ARE applied**. The static flag guards self-modification during
*annealing*, not deliberate user-approved edits — state this distinction if the user asks why a
static skill is being edited.

## Worked example

Session: the user corrected a report skill's output format twice.
- First: `"put the summary table first"`
- Later: `"again — table first, then commentary"`

Two explicit same-direction corrections → **one HIGH proposal**:

> **HIGH — target skill: `weekly-report`**
> Signals (verbatim): "put the summary table first" · "again — table first, then commentary"
> Edit — in the "Output order" section:
> before: `Lead with the narrative commentary, then the summary table.`
> after: `Lead with the summary table, then the narrative commentary.`

Nothing is applied. On approval → one commit scoped to `weekly-report/`, plus
`[2026-07-15] Learned from session: summary table leads, commentary follows`. If declined, the
signal is dropped.

## Scenario checks (these must hold from this text alone)

- Two same-direction corrections → exactly one HIGH proposal quoting both; nothing applied before
  approval.
- A single offhand phrasing → no proposal, or LOW at most.
- A correction already encoded in the target skill → no proposal (you read the skill in step 2).
- Approval applies exactly the approved subset — no more, no less.

## Gotchas

- **Read the target skill before proposing.** Do not propose an edit that merely restates content
  the skill already contains — that is the top false-positive.
- Attribute to exactly one skill; if a signal spans two, propose against whichever owns the corrected
  output, not both.
