---
name: audit-skill
description: Audits existing skills against current Anthropic and OpenAI skill-authoring guidance,
  reports per-rule evidence with exact fixes, and applies only the fixes the builder approves. Use
  when someone says "audit my skills", "check my skills against best practices", "skill best
  practices", "review this skill", "are my skills up to date", "improve my skills", or points at a
  skills folder in any repo.
  Not for a skill that just failed in use (improve-skill) or for building a new one (build-skill).
public_safe: true
metadata:
  target-models: "claude-opus-5-5, claude-sonnet-5-5, claude-fable-5-1"
---

# Audit skills

Without this skill, an audit is a vibe check: a few generic suggestions, no evidence, and edits
made before anyone agreed to them. This skill makes it a report the builder can act on — every
rule judged with a file:line, every fix written out exactly — and changes nothing until the builder
picks what to apply. It works on any skills folder, factory-built or not, in any repo.

The rules live in [references/rubric.md](references/rubric.md). Read it before judging anything.

## Checklist

Copy this into your response and tick it off:

```
Audit progress:
- [ ] 1. Scope resolved, skills listed
- [ ] 2. Lint run over the scope
- [ ] 3. Every skill judged against the rubric
- [ ] 4. Report delivered, changes ranked, builder asked which to apply  ← stop here
- [ ] 5. Approved changes applied, nothing else
- [ ] 6. Each changed skill verified (if anything regressed, go back to step 5 for that skill)
- [ ] 7. Each changed skill saved, summary given
```

## 1. Resolve scope

Default scope is every skill in the current repo: folders holding a `SKILL.md` under
`.claude/skills/`, `.agents/skills/`, or `skills/`. If the builder names one skill or a folder, audit
only that. Follow links: a skill folder that is a symlink is audited at its real location, and that
is where any fix will be saved.

Note each skill's tier: one under `vendor/` or whose frontmatter says `tier: external` is someone
else's skill — report on it, never edit it.

## 2. Run the lint

```
python3 "${CLAUDE_SKILL_DIR}/scripts/lint_skills.py" <scope paths> --json
```

`${CLAUDE_SKILL_DIR}` is this skill's own folder; on harnesses that do not substitute it, use the
folder this SKILL.md lives in. The script is stdlib-only Python 3.10+, needs no install, never
edits anything, and exits 0 whenever the scan completed. Its findings are evidence for the rubric's
mechanical rules, tagged with rule IDs and file:line; its `facts` (line counts, reference files,
scripts, frontmatter keys, target models) save you re-deriving them. If Claude Code's
`claude plugin validate <skills-folder>` is available, run it on the folder that holds the skills:
it catches frontmatter the loader rejects.

## 3. Judge each skill

Read each skill's `SKILL.md`, every file it references, and its scripts — the whole of each, not
excerpts. Then give every rubric rule one verdict: pass, fix, or n.a., per "How to judge a rule"
in the rubric. Mechanical rules start from the lint finding; judgment rules (A3, B1–B6, D1, E1,
F1, G2–G5, H3, I1, J2) need the reading.

For more than three skills, hand each skill to its own sub-agent so the reading stays out of your
context: give it the skill's path, the rubric's path, and that skill's lint output, and ask for the
filled table and fix list in the report format below. Collect, then merge.

## 4. Report, then stop

Per skill, a table. Always show the seven core rules, numbered as builders know them, then every
other rule whose verdict is fix. Collapse the remaining passes into one line.

| # | Core rule | Rubric IDs |
|---|---|---|
| 1 | Long references open with a Contents list | C4 |
| 2 | Strictness matches fragility | D1 |
| 3 | Target model named; no older-model writing | G1–G5 |
| 4 | Under 500 lines; references split by area, linked from SKILL.md | C1–C3 |
| 5 | Ordered jobs get a checklist with "go back to step X" | E1 |
| 6 | Quality checked against something concrete, fixed, re-checked | F1 |
| 7 | Install line and import next to every script or library | H1 |

```
### weekly-update  (.claude/skills/weekly-update)
| Rule | Verdict | Evidence | Exact change |
|---|---|---|---|
| 1 · C4 Contents list | fix | references/format.md:1 (164 lines, none) | Insert after line 1: "## Contents" + one bullet per ## heading |
| 2 · D1 Strictness | fix | SKILL.md:41 "post the update to Slack" in prose | Replace with: Run `scripts/post.py --dry-run`, show the builder, then run without --dry-run |
| 3 · G2 Shouting | pass | SKILL.md:12, :58 — 2 emphatic words, both on the one irreversible step | — |
| ... |
| A3 Description | fix | SKILL.md:3 no "Use when" clause | Append: "Use when writing the Monday update from a channel export." |
Also pass: A1 A2 A4 B2 B3 C5 C6 J1. n.a.: H2–H4 (no scripts).
```

Then one ranked list across all skills, numbered so the builder can answer with numbers:

```
1. [P1] weekly-update · D1 — Slack post is prose; make it a dry-run-first script call
2. [P2] weekly-update · C4 — add Contents to references/format.md
3. [P3] ad-copy · G1 — add metadata target-models
```

Priority meanings are in the rubric. End with one question: which numbers to apply ("all P1",
"1, 3", "none"). Then stop. Do not edit, stage, or save anything before the builder answers.

## 5. Apply only what was approved

Before the first edit, check each target skill's folder for unsaved work that is not yours (in a
git repo: `git -C <repo> status --porcelain -- <skill-folder>`). If there is any, skip that skill and
say so in plain words; never edit over someone else's work in progress. Unsaved work elsewhere in
the repo is left alone: it does not block the audit, and saving is scoped so it is never swept in.

In a factory build home (the repo has a `githooks/pre-push` hook that runs `release-gate.py`), the
approved edit is a gated change: first tag the skill's current state `<skill>/rollback-<n>` (next
unused number; fetch tags first so the number cannot collide) so "undo that" has a target.

Make exactly the approved changes, as written in the report. Everything else stays byte-for-byte:
no drive-by rewording, no reformatting, no extra fixes you noticed along the way (list those as new
suggestions instead). An edit may tidy only its own seam — deleting a line takes its now-doubled
blank line with it. A description edit keeps every trigger phrase the old one had unless dropping
one was the approved change. A rename updates every place that invokes the skill by name.

A skill marked `static: true` is still edited when the builder approves: static guards
against self-modification, not against deliberate approved edits.

## 6. Verify each changed skill

- Re-run the lint on it. Each approved fix's finding is gone, and no new `fix` finding appeared.
- The frontmatter still parses and the `name` is unchanged (unless renaming was approved).
- If the skill has saved examples (`cases/` or `evals/`), replay one: run the skill on its saved
  input and judge the output against the saved expected output or rubric. It must still meet it.

If any check fails, go back to step 5 for that skill and correct the edit. If you cannot make it
pass, put that skill's folder back exactly as it was before step 5 and tell the builder which change
could not be applied safely and why.

Then show the builder each applied change as a before → after excerpt (a few lines of context each).
If the builder asks for the diff, show the raw diff too — the request wins over the plain default.

## 7. Save

In a git repo, save each changed skill on its own: stage only that skill's folder by explicit path
(`git -C <repo> add <skill-folder>`, never a repo-wide add), commit with a message like
`Audit fixes for <skill>: C4, D1`, and append one line to its `CHANGELOG.md` if it has one
(`[YYYY-MM-DD] Audit: <what changed>`). Never rewrite or amend earlier history.

Publishing depends on whose repo this is:

- **A factory build home** (it carries the release gate): the builder's approval covers publishing,
  as with learn-from-session. Install the gate's hook first exactly as the factory spec says
  (repo-local `git -C <repo> config core.hooksPath githooks`, only when `core.hooksPath` is unset or
  already `githooks`; anything else belongs to another hook manager — say so, never overwrite it).
  Push the branch and the rollback tags together, and tag the pushed state `<skill>/review-<n>`.
- **Any other repo**: save locally, then ask once whether to publish ("Saved on this machine. Push
  them to the shared copy too?"). A team repo may publish straight to everyone's main line, so that
  call is the builder's.

If a push is refused, say once, plainly, that the changes are saved on this machine only. Outside
git, edit the files and say that no version history was kept.

To undo an audit change later: restore that skill's folder from its rollback tag, or, where there
is none, from the version saved just before the audit change — as a new save, never by rewriting
history.

Close with a plain summary: what was applied per skill, what was skipped and why, and any skill
with no saved example to replay (offer to capture one — rubric K1).

Talk to the builder in plain language throughout: "saved", "put back", "published", not git terms.

## Handoffs

- A skill that already fails on its own saved example, before any audit edit, is broken rather than
  out of date: hand it to `improve-skill` instead of patching it here.
- To build a missing skill the audit reveals (one skill doing two jobs → split), use `build-skill`.

## Gotchas

- **Lint findings are evidence, not verdicts.** A Contents list on a lookup-table reference, or
  CRITICAL used as a severity label, can be a pass. Say why when you overrule the lint.
- **Don't fix the rubric into every skill.** Rules marked n.a. stay n.a.; adding a checklist to a
  one-step skill or a feedback loop to a lookup skill is noise, not compliance.
- **Description rewrites are where audits break skills.** Shortening a description drops trigger
  phrases and the skill silently stops loading. Keep the phrases; cut the catch-alls.
- **`model:` in frontmatter is not documentation.** In Claude Code it switches the model; record the
  target under `metadata` → `target-models` instead.
