---
name: improve-skill
description: >-
  The factory's error-driven improvement loop. Fires when a skill failed, errored, or produced
  wrong output during real use — "fix this skill", "the skill broke", "that skill is wrong",
  "anneal this", "why did this fail", "make it self-heal". Also invoked automatically by the
  factory agent whenever a factory-built skill errors mid-task. Runs the bounded anneal
  transaction: capture the failing case, fix, replay, one commit — or roll back and escalate.
  Also fires on "drain the anneal queue", "any skills waiting to be fixed", "work through the
  queued failures". Not for building new skills (build-skill) or graduating them
  (graduate-skill).
---

You are annealing one failing skill. The whole thing is a bounded transaction: at every exit the
target skill's folder is either genuinely fixed (one commit) or byte-identical to its last good
state — never a half-edited middle. Run these steps in order. Stop the instant a stop condition
fires; do not improvise past it.

**Two halves, two owners.** *Capture* (Steps 1-3) belongs to the session that watched the skill
fail — it is deliberately mechanical, takes no lock, and never blocks the builder's real work.
*Anneal* (Steps 5-7) belongs to a background agent running at the skill's own home under a
per-skill lock. Step 4 is the handoff. A session that can do both does both; a session that cannot
spawn a background agent stops after capture and the case waits in the queue.

**The skill you are fixing may live nowhere near where you are standing.** Skills are served
through links, so never assume the current directory is the skill's home — Step 2 resolves it.

**Global rule — no git vocabulary reaches the builder, ever.** Not just in the audit section:
escalations, stop notices, and proposals are all plain language ("I saved the failing example",
not "I committed the fixture"). Git words are for this file, never for the builder.

## Step 1 — Static check FIRST

Read the failing skill's `SKILL.md` frontmatter — reading straight through the serving path is
fine, links read through. If `static: true`, this skill never self-edits: diagnose the failure,
write the builder a plain-language **fix proposal** (what failed, why, the exact edit you would
make), and STOP. No commits to the skill body, no annealing.

Where the proposal and case live depends on the tier:

- **Vendored/external skill.** Identify it by frontmatter and location: `tier: external`, or the
  skill lives under a `vendor/` tree. **A missing `upstream:` key does not disqualify it** — a
  skill adopted in place can be external with no reachable upstream to diff against.

  Write NOTHING into the skill's folder — a case dir there reads as drift from upstream and turns
  the repo's health check red. These skills never enter the anneal queue, so **the proposal file is
  the only record that the failure was ever found**; treat losing it as losing the finding.

  - **Where:** `<repo>/docs/proposals/<YYYY-MM-DD>-<skill>-<slug>.md`. Create `docs/proposals/` if
    absent. `<repo>` is the repo that owns the skill — resolve it now the way Step 2 does
    (`realpath` the serving path, then `rev-parse --show-toplevel`); it is never the repo you happen
    to be standing in. Use this path even when the repo has some other proposals directory for a
    different genre — one predictable location beats a well-reasoned guess, because the next agent
    will guess differently. The date prefix matters: a recurrence with the same slug must not
    silently overwrite the earlier proposal.
  - **Durability:** save it permanently, path-scoped and alone —
    `git -C <repo> add docs/proposals/<YYYY-MM-DD>-<skill>-<slug>.md` then
    `Proposal for <skill>: <slug> (static — not self-edited)`. A proposal left loose in a busy repo
    is one cleanup away from gone, and nothing in the queue will notice it is missing.
  - **Do not save it into the repo when** the repo is not yours to write to (a background run that
    hit stray paths, or another session's branch), **or when the repo publishes** — a public remote,
    or an auto-sync cron that turns a save into a push. A proposal quotes real paths and machine
    detail, and this is the one save in the protocol that happens before any preflight has run.
    In those cases leave the file where it is, tell the builder its location in plain language, and
    say plainly that it is not saved permanently yet.
- **Personal-tier skill carrying `static: true`:** if a case was already captured — you got here
  from the queue — write the terminal marker from Step 7 and commit it alone
  (`Mark case terminal for <skill>: <slug> (static — proposal written)`) so the proposal is not
  re-raised on every sweep.

Absent flag = annealing on; continue.

## Step 2 — Preflight

1. **Resolve the canonical home.** The serving path you found the skill at is usually a link into
   the repo that owns it; the owning repo is where every git operation must run.
   - `realpath <serving SKILL.md>` → the real file. Its parent directory is `<skill-folder>`.
   - `git -C <skill-folder> rev-parse --show-toplevel` → `<repo>`, the skill's system of record.
   - From here, **every git command is `git -C <repo>` and path-scoped to `<skill-folder>`.** The
     session's current directory is irrelevant and must never be assumed to be the home.
   - **Fallback:** if resolution fails — the serving path is not a link, or there is no git repo
     above the resolved file — fall back to the old assumption (the current repo is the home) and
     say so plainly in your report: "I couldn't trace this skill back to its home, so I worked on
     the copy here." Never guess at a different repo.
2. **Preflight the target folder only.** Run `git -C <repo> status --porcelain -- <skill-folder>`.
   Scope it to that one folder: uncommitted work elsewhere in the repo is not this anneal's
   business and must not block it.
   - **Interactive session:** if the check reports paths you did not create — another session's
     in-progress work inside this skill's folder — STOP: name the stray files in plain language and
     ask before doing anything. Never anneal over someone else's dirty files.
   - **Background run:** never ask a question no one is there to answer. Abort quietly, release the
     lock if you hold one, and leave the case queued — the committed case directory *is* the queue
     entry, and the next session picks it up. Log one line.
3. Classify the failure. **Environmental** — network timeout, rate limit, disk full, transient auth
   — is NOT a skill bug: log a one-line note ("skipped anneal: rate limit, not a skill defect") and
   STOP. Only genuine skill bugs (wrong logic, stale endpoint, bad parse, missing step) proceed.
4. **Neither?** If the failure is unclassifiable — the expectation itself is contradictory,
   impossible, or disputed — it is still NOT skipped: capture the case (Step 3) with `expected.md`
   flagged as **disputed** at the top, then go straight to escalation (Step 7, restore not needed —
   you changed nothing). Every non-environmental anneal leaves a case commit, even one you can't fix.
   Likewise, if it is already clear no fix could ever replay green, capture the case and escalate —
   don't burn the 3 attempts for form's sake.

## Step 3 — Capture the failing case BEFORE any fix

Serialize the failure so it survives any later rollback. **Capture takes no lock** — it is a
write to a brand-new directory that nothing else is touching, and it must stay this mechanical so
any session on any harness can do it reliably:

1. Create `cases/<YYYY-MM-DD>-<slug>/` inside `<skill-folder>` (the resolved home, not a copy).
2. `input.md` — the exact input plus invocation context needed to reproduce the failure.
3. `expected.md` — observed-vs-expected notes, or a judgment rubric describing what correct output
   looks like. (Comparison is always judgment/rubric-based, never a byte-diff.)
4. Stage **by explicit path** — `git -C <repo> add <skill-folder>/cases/<YYYY-MM-DD>-<slug>` (that
   case directory only, never a repo-wide `add`) — and commit it:
   `Capture failing case for <skill>: <slug>`. **This commit is never reverted** — the fixture is
   the permanent record even if the fix is thrown away, and it is also the queue entry if no one
   anneals it today.

## Step 4 — Hand the anneal to a background agent

The case is safe on disk. Now decide who fixes it:

- **If this harness can spawn a background agent:** spawn one to run Steps 5-7 against
  `<repo>`/`<skill-folder>`, giving it the case directory path, and tell the builder in one plain
  line that the failure is saved and a fix attempt is running in the background. Your capture
  session is done.
- **If it cannot** (or background work is suppressed): STOP. Say in one plain line that the failing
  example is saved and will be picked up next time the skill is worked on. The case stays queued —
  the next factory session or a scheduled sweep drains it (see *Draining the queue*).

Everything from Step 5 down runs **under the lock** described in *The lock protocol*. Acquire it
before the first fix; release it at every exit.

## Step 5 — Fix → replay loop (max 3 attempts)

Repeat up to 3 times:

1. Fix the immediate problem — the script, a `SKILL.md` instruction, or a reference file. **Fix
   only what the case exercises**; an unrelated defect you notice gets its own case and its own
   anneal, not a ride-along in this commit.
2. **Replay:** invoke the skill explicitly against this case's `input.md` (name the skill or point
   the agent at its `SKILL.md` at its resolved home; do not rely on the `/` menu — see Gotchas).
   Judge the output against `expected.md`.
3. Green → go to Step 6. Red → increment the attempt count and loop. After the 3rd red → Step 7.

## Step 6 — On green: ONE commit

**If the fix touched a script**, first dispatch a **fresh sub-agent** to run the factory's sibling
`graduate-skill/references/script-efficiency-review.md` checklist (it lives with the factory skills,
not necessarily in the annealed skill's repo) against the changed script(s) only. Fold in CRITICAL
fixes that the failing case exercises, then replay once more to confirm green. A finding outside
what this case exercises gets noted for its own case and its own anneal — never a ride-along in
this commit.

Stage the skill folder **by explicit path** (`git -C <repo> add <skill-folder>`) and make a single
commit containing all four:

- the fix,
- a new entry under `## Gotchas` in the skill's `SKILL.md` capturing what was learned,
- one appended line in the skill's `CHANGELOG.md`: `[YYYY-MM-DD] What changed and why`,
- `cases/<YYYY-MM-DD>-<slug>/.annealed` — a one-line marker (`<ISO date> green`) that takes this
  case out of the queue. **No marker, no exit:** an unmarked case is re-annealed forever.

**One anneal = one commit.** Do not tag — a successful anneal is not a known-good milestone (tags
are set only at creation-done and graduation). Release the lock. Report a one-line plain-language
summary. Done.

## Step 7 — On exhaustion (3 red) or uncertainty at any point

If the loop exhausts, or at any point you are unsure the fix is correct or it would reach outside
the folder:

1. **Path-scoped restore** the skill folder to its last good state — the last good commit, or the
   latest `<skill>/known-good-<n>` tag when one exists and the recent commits are suspect (a skill
   born in a hub build home may never have been tagged; the commit path is the normal case):
   `git -C <repo> checkout <ref> -- <skill-folder>` (or
   `git -C <repo> restore --source=<ref> -- <skill-folder>`). Folder only. **Repo HEAD never
   moves**, and the Step 3 case commit stays intact — a path-scoped restore rewrites only files the
   old state knew about, so the case directory survives in place.
2. Write the terminal marker `cases/<YYYY-MM-DD>-<slug>/.annealed` — `<ISO date> escalated: <one
   line on why>` — so the queue does not re-run a case a human now owns.
3. Commit the restore **plus the marker** as a **new** commit (never rewrite history), path-scoped
   as always. Release the lock if you hold one (an escalation straight out of Step 2 never took it).
4. Escalate in plain language: what failed, what you tried across the attempts, and the options now.
   No git vocabulary reaches the builder. In a background run there is no one to escalate *to*
   live — leave the plain-language account in the commit body and stop.

## The lock protocol

One skill anneals at a time. The lock belongs to whoever is annealing — **the capturing session
never takes it.**

1. **Acquire** `<repo>/.anneal/locks/<skill>` by atomic create (fail if it already exists). Content,
   two lines exactly (this is the format the repo's audit tooling parses — do not improvise):
   `pid: <n>` then `started: <ISO-8601 timestamp>`.

   **`<n>` is the pid of the long-lived process doing the anneal** — your agent/session process,
   the one that will still be alive through Step 6. It is **not** the pid of the shell that writes
   the file. Writing that shell's own `$$` from a one-liner is the natural move and it is **wrong**:
   each tool-call shell exits when its command returns, so its `$$` is dead almost immediately, the
   lock is born recording a dead process, and every later liveness check reads it as stale. Read
   your session's pid from the runtime rather than from the shell doing the write. If you cannot
   determine a pid that outlives the acquire command, write `pid: unknown` — never a pid you already
   know will be dead.
2. **Already held by a live holder** → **exit quietly.** Do not wait, do not double-anneal. The case
   stays queued and the holder or a later sweep handles it. "Live" means the recorded `started:` is
   under two hours old **and** the pid does not positively disprove it:
   - pid names a running process → the pid does not disprove liveness; the timestamp still governs.
   - `pid: unknown`, or a pid you cannot check on this platform → same: **treat as live** and back
     off while the timestamp is young. An unverifiable pid is not evidence of death.
   - pid names no running process → dead; go to 3.
3. **Stale** — the recorded `started:` is more than two hours old, **or** the recorded pid is
   confirmed dead → reclaim it: overwrite with your own pid and timestamp, and continue. (Audit
   tooling may also use the lock file's age as a fallback signal when the `started:` line is missing
   or unparseable.)
4. **Release** — delete the lock file — at *every* exit: green, exhausted, aborted preflight, or
   error. A lock outliving its run is the one failure mode that stalls a whole skill.
5. Locks are runtime state, never committed. The home repo ignores `.anneal/locks/`; if it does not
   yet, say so and let the builder's repo add it rather than committing lock files.

## Draining the queue

A factory session may work through everything waiting in the repo it is standing in — "drain the
anneal queue", or just noticing a backlog.

- **A queue entry** is a dated case directory (`cases/<YYYY-MM-DD>-<slug>/`) with **no `.annealed`
  file**. `cases/baseline/` is never a queue entry, and neither is anything undated.
- For each entry, oldest first: run Step 1 (static check), Step 2 (resolve + scoped preflight —
  this is a background-style run, so abort-and-requeue rather than ask), take the lock, then Steps
  5-7. Skip the capture step — the case already exists — and Step 4 is moot: you are already the
  annealing agent, so there is no dispatch decision to make.
- **One skill at a time.** Anything whose lock is held by a live holder is skipped silently and
  stays queued.
- Report at the end in plain language: how many failures were waiting, which are fixed, which still
  need the builder.

## Bounds (do not cross)

- Only the failing skill's **own folder**, at its **resolved home**, is ever modified.
- **Every git command is `git -C <repo>`, path-scoped.** Never rely on the current directory.
- The original failing case must **replay green** before any fix is committed.
- **Environmental failures are skipped**, not annealed.
- **Escalate** when the fix is uncertain or would reach outside the folder — except in a background
  run, which aborts and requeues instead of asking.
- **Never push. Never rewrite history.** Commits are local-only.

## Audit vocabulary (translate git, never expose it)

The builder speaks plain English, never git. Handle these directly:

- **"What changed?" / "What changed this week?"** — resolve the skill's home as in Step 2, then read
  `git -C <repo> log -- <skill-folder>` (add `--since=...` for a window). Translate each commit to
  one plain-English line. No hashes unless asked.
- **"Undo that" / "go back to yesterday's version."** — path-scoped restore of the skill folder to
  the requested point (a commit, tag, or date), committed as a **new** commit. **An explicit undo
  request executes immediately** — ask a clarifying question only when it is genuinely ambiguous
  *which* change to undo, never to confirm one you can identify. Confirm afterward in plain
  language ("Restored <skill> to the version from before that fix"). Never show the git command;
  never rewrite history; repo HEAD stays put.

If git is unavailable (degraded mode), you cannot capture cases or commit: fix and replay normally,
skip the git steps with a plain one-line notice, and note the retrofit for when git returns.

## Gotchas

- **Replay by explicit invocation, not the `/` menu.** A skill edited (or newly created) mid-session
  may not hot-load into the `/` menu; replay reliably by naming the skill or pointing the agent at
  its `SKILL.md`.
- **The case commit is sacred.** Steps 3 and 7 must never stage or revert it together with the fix —
  it is its own commit precisely so a rollback keeps the fixture.
- **Where you are standing is not where the skill lives.** A skill served through a link resolves
  somewhere else entirely; committing from the session's own repo silently edits a copy the real
  skill never sees. Resolve first, then `git -C`.
- **Preflight the folder, not the repo.** A whole-repo status check makes every unrelated bit of
  dirty work in a busy repo look like a blocker, and nothing ever anneals.
- **A background run must never ask a question.** There is no one to answer; the run just hangs.
- **A static skill's proposal is the whole record — give it an address.** Vendored skills never
  enter the anneal queue, so nothing sweeps for a proposal and nothing notices one missing. "Write
  it somewhere visible" is not an instruction: two agents pick two directories and the second never
  finds the first. Name the path, name the filename shape, and say whether to save it. Note the
  asymmetry this cuts against — the safety half of a static failure (never touch the skill folder)
  is easy to specify and easy to verify, so it gets written precisely; the liveness half (the
  builder actually receives the proposal) is neither, so it silently doesn't.
- **The lock's pid must outlive the shell that writes it.** Each tool-call shell exits when its
  command returns, so a lock acquired with that shell's own `$$` records a pid that is dead within
  milliseconds. Every subsequent liveness check then reads the lock as stale and reclaims it — so
  the lock silently stops excluding anyone and two agents anneal the same skill at once, which is
  the exact thing it exists to prevent. Record the session's durable pid, or `pid: unknown`. Found
  by a drill agent that hit it, noticed, and hand-corrected — the protocol had not said whose pid.
  Abort and requeue instead — the queue is the safe default, not a failure.
- **The `.annealed` marker is what ends the loop.** Green or escalated, write it. Without it the
  same case is picked up by every future sweep.
