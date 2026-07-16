# Frozen baseline task — fable-codex

## Invocation context

- **Guinea-pig repo:** `/Users/malachirose/code/agents` (the pm-agent lives in `pm-agent/`)
- **Frozen pre-task commit:** `6eec1b8506faea64ba501f7768863924ba466ce1` (branch `feat/pm-agent-capture-reenable`)
- **Run protocol (KTD9):** each benchmark pass runs in a disposable git worktree cut from the frozen commit (`git worktree add <tmp> 6eec1b8...`), and the worktree is discarded after the diff + summary are captured. The repo itself is never mutated.
- **Baseline pass:** Claude Fable only — no fable-codex skill, no codex CLI, no Sol/Luna.
- **With-skill pass (U6):** same task text verbatim, fable-codex explicitly invoked.

## Task (verbatim — do not edit between runs)

In the pm-agent (`pm-agent/` inside this repo), proposal records are created with free-string `kind` values scattered across modules — e.g. `triage_recategorize` and `triage_file_label` in `pm_agent/triage.py`, `tier_graduation` in `pm_agent/anneal.py`, `capture_which_team` / `capture_file` / `capture_maybe` in `pm_agent/capture.py`, `freeform_request` in `pm_agent/replies.py`. Nothing validates `kind` at creation time, so a typo or an unregistered new kind flows silently into the proposal store and downstream consumers (triage, replies, anneal) that assume specific kinds.

Introduce a validated registry of proposal kinds:

1. A single `VALID_PROPOSAL_KINDS` constant in `pm_agent/proposals.py` listing every kind currently created anywhere in the codebase.
2. Validation in `ProposalStore.create()` that rejects an unknown `kind` with a clear, actionable error, following the repo's existing validation conventions.
3. Call sites and/or downstream consumers reference the registry rather than re-hardcoding strings where that improves consistency (use judgment; smallest complete change).
4. Tests: rejection of an unknown kind, and acceptance of every registered kind (existing behavior for valid kinds must not change).

Run the pm-agent test suite (pytest, `pm-agent/tests/`) and leave it fully green.
