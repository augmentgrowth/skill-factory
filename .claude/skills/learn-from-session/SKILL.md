---
name: learn-from-session
description: >-
  Mines the current session for durable preferences and corrections, then proposes
  confidence-ranked skill edits and applies only the approved ones. Use when someone says
  "learn from this session", "what did you learn", "mine this session", "update the
  skill with what I told you", or asks for an end-of-session review of skill output. Not for
  a skill that failed (improve-skill) or a best-practices audit (audit-skill).
metadata:
  target-models: "claude-opus-5-5"
---

Preference mining is the propose-first half of the dual improvement loop. Error-annealing
(`improve-skill`) runs autonomously because behavior is observable and git rollback is the safety
net; preference mining is judgment, so it is **PROPOSE-FIRST with human approval** — you apply
nothing until the user says so. Where the harness supports session-end hooks, this may run
automatically at session end; on-request invocation is the portable path.

**The approval covers shipping.** It is one gate, not two: the user confirms *what* you understood
about them, and that same yes carries the edit through commit and push. Only the user knows whether
you read them correctly — but once they say so, there is nothing left for a second ask to decide.

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
- **LOW** — an inferred preference, or a single offhand phrasing. An offhand remark never rates
  higher; one aside is not yet a correction.

Each proposal shows: the **verbatim quoted signal(s)** from the session, the **target skill**, and
the **exact edit** (before → after, or the new line to add).

### 5. Apply only approved edits
The user approves selectively — all, some, or none. Before the first git write, run the release-gate
preflight: repo-local `git -C <repo> config core.hooksPath githooks`, only when `githooks/pre-push`
exists *and invokes* `scripts/release-gate.py`, that script exists, and `core.hooksPath` is unset or
already `githooks`. Never `--global`; a different existing value belongs to another hook manager —
escalate rather than clobber. Silent. Full rule: the spec's "Install the hook yourself, in preflight."

For each approved edit:
- Before editing: `git -C <repo> status --porcelain -- <skill-folder>`; if it lists files
  you did not create, skip that skill and say so. `git -C <repo> fetch --tags`, then tag the
  current state `<skill>/rollback-<n>` (next unused n).
- Apply the edit and its CHANGELOG line (`[YYYY-MM-DD] Learned from session: <what>`), then `git -C <repo> add <skill-folder>` and
  `git -C <repo> commit -m "Learn from session for <skill>: <what>" -- <skill-folder>`;
  tag it `<skill>/review-<n>`.
- Publish without asking again:
  `git -C <repo> push origin HEAD refs/tags/<skill>/rollback-<n> refs/tags/<skill>/review-<n>`.
  If refused, say once that it is saved on this machine only.

**Declined signals are discarded** — never queued, never re-proposed from memory. The user
already judged them; proposing one again asks them to say no twice.

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

## Gotchas

- **Read the target skill before proposing.** Do not propose an edit that merely restates content
  the skill already contains — that is the top false-positive.
- Attribute to exactly one skill; if a signal spans two, propose against whichever owns the corrected
  output, not both. Two copies of one rule drift apart the first time either skill is edited.
