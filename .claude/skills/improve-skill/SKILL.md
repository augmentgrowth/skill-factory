---
name: improve-skill
description: >-
  The factory's error-driven improvement loop. Fires when a skill failed, errored, or produced
  wrong output during real use — "fix this skill", "the skill broke", "that skill is wrong",
  "anneal this", "why did this fail", "make it self-heal". Also invoked automatically by the
  factory agent whenever a factory-built skill errors mid-task. Runs the bounded anneal
  transaction: capture the failing case, fix, replay, one commit — or roll back and escalate.
  Not for building new skills (build-skill) or graduating them (graduate-skill).
---

You are annealing one failing skill. The whole thing is a bounded transaction: at every exit the
target skill's folder is either genuinely fixed (one commit) or byte-identical to its last good
state — never a half-edited middle. Run these steps in order. Stop the instant a stop condition
fires; do not improvise past it.

## Step 1 — Static check FIRST

Read the failing skill's `SKILL.md` frontmatter. If `static: true`, this skill never self-edits:
diagnose the failure, write the builder a plain-language **fix proposal** (what failed, why, the
exact edit you would make), and STOP. No commits to the skill body, no annealing. Absent flag =
annealing on; continue.

## Step 2 — Preflight

1. Run `git status`. List every uncommitted path. If any path lies **outside the target skill's
   folder**, or looks like another session's in-progress work, STOP: name the stray files in plain
   language and ask before doing anything. Never anneal over someone else's dirty files.
2. Classify the failure. **Environmental** — network timeout, rate limit, disk full, transient auth
   — is NOT a skill bug: log a one-line note ("skipped anneal: rate limit, not a skill defect") and
   STOP. Only genuine skill bugs (wrong logic, stale endpoint, bad parse, missing step) proceed.

## Step 3 — Capture the failing case BEFORE any fix

Serialize the failure so it survives any later rollback:

1. Create `cases/<YYYY-MM-DD>-<slug>/` inside the skill folder.
2. `input.md` — the exact input plus invocation context needed to reproduce the failure.
3. `expected.md` — observed-vs-expected notes, or a judgment rubric describing what correct output
   looks like. (Comparison is always judgment/rubric-based, never a byte-diff.)
4. Stage this folder **by explicit path** (that skill's folder only — never a repo-wide `add`) and
   commit it: `Capture failing case for <skill>: <slug>`. **This commit is never reverted** — the
   fixture is the permanent record even if the fix is thrown away.

## Step 4 — Fix → replay loop (max 3 attempts)

Repeat up to 3 times:

1. Fix the immediate problem — the script, a `SKILL.md` instruction, or a reference file.
2. **Replay:** invoke the skill explicitly against this case's `input.md` (name the skill or point
   the agent at its `SKILL.md`; do not rely on the `/` menu — see Gotchas). Judge the output against
   `expected.md`.
3. Green → go to Step 5. Red → increment the attempt count and loop. After the 3rd red → Step 6.

## Step 5 — On green: ONE commit

Stage the skill folder **by explicit path** and make a single commit containing all three:

- the fix,
- a new entry under `## Gotchas` in the skill's `SKILL.md` capturing what was learned,
- one appended line in the skill's `CHANGELOG.md`: `[YYYY-MM-DD] What changed and why`.

**One anneal = one commit.** Do not tag — a successful anneal is not a known-good milestone (tags
are set only at creation-done and graduation). Report a one-line plain-language summary. Done.

## Step 6 — On exhaustion (3 red) or uncertainty at any point

If the loop exhausts, or at any point you are unsure the fix is correct or it would reach outside
the folder:

1. **Path-scoped restore** the skill folder to its last good state — prefer the latest
   `<skill>/known-good-<n>` tag if the recent commits are suspect, else the last good commit:
   `git checkout <ref> -- <skill-folder>` (or `git restore --source=<ref> -- <skill-folder>`). Folder
   only. **Repo HEAD never moves**, and the Step 3 case commit stays intact.
2. Commit the restore as a **new** commit (never rewrite history).
3. Escalate in plain language: what failed, what you tried across the attempts, and the options now.
   No git vocabulary reaches the builder.

## Bounds (do not cross)

- Only the failing skill's **own folder** is ever modified.
- The original failing case must **replay green** before any fix is committed.
- **Environmental failures are skipped**, not annealed.
- **Escalate** when the fix is uncertain or would reach outside the folder.
- **Never push. Never rewrite history.** Commits are local-only.

## Audit vocabulary (translate git, never expose it)

The builder speaks plain English, never git. Handle these directly:

- **"What changed?" / "What changed this week?"** — read `git log` scoped to the skill folder
  (`git log -- <skill-folder>`, add `--since=...` for a window). Translate each commit to one
  plain-English line. No hashes unless asked.
- **"Undo that" / "go back to yesterday's version."** — path-scoped restore of the skill folder to
  the requested point (a commit, tag, or date), committed as a **new** commit. Confirm in plain
  language ("Reverted <skill> to yesterday's version"). Never show the git command; never rewrite
  history; repo HEAD stays put.

If git is unavailable (degraded mode), you cannot capture cases or commit: fix and replay normally,
skip the git steps with a plain one-line notice, and note the retrofit for when git returns.

## Gotchas

- **Replay by explicit invocation, not the `/` menu.** A skill edited (or newly created) mid-session
  may not hot-load into the `/` menu; replay reliably by naming the skill or pointing the agent at
  its `SKILL.md`.
- **The case commit is sacred.** Steps 3 and 6 must never stage or revert it together with the fix —
  it is its own commit precisely so a rollback keeps the fixture.
