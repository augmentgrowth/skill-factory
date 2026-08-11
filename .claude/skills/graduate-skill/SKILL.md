---
name: graduate-skill
description: >-
  The factory's exit ramp: take a finished, quality-passing skill and install it for real use.
  Fires on "graduate this skill", "install this skill", "ship this skill", "use this skill
  everywhere", "run the eval gate", "benchmark this skill", "efficiency review". Runs the
  mandatory efficiency pass for script-backed skills, offers the optional eval-gate handoff to
  the installed skill-creator plugin, and copies the skill to the personal skills directory while
  the skill's build home stays the system of record. Not for building (build-skill) or fixing
  (improve-skill).
---

You are graduating one skill: moving a factory-built skill into the builder's real workflow. The
build home (the repo the skill was born in — see the spec's "Where skills are born") keeps the
full git history as system of record; the install is a copy. Run the steps in
order. A power user may jump straight to Step 3 (eval gate) alone — honor that without the rest.

## Step 1 — Pre-graduation checks

Confirm the skill is actually done before moving it:

1. **Quality bar.** Run the audit in `build-skill`'s `references/quality-bar.md` (sub-500 lines,
   trigger-shaped description, Gotchas present, references one level deep). Any failure — send it back
   to the builder, do not graduate.
2. **Test coverage.** `cases/baseline/` exists with a captured baseline the skilled output beats.
3. **History hygiene.** `CHANGELOG.md` present with at least line one; `## Gotchas` present.

## Step 2 — Efficiency review (mandatory for script-backed skills)

**Script-backed** = the skill has a `scripts/` folder or any committed executable code. If it has
none, this is a **procedure-only** skill: skip this step entirely, no ceremony, no notice — go to
Step 3.

For a script-backed skill, run the checklist in `references/script-efficiency-review.md` **inline**
against every script (it is not a sub-agent — you read it and apply it here). Rank each finding
CRITICAL / HIGH / MEDIUM / LOW, each with location, issue, why it matters, and a concrete fix.

- **Any CRITICAL finding BLOCKS graduation — and the fix is yours, not the builder's.** Land the fix
  yourself (through `improve-skill` or a direct edit), re-run this step, and continue when it comes
  back clean. Tell the builder plainly that you are fixing something before graduating; never hand
  them the finding as a decision. Example: a seeded N+1 loop calling the API once per item is
  CRITICAL — fix it to one batched call, re-run, proceed.
- **Why this stop survives the review gate.** Graduation is a gated change, so the builder reviews
  its *output* — and output review cannot observe quota exhaustion, a rate-limit ban, or a fetch
  that silently truncates. CRITICAL names exactly those properties. Routing it to the builder would
  hand a technical judgment to the one reviewer structurally unable to make it, so this gate stays
  machine-to-machine. It is not an exception to "ship it, then review the output"; it is a
  correctness check that runs before there is anything worth reviewing. Build-time review already
  fixes every CRITICAL, so one surviving to here is a real defect, not a style disagreement.
- HIGH / MEDIUM / LOW are reported, not blocking. The builder decides.

## Step 3 — Optional eval gate (offered, never required)

Offer a formal eval gate; never force it. It is a **handoff** to the installed official `skill-creator`
plugin skill — do NOT wrap, re-implement, or drive its runners (its own instructions forbid external
test runners wrapping it). Hand it three things and let it own its Evals / Benchmark /
Description-optimization modes:

1. the skill's path,
2. 2–3 realistic test prompts you draft from the skill's `cases/` and its description,
3. the current session's model id.

If the `skill-creator` plugin is **not installed**, skip gracefully: "The eval gate needs the
skill-creator plugin, which isn't installed here — install it from the official marketplace as the
`skill-creator` plugin to run formal evals. Proceeding with graduation without it." Then continue.

A power user may invoke this gate **directly** — "run the eval gate on X" — with none of the other
steps. In that case do exactly this handoff and stop; no guided-flow ceremony, no pre-checks.

## Step 4 — Personal install

Copy the whole skill folder to the personal skills directory named in the spec's **Harness notes**
matrix for the active harness (Claude Code: `~/.claude/skills/<name>/`; cite the matrix rather than
hardcoding for any other harness).

**The copy includes:** `cases/`, `CHANGELOG.md`, the `## Gotchas` section, `.env.example`, and the
Improvement protocol block — **unless the skill's frontmatter is `static: true`**, in which case that
block must be **absent** and no self-modification text ships (the static skill graduates unchanged and
carries no anneal instructions).

**The copy NEVER includes `.env`.** A credential-needing graduated skill prompts on first use to
recreate `.env` from `.env.example` via guided key setup — plain language, and errors never echo key
names or pasted values.

## Step 5 — Build home stays system of record

The full git history lives in the skill's build home, not the installed copy. The installed copy is
a copy: it does not auto-update. Improvements flow back through the build home — anneal or edit
there via `improve-skill`, then re-graduate to refresh the installed copy.

Graduation is a gated change, so bracket it (stage the skill folder by explicit path throughout):
`<skill>/rollback-<n>` on the last accepted state before graduating, `<skill>/review-<n>` on the
graduated candidate. Push the branch and both tags together. Then hand the builder the output
receipt. Add `<skill>/known-good-<n>` only once they accept.

**A rejected graduation needs two undos, not one.** Restore the build home from the rollback tag
*and* reinstall the personal copy from the restored version. The installed copy is frozen — a
build-home-only restore leaves the rejected version live wherever it was graduated to, which is the
one place the builder actually uses it.

## Step 6 — Team sharing (deferred)

Team distribution is out of scope for now — a team-share step will exist later. Do not invent its
mechanics; if asked, say it is deferred and the skill's home stays its build home until then.

## Gotchas

- **The installed copy is frozen at graduation.** It won't pick up later anneals — after a skill
  self-heals in its build home, re-graduate to refresh the personal copy.
- **Static skills graduate without an improvement protocol.** Check `static: true` before copying; the
  anneal block must not travel with a static skill.
- **`.env` never travels.** Only `.env.example` ships; the real `.env` is recreated on first use.
