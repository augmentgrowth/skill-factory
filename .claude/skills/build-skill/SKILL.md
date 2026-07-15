---
name: build-skill
description: Guided flow to turn a recurring workflow into a top-tier, git-tracked
  Claude skill. Use when someone wants to build, make, or create a skill; "turn my
  weekly workflow into a skill", "capture how I do X", "I want a skill for…",
  "automate my recurring task", or describes a repeating task they want on rails.
  Triggers on: build a skill, make a skill, create a skill, skill for, turn this
  into a skill, capture my process. NOT for ordinary coding or debugging, and NOT
  for improving an existing factory skill (that routes to improve-skill).
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

## Step 0 — Preflight (first action)

Before anything else, silently check: is git present, is an identity configured, is
the repo state clean? (Uncommitted files outside the skill folder you are about to
create → stop and ask in plain language; they may be another session's work.)

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
  articulate their workflow DEFAULTS here** (least articulation required).
- **research-backed** — research what great looks like externally, then encode it.
  See `references/research-backed.md`. Needs web tools; **a web-less session falls
  back to describe-first with an explicit notice** — never fabricated sources.

## Step 2 — Baseline capture (before ANY drafting)

The baseline is captured first so the final side-by-side is literal. Do not draft yet.

1. Create the new skill's folder at `.claude/skills/<name>/` — the same tree as the
   factory skills, deliberately: it auto-loads for the with-skill test and is
   git-tracked from birth.
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

Draft from `templates/TEMPLATE_Skill.md` against the quality bar
(`references/quality-bar.md`). Match specificity to fragility: prose where the agent
should think, exact text or `scripts/` where the operation is fragile. Scaffold the
`## Gotchas` section at birth, even if it starts with one placeholder line.

**Credentials are lazy (only if the skill actually needs them):** scaffold a committed
`.env.example` documenting every variable in the skill folder, then set keys up with the
builder — they paste values into `.env` themselves, or you write them **without echoing
or logging any value**. Never commit, print, or repeat a secret. The `.env` is gitignored.

## Step 5 — Self-critique

Run the five checks in `references/self-critique.md` (Voice / Principles / Anti-Pattern
/ Example / Focus) and fix what fails **before showing the builder the draft**. Present
an honest assessment: what improved, what is still weak, what you need answered.

## Step 6 — Side-by-side test (the done gate)

Re-run the **same** frozen `cases/baseline/input.md`, now WITH the skill — by explicit
invocation: read the new `SKILL.md` and follow it. (A mid-session skill folder may not
hot-load into the `/` menu; do not rely on it.) Render **both** outputs side by side:
baseline vs with-skill. **The builder judges.**

- Skill loses or ties → iterate: back to Step 4.
- **This gate REFUSES to close without the side-by-side being shown to the builder.**

## Step 7 — Done + personal install

1. **One commit** (commit 2): the finished skill plus changelog line one, staged by the
   skill folder's explicit path. Then set the first known-good tag `<skill>/known-good-1`
   so a rollback target always exists. Degraded mode: skip commit and tag with the notice.
2. **Offer the personal install.** Copy the skill folder — including `cases/`,
   `CHANGELOG.md`, and `.env.example` if present, but **NEVER** the real `.env` — to the
   harness's personal skills directory (Claude Code: `~/.claude/skills/<name>/`; other
   harnesses per the spec's Harness notes matrix in `CLAUDE.md`).
3. Tell the builder the **factory repo remains the skill's system of record** — that's
   where its history lives and where to come back to improve it (via `improve-skill`).

## Gotchas

- **Hot-load is not guaranteed.** A skill folder created mid-session may not appear in the
  `/` menu; always run the with-skill test by explicit invocation (name it or point the
  agent at its `SKILL.md`), never by relying on the menu.
- **Under Codex, project skills never auto-load at all.** Step 2's "it auto-loads for the
  with-skill test" is Claude-Code-only. Codex does not treat `.claude/skills/` as invocable
  skills (verified 2026-07-15) — the with-skill test there is *always* a direct `SKILL.md`
  read, which is how `AGENTS.md` already routes into every skill. The `.claude/skills/<name>/`
  build location is still correct on both harnesses; only the auto-load rationale is Claude-specific.
- [Grow this from real failures — replace/extend as the flow teaches you something.]
