---
name: fable-codex
description: Two-model coding loop — Claude orchestrates, GPT-5.6 Sol argues plans
  and reviews code, GPT-5.6 Luna implements, all through persistent codex CLI
  threads. Default-on for any non-trivial coding task when planning, implementing,
  reviewing, or fixing — not just when asked to delegate. Use when building a
  feature, executing a plan, refactoring across files, or fixing a real bug.
  Triggers on: implement, build, refactor, fix, code review, plan review, delegate
  to codex, second model, sol, luna, two-model verification. NOT for trivial edits,
  pure Q&A, or single-file mechanical changes.
---

# Fable-Codex — two-model orchestration loop

By default, an orchestrating Claude does everything itself: it writes the plan, implements it, and
approves its own work — one model, one blind spot, premium tokens spent on labor. This skill runs a
structured loop where a second vendor's models argue back: Sol (GPT-5.6, xhigh) adversarially
reviews plans and code in persistent codex threads, Luna (GPT-5.6) implements, and you — the
orchestrator — arbitrate every gate, fix defects directly, and own the final answer. Two models
catch what one misses; most of the labor moves onto the codex subscription.

## Applicability test (run this first)

Run the loop for any task with real design or defect surface: multi-file changes, behavior changes,
anything a reviewer could meaningfully argue with. **Opt out** and just do the work directly when
the task is trivial — a typo-class fix, pure Q&A, a single-file mechanical change, or anything where
the loop's overhead exceeds the task. When you opt out, say so in one line ("skipping the fable-codex
loop: trivial change").

The loop assumes a git repo. Its content is sent to OpenAI via codex; preflight refuses repos listed
in `~/.fable-codex/denylist`.

## Stage 0 — Preflight

Run `scripts/preflight.sh` from the target repo (first run in a while: `scripts/preflight.sh
--probe-model gpt-5.6-sol`). Exit 0 → proceed. Any failure names the exact blocker (codex missing,
unauthenticated, model rejected, repo denylisted) — announce **degraded mode** to the operator and
run the whole task under `references/claude-tier-fallback.md` instead: same stage shape, Claude-tier
seats, no codex. The fallback charter also governs incidental subagent work (scouting, log reading)
throughout a normal loop.

Pick a short `<deliverable>` slug for this task (e.g. `auth-retry-fix`). All thread state keys off
it; `scripts/codex-thread.sh reviewer show <deliverable>` displays it, and `... reset <deliverable>`
clears it for a clean restart.

## Stage 1 — Plan (author or ingest)

- **A plan document already exists** (e.g. a `docs/plans/*.md` artifact from a planning workflow):
  ingest it — do not re-author. Enter at Stage 2, or at Stage 3 if the operator says the plan is
  already vetted/approved.
- **No plan:** investigate the repo and write the smallest executable plan that fully satisfies the
  task — required behavior and acceptance criteria, files to change, sequence, tests and validation
  commands, non-goals, risks. Do not touch implementation files yet.

## Stage 2 — Sol plan review (persistent thread, cap 3)

Fill the **plan-review round-1** template from `references/sol-review-prompts.md` and pipe it to:

```bash
scripts/codex-thread.sh reviewer start <deliverable>
```

Parse the result with `scripts/extract-verdict.sh` on the printed message (missing verdict = treat
as REVISE). Then loop:

- `VERDICT: REVISE` → treat findings as **claims, not orders**: verify each against the repo,
  revise the plan where Sol is right, and prepare `IMPLEMENTER_NOTES` for anything you're keeping
  deliberately. Send the **round-2+ incremental** template via
  `scripts/codex-thread.sh reviewer resume <deliverable>`.
- `VERDICT: APPROVED` → Stage 3.
- **Round cap 3** (override only if the operator asked): cap hit without APPROVED → stop and
  escalate — present the surviving blockers with Sol's evidence and your position, and ask the
  operator for direction. Never run an open-ended review loop.

## Stage 3 — Luna implements (workspace-write)

Fill `references/luna-implement-prompt.md` with the task + approved plan and pipe it to:

```bash
scripts/codex-thread.sh implementer start <deliverable>
```

Network is OFF by default; add `--network` only when the plan needs dependency installs, and then
report the run's outbound activity in the completion report. If Luna reports a blocker, resolve it
yourself if it doesn't change scope (one `implementer resume` follow-up allowed), otherwise escalate
to the operator.

## Stage 4 — Integrate: read the diff yourself, fix directly

Read Luna's full diff against the plan and the pre-task state (`git diff` **plus** `git log` for
anything Luna committed — committed work is invisible to `git diff HEAD`; Luna is told not to
commit, but verify). Check behavior, edge cases, error paths, security, conventions, accidental
changes. **Fix defects directly in your own edits — do not round-trip fixes back to Luna.** Simplify
overbuilt code; add nothing speculative.

## Stage 5 — Test gate

Run the strongest practical validation the repo supports: focused tests for changed behavior, then
lint/type/format checks, then broader tests proportionate to the change. Relevant tests must pass
before review. A failure that is demonstrably pre-existing and unrelated: record the evidence and
continue; anything else: fix it (back to Stage 4). Record exact commands + outcomes — they feed the
review prompt's TEST EVIDENCE block.

## Stage 6 — Sol code review (persistent thread, cap 3)

Fill the **code-review round-1** template and pipe to `scripts/codex-thread.sh reviewer start
<deliverable>-code` (a separate thread from plan review). Loop exactly as Stage 2, with the
code-review vocabulary (`CHANGES_REQUIRED` instead of `REVISE`):

- Findings are claims: verify each against the code before acting. Fix what's real (Stage 4 rules),
  rebut what isn't in `IMPLEMENTER_NOTES`, re-run affected tests, then
  `scripts/codex-thread.sh reviewer resume <deliverable>-code` with the incremental template.
- Cap 3 → escalate with surviving findings, your evidence, and the test state.

## Stage 7 — Fresh-thread final verdict

After the incremental loop reaches APPROVED, run the **final-verdict** template in a brand-new
thread — independent eyes, no debate history:

```bash
scripts/codex-thread.sh reviewer fresh <deliverable>-code
```

`CHANGES_REQUIRED` with material findings → verify; real → fix and re-gate (Stage 4→5), then one
more fresh verdict. A second material rejection → escalate to the operator with both verdicts.

## Stage 8 — Report + closeout handoff

Never claim completion unless the test gate passed and a fresh Sol thread approved. Report:

- what changed (files + behavior), validation commands and results
- final Sol verdict, plus findings Sol raised that you acted on (the two-model evidence)
- network use if `--network` was enabled; pre-existing failures; unresolved risks or open decisions

The loop ends at approved code — commit/PR/merge is deliberately out of scope. Name closeout as the
next step: if the operator has a GitHub closeout skill installed (e.g. `github-autopilot`), invoke
it; otherwise say plainly "ready to commit/PR when you are."

## High-risk stop rule (all stages)

Auth, billing, permissions, security boundaries, migrations, data loss, shared state: no agent —
you included — proceeds through ambiguity here. Stop, surface the question with evidence, wait for
the operator.

## Role separation (absolute)

- Sol reviews; Sol never edits files (read-only sandbox enforced by the scripts).
- Luna implements; Luna never reviews or approves its own work, never commits.
- You arbitrate and fix, but never self-approve: a plan needs Sol's APPROVED before implementation,
  and code needs a fresh-thread Sol APPROVED before completion. In degraded mode the fallback
  charter's Opus-tier reviewer takes Sol's seats — the separation survives the seat swap.

## Overrides

Defaults: Sol = `gpt-5.6-sol` xhigh (all review seats), Luna = `gpt-5.6-luna` (implementation).
Override per invocation with `--model`/`--effort` on any `codex-thread.sh` call when the operator
asks (e.g. `--effort medium` for a cheap round); round cap changes are operator-only.

## Gotchas

- **No-network sandbox breaks dependency installs.** Luna's default run can't fetch packages; a
  plan needing installs either pre-installs deps before Stage 3 or opts into `--network` (and the
  completion report must then note outbound activity).
- **Committed changes are invisible to `git diff HEAD`.** If an implementer commits despite
  instructions, your Stage-4 diff read silently misses that work — always check `git log` against
  the pre-task baseline commit, not just the working tree.

## Improvement protocol

When this skill fails during a run:
1. Fix the immediate problem so the current run succeeds.
2. Re-run the exact failing case; confirm it now passes before continuing.
3. Add a `## Gotchas` line capturing the trap so it can't recur.
4. Append one line to `CHANGELOG.md`: `[YYYY-MM-DD] What changed and why`.
5. Commit once — one anneal, one commit — touching only this skill's folder.

Skip this loop for one-off environmental failures (network timeout, rate limit, disk full).
Escalate to the user when the fix is uncertain or reaches outside this skill's folder.

## Changelog

Changes live in `CHANGELOG.md` in this folder — one line per change.

## Cases

This skill owns a `cases/` directory. At birth it holds `cases/baseline/input.md` (frozen sample
task) and `cases/baseline/output-baseline.md` (the no-skill output). The with-skill test re-runs the
same input and is judged against the baseline; annealing adds a `cases/<name>/` per fixed failure.
