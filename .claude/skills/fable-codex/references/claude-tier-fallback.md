# Claude-tier delegation charter (absorbed from `/fable-delegate`)

This is the Claude-only routing charter fable-codex inherited from the retired `/fable-delegate`
command. It has exactly two entry points:

1. **Incidental work during a codex loop.** Scouting, log reading, checklist verification, and other
   side work that shouldn't burn main-loop context routes here even while Sol/Luna carry the main
   stages.
2. **Full-fallback mode.** When `preflight.sh` fails (codex missing, unauthenticated, model rejected,
   repo denylisted), the whole task runs under this charter instead of the codex loop. Announce the
   degraded mode to the operator explicitly — name the preflight blocker and say Claude-tier subagents
   are carrying the loop. The stage shape survives (plan → adversarial review → implement → integrate
   → test gate → final review); only the seats change: an Opus-tier subagent takes Sol's reviewer
   seats (fresh subagent for the final verdict), a Sonnet-tier subagent takes Luna's implementation
   seat. No part of this charter requires codex.

## Routing

**The main loop (the orchestrator) owns:** real intent and scope; architecture and approach;
decomposing ambiguous work into ordered, dependency-aware tasks; tradeoffs (speed vs quality vs risk
vs scope); spotting hidden risk; resolving disagreement between agents; reviewing outputs that
matter; the final answer.

**Opus-tier subagents own** the hardest delegated technical work: complex implementation, deep
debugging, cross-module reasoning, architecture review, security-sensitive reasoning, data
consistency, concurrency/caching, and auditing cheaper agents' work for hidden flaws. They reason
deeply; the main loop keeps final authority.

**Sonnet-tier subagents own** normal engineering execution: scoped implementation, adding/updating
tests, medium-complexity debugging, local refactors, following existing patterns, fixing clear
failures, connecting already-designed pieces. Never product calls or architecture changes.

**Haiku-tier subagents own** cheap evidence work: repo discovery, file and log summaries, simple
checks, checklist verification, edge-case scanning, confirming a change matches the plan. They
report facts, never direction.

### Boundary test

- Mostly searching, reading, editing, testing, or verifying → delegate to a cheaper agent.
- Involves intent, design, tradeoffs, risk, disagreement, or final approval → keep it in the main loop.
- Do the work directly only when delegating would cost more than the task itself.

### High-risk areas

Auth, billing, permissions, security, migrations, data loss, shared state, caching, concurrency,
cross-module behavior, public APIs, user-visible workflows. For high-risk work: the main loop makes
the call, an Opus-tier agent handles or reviews the hard technical parts, cheaper agents verify
concrete evidence. No agent improvises here — ambiguity stops and surfaces.

## Return contracts (non-negotiable)

Every delegated task states its output contract up front. Subagents return the contract and nothing
else. A subagent that returns a wall of raw output has failed the task regardless of whether the
work was correct.

- **Scout report (Haiku):** ≤15 lines. Findings as `file:line` refs + one-sentence facts. Never
  paste file contents back; if a file matters, say why and where.
- **Build report (Sonnet):** ≤20 lines. What changed (files + line ranges), what was run to verify,
  pass/fail, anything ambiguous punted upward. Diffs only if ≤30 lines; otherwise summarize.
- **Deep report (Opus):** ≤40 lines. Conclusion first, then reasoning, then evidence refs. No
  exploratory narration.
- **Test/lint runs:** failures only. Passing output is one line: `N passed`.

## Context hygiene

- Grep before read; read ranges, not files; never re-read what's already in context.
- Noisy operations (test suites, log inspection, dependency audits, large-file summarization) run in
  isolated subagents so only the summary reaches the main thread.
- Own output is terse: decisions and diffs, not essays.

## Parallel / serial doctrine

- Fan out read-only work (discovery, summarization, verification, log review) in parallel.
- Serialize anything destructive (edits, migrations, git operations), each verified before the next.
- Never parallelize two agents that write to overlapping files.

## Escalation ladder

- Haiku fails or returns garbage once → retry once with a tighter prompt; fails again → Sonnet.
- Sonnet fails a scoped task twice → stop; escalate to Opus with both failure reports attached.
- Opus and a cheaper agent disagree → the main loop decides. Agents never re-litigate each other.
- Any agent hitting ambiguity in a high-risk area → stop and surface immediately.
- Escalation always carries prior failure evidence forward so the next model doesn't rediscover it.

## Delegation prompt template

Every delegation includes exactly: **Goal** (one sentence), **Scope** (files/dirs in bounds, and what
is explicitly out of bounds), **Contract** (which return format above), **Done means** (the
observable check that proves completion). Nothing else — no background lore, no pasted context the
agent can fetch itself.

## Main-loop spend rules

- Read subagent reports, not subagent transcripts.
- Open a file yourself only when a decision hinges on it.
- About to do more than ~3 tool calls of searching/reading/testing? That's a delegation smell —
  package it and hand it down.
- One clarifying question to the operator beats ten tokens of guessing wrong.

## Final gate

Before answering, confirm: the real request was handled; premium reasoning was spent only where it
mattered; delegated work came back with evidence; non-trivial work was verified; remaining risk is
stated. Final response = what was done or decided, verification result, remaining risk. Nothing else.
