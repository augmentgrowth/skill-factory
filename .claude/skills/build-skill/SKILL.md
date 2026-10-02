---
name: build-skill
description: >-
  Guided flow to turn a recurring workflow into a top-tier, git-tracked
  Claude skill. Use when someone wants to build, make, or create a skill; "turn my
  weekly workflow into a skill", "capture how I do X", "I want a skill for…",
  "automate my recurring task", or describes a repeating task they want on rails.
  Triggers on: build a skill, make a skill, create a skill, skill for, turn this
  into a skill, capture my process. NOT for ordinary coding or debugging, and NOT
  for improving an existing factory skill (that routes to improve-skill).
metadata:
  target-models: "claude-opus-5-5"
---

# Build a Skill

A builder walks in with a workflow they repeat and walks out with a committed,
tested skill that beats what Claude does by default. Your job is to run the whole
flow — including every git operation — so the builder never learns git and never
sees git vocabulary. By default Claude free-hands "make me a skill" into a generic
SKILL.md with no baseline, no test, no Gotchas. This flow refuses to close until the
skill provably wins side by side. Read `CLAUDE.md` for the full factory
contract; this skill is its executable guided flow.

Run the steps in order. Per-path detail lives in `references/` — load only what the
chosen path needs.

```
Build progress:
- [ ] 0. Preflight passed (or degraded mode announced)
- [ ] 1. Intake path chosen
- [ ] 2. Baseline input + no-skill output saved; birth save made
- [ ] 3. Type named; split decided
- [ ] 4. Draft written; Gotchas scaffolded
- [ ] 5. Lint has no fix findings; six checks pass; independent audit has no open P1/P2 — if not, back to step 4
- [ ] 6. Side-by-side shown; builder judged it a win — if lose/tie, back to step 4
- [ ] 7. Saved, tagged, published; personal install offered
```

## Step 0 — Preflight (first action)

Before anything else, silently check: is git present, is an identity configured, is
the release gate installed, is the repo state clean? (Uncommitted files outside the
skill folder you are about to create → stop and ask in plain language; they may be
another session's work.)

- **Release gate:** a repo cannot install its own hooks, so a fresh clone is
  unguarded until someone does — and the builder is never that someone. Run
  `git -C <repo> config core.hooksPath githooks` (repo-local, **never `--global`**)
  only when all three hold: `githooks/pre-push` exists *and invokes*
  `scripts/release-gate.py`; that script exists; and `core.hooksPath` is unset or
  already `githooks`. Checking the filename alone would arm every hook in a
  stranger's repo; a different existing value means another hook manager owns it —
  escalate, never clobber. Silent, like the identity check. Full rule: the spec's
  "Install the hook yourself, in preflight."

- **Git missing:** offer a guided install (on macOS, the developer-tools prompt).
- **Declined or unavailable:** continue in **degraded no-git mode** — build and test
  the skill normally, skip every commit, and say once, plainly: "I'll build and test
  this now; version history is off until git is set up, then I can save it." Note the
  later retrofit. Never expose git vocabulary in any of this.

## Step 1 — Intake routing

Three paths. Honor an explicit choice; otherwise infer from how the builder talks.

- **describe-first** — the builder can explain the workflow. See
  `references/describe-first.md`.
- **reverse-engineer** — do the task live together, then extract the skill from the
  successful session. See `references/reverse-engineer.md`. **A builder who can't
  articulate their workflow defaults here** (least articulation required).
- **research-backed** — research what great looks like externally, then encode it.
  See `references/research-backed.md`. Needs web tools; **a web-less session falls
  back to describe-first with an explicit notice** — never fabricated sources.

## Step 2 — Baseline capture (before any drafting)

The baseline is captured first so the final side-by-side is literal. Do not draft yet.

1. Create the new skill's folder at `.claude/skills/<name>/` **in the build home** — the
   git repo the builder is standing in (in a cloned factory, that's the clone itself; see
   the spec's "Where skills are born"). It is git-tracked from birth and, on Claude Code,
   auto-loads for the with-skill test. Never create it inside a plugin's managed cache;
   if the current directory isn't a git repo, ask where the builder's skills live before
   falling back to degraded no-git mode.
2. Freeze a sample input. For live-data workflows (paid-media reports and the like),
   use a **pasted representative sample export** — never a live API pull, and no
   credentials in the guided flow. Monday's data isn't Tuesday's; a captured sample is
   the stable fixture.
3. Write `cases/baseline/input.md` (the frozen input plus its invocation context).
4. Produce Claude's genuine **no-skill** output for that input and save it as
   `cases/baseline/output-baseline.md`.
5. Commit this as the skill's **birth commit** (commit 1), staged by the skill folder's
   explicit path only. Degraded mode: write the files, skip the commit with the notice.

## Step 3 — Classify + split (before drafting)

Using `templates/taxonomy.md`, name the type — **capability / knowledge /
workflow** — because the type decides what the skill emphasizes. Then apply the
**one-or-many rule**: any chunk of logic reusable in another workflow becomes its own
atomic skill; a workflow skill chains atomic skills by name rather than inlining them.
Decide the split now, before you write a line.

## Step 4 — Draft

Draft from `templates/TEMPLATE_Skill.md` against the factory rubric
([../audit-skill/references/rubric.md](../audit-skill/references/rubric.md)) and the
quality bar ([references/quality-bar.md](references/quality-bar.md)). `templates/` lives at
the factory's root — in a clone that is the repo root; under a plugin install it is
`${CLAUDE_PLUGIN_ROOT}/templates/`. Three rubric rules shape the draft most:

- **Strictness matches fragility.** For each step ask what happens if Claude does it
  differently: nothing much → prose with the reason; consequential (money, deleting,
  sending, irreversible) → an exact command or a `scripts/` file.
- **Ordered jobs get a checklist** Claude copies and ticks off, with a "go back to step N"
  line wherever a check can fail; **quality-critical output gets a concrete check** (a
  script, rubric, or reference) to fix against and re-run.
- **Write for current models:** plain imperatives with the reason, no all-caps MUST/NEVER,
  no over-explaining, no "write out your reasoning", key rules near the top. Record the
  models you test on in `metadata` → `target-models`.

**Don't teach to the test.** Rules and examples in the skill never quote the sample's data or
the answers computed from it — this week's totals, per-row results, the expected output from
`cases/baseline/input.md`; use a different week, client or sample. Standing rules the builder
states (a target, a threshold, a channel) belong in the skill. A skill that contains its
fixture's answers wins the side-by-side by recall, and the replay proves nothing about next week.

Scaffold the `## Gotchas` section at birth, even if it starts with one placeholder line.

**Credentials are lazy (only if the skill actually needs them):** scaffold a committed
`.env.example` documenting every variable in the skill folder, then set keys up with the
builder — they paste values into `.env` themselves, or you write them **without echoing
or logging any value**. Never commit, print, or repeat a secret. The `.env` is gitignored.

## Step 5 — Self-critique

First run the lint —
`python3 "${CLAUDE_SKILL_DIR}/../audit-skill/scripts/lint_skills.py" <skill-folder>` (stdlib
only, no install; `${CLAUDE_SKILL_DIR}` is this skill's folder — on harnesses that don't
substitute it, use that folder's path) — and resolve every `fix` finding before anything
else; it catches the mechanical misses (limits, nesting, missing Contents lists, undeclared
dependencies) so your own pass can spend its attention on judgment. Then run the six
checks in `references/self-critique.md` (Voice / Principles / Anti-Pattern / Example /
Model Calibration / Focus) and fix what fails.

**Independent audit (every draft).** You wrote the draft, so you are the worst judge of it.
Dispatch a **fresh sub-agent** with only three things: the draft's folder path, the path to
`../audit-skill/SKILL.md` (relative to this skill's folder), and the instruction "Follow this
audit skill's steps 1–4 on that one skill, report only — change nothing, and stop at the
question. Run its scripts rather than trusting them, including feeding any checker a
deliberately bad output — but never run anything that sends, posts, deletes or spends." Fix every P1 and P2 it reports (or say in one line why a finding
does not apply),
re-run the lint, and only then show the builder the draft. P3 items go into the honest
assessment for the builder to decide.

Present the draft **with an honest assessment**: what improved, what is still weak, what you
need answered.

**Script efficiency pass (script-backed drafts only).** If the draft added or changed
anything in `scripts/`, dispatch a **fresh sub-agent** to run the sibling
`graduate-skill/references/script-efficiency-review.md` checklist against those scripts
and return severity-ranked findings only — the pass reads far more than it reports,
which is exactly the context-isolation case sub-agents are for. Fix every CRITICAL and
HIGH before Step 6; note MEDIUM/LOW for the builder. This is the same checklist
graduation re-runs as its gate — catching issues at write time means graduation should
find nothing.

## Step 6 — Side-by-side test (the done gate)

Re-run the **same** frozen `cases/baseline/input.md`, now WITH the skill — by explicit
invocation: read the new `SKILL.md` and follow it. (A mid-session skill folder may not
hot-load into the `/` menu; do not rely on it.) Render **both** outputs side by side:
baseline vs with-skill. **The builder judges.**

- Skill loses or ties → iterate: back to Step 4.
- **Do not close this gate until the side-by-side has been shown to the builder.**

## Step 7 — Done + personal install

1. **In a factory clone, settle publishability first.** A factory clone is a repo whose
   `githooks/pre-push` invokes `scripts/release-gate.py`. Its release gate refuses to publish a
   new skill whose frontmatter lacks `public_safe: true`. Ask the builder once, plainly: "Is this
   skill safe for anyone to see — no client names, private data, or internal detail?" On a yes,
   add `public_safe: true` to the frontmatter; on a no, leave it out and say the skill will stay
   on this machine (or in their private repo). Skip this outside a factory clone.
2. Save the finished skill plus changelog line one, scoped to the folder:
   `git -C <repo> add .claude/skills/<name>`
   `git -C <repo> commit -m "<name>: finished skill" -- .claude/skills/<name>`
   `git -C <repo> tag <name>/known-good-1`
   When the remote is yours: `git -C <repo> push origin HEAD refs/tags/<name>/known-good-1`.
   If the push is refused (a factory clone's gate refuses a new skill without
   `public_safe: true`), say once, plainly, that the skill is saved on this machine only.
   Degraded mode: skip all of this with the notice.
3. **Offer the personal install.** Copy the skill folder — including `cases/`,
   `CHANGELOG.md`, and `.env.example` if present, but **NEVER** the real `.env` (or a personal `config.json`) — to the
   harness's personal skills directory (Claude Code: `~/.claude/skills/<name>/`; other
   harnesses per the spec's Harness notes matrix in `CLAUDE.md`).
4. Tell the builder the **build home remains the skill's system of record** — that's
   where its history lives and where to come back to improve it (via `improve-skill`).
   There is no later migration step.

## Gotchas

- **No sub-agent tool? Use a fresh headless session.** Step 2's no-skill baseline, Step 5's audit
  and efficiency pass, and Step 6's with-skill run each need a session that has not seen this
  conversation. Where the harness cannot spawn sub-agents, start one from an empty folder, granting
  only the folders and tools the step needs — a bare `claude -p "…"` is denied file reads:
  `claude -p --add-dir <skill-folder> --add-dir <factory-skills-folder> --allowedTools "Read" "Grep" "Glob" "Bash(python3:*)" -- "<the instruction>"`.
  Doing the independent audit yourself defeats it; say so if neither route is available. Found by
  the first cold build run, which had no Agent tool and improvised this.

- **Hot-load is not guaranteed.** A skill folder created mid-session may not appear in the
  `/` menu; always run the with-skill test by explicit invocation (name it or point the
  agent at its `SKILL.md`), never by relying on the menu.
- **Under Codex, `.claude/skills/` skills never auto-load.** Step 2's "it auto-loads for the
  with-skill test" is Claude-Code-only. Codex does not treat `.claude/skills/` as invocable
  skills (verified 2026-07-15) — the with-skill test there is *always* a direct `SKILL.md`
  read, which is how `AGENTS.md` already routes into every skill. The `.claude/skills/<name>/`
  build location is still correct on both harnesses; only the auto-load rationale is Claude-specific.
- [Grow this from real failures — replace/extend as the flow teaches you something.]
