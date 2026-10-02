# Skill rubric

The one rubric the factory drafts against (build-skill), gates on (graduate-skill), and audits
against (audit-skill). Rule IDs are stable: `scripts/lint_skills.py` tags its findings with them.

## Contents

- How to judge a rule
- A. Discovery and frontmatter (A1–A4)
- B. Concision and content (B1–B6)
- C. Structure and progressive disclosure (C1–C6)
- D. Degrees of freedom (D1)
- E. Ordered workflows (E1)
- F. Feedback loops (F1)
- G. Model calibration (G1–G5)
- H. Scripts and dependencies (H1–H4)
- I. Examples and templates (I1)
- J. Gotchas (J1–J2)
- K. Evaluation (K1)
- L. Factory extras (L1)
- Sources and refreshing this rubric

## How to judge a rule

Every rule gets exactly one verdict per skill:

- **pass** — the skill meets it. Evidence is still a file:line, so the builder can see why.
- **fix** — it does not. Give the evidence and the exact change: the before text and the after
  text, or the new line and where it goes. "Consider improving" is not a change.
- **n.a.** — the rule cannot apply (no scripts → H1–H3 are n.a.; nothing order-dependent → E1 is
  n.a.). Say why in a few words.

Lint findings are evidence, not verdicts. A `check` finding means a reader must decide; a `fix`
finding is almost always a fix but you may overrule it with a reason (a long reference that is a
lookup table may not need prose headings in its Contents list).

Priority for the ranked change list:

- **P1** — the skill fails to load, fails to trigger, misfires on unrelated requests, or can take a
  consequential action (money, deletion, sending, anything irreversible) without an exact command or
  script. Also: instructions that make current models refuse (G4).
- **P2** — the skill works but wastes context or drifts: structure (C), missing checklist or
  feedback loop where order or quality matters (E, F), undeclared dependencies (H1), shouting (G2).
- **P3** — polish: terminology, time-stamped phrasing, missing target-model note, extra examples.

## A. Discovery and frontmatter

**A1 Name is valid.** 1–64 chars; lowercase letters, digits, single hyphens; no leading or trailing
hyphen; no `anthropic` or `claude`; equals the folder name. Vague names (`helper`, `utils`) are a
fix. Fix shape: rename folder and `name` together, and update anything that invokes it by name.

**A2 Description fits.** Non-empty, ≤1,024 chars, no angle brackets. In Claude Code the description
plus `when_to_use` is cut at 1,536 chars in the skill listing, and listings shrink further when many
skills are installed, so the first sentence carries the load.

**A3 Description triggers well.** It is a trigger, not a summary:

- third-person *what* ("Turns a weekly export into…", never "I can…" / "You can…"),
- an explicit *when* ("Use when…"),
- the phrases a user would actually say and the file types involved,
- a boundary ("Not for…") where a neighbouring skill or common request could misroute,
- no exhaustive capability lists or catch-alls — they attract unrelated requests. Aim for roughly
  500 chars; detailed workflow belongs in the body.

Judge it by imagining five requests that should trigger and three near-misses that should not.

**A4 Frontmatter is portable.** Claude Code and Codex ignore unknown keys, but claude.ai upload,
the Skills API and Anthropic's `package_skill` *reject* any key outside `name`, `description`,
`license`, `compatibility`, `metadata`, `allowed-tools` — and OpenAI's `quick_validate` is stricter
still, rejecting `compatibility` too. Fix: move custom
flags under `metadata` as strings (`metadata:` then `  owner: "growth"`). Exception: the factory's
own keys (`static`, `tier`, `upstream`, `public_safe`) stay top level, because the factory's tools
read and rewrite them there; strip or move them only in a copy made for upload. Claude Code's own keys
(`when_to_use`, `disable-model-invocation`, `context`, `allowed-tools`…) are fine for a skill that
only runs in Claude Code — n.a. unless the builder uploads it elsewhere. Never use `model:` to
document a target model: in Claude Code it *switches* the model for the turn.

## B. Concision and content

**B1 Nothing Claude already knows.** For each paragraph ask: would Claude get this wrong without
it? If not, cut it. General explanations of a well-known tool, language, or concept are a fix.

**B2 One term per concept.** Mixing "export", "report" and "file" for the same thing is a fix.

**B3 No time bombs.** `"Before August 2025 use the old endpoint"` goes stale silently. Fix: state the
current way; put the old way in a collapsed "Old patterns" note if it still matters.

**B4 Standing instructions, important ones first.** Skill text is read once and not re-read on later
turns; after compaction only the first ~5k tokens of a skill survive. One-time steps phrased as if
they will be re-read, or the key rule buried at the bottom, are a fix.

**B5 A default, not a menu.** "You can use A, B, C or D" is a fix: pick one default and give one
escape hatch ("use B only when…").

**B6 Scope stays narrow.** A single example, past failure, or personal preference written up as a
universal rule is a fix: narrow it to the situation it came from.

## C. Structure and progressive disclosure

**C1 SKILL.md under 500 lines** (roughly 5k tokens). Over that, split by area into references.

**C2 References one level deep.** Every reference file links directly from SKILL.md. A file reached
only through another reference may be read partially or not at all.

**C3 Every reference is linked and has a reason to open it.** An orphan file in the skill folder is
invisible. Each link says *when* to read it ("For refunds, read `references/refunds.md`").
References are split by area (one per domain or path), not one grab-bag file.

**C4 Long references open with Contents.** Any reference over 100 lines starts with a Contents list
whose entries match its headings, so a partial read still shows the map.

**C5 Forward slashes in paths.** `scripts\run.py` breaks on every non-Windows harness.

**C6 Links resolve.** A link to a file that is not there is a silent dead end.

## D. Degrees of freedom

**D1 Strictness matches fragility.** For each step ask: what happens if Claude does this
differently?

- Nothing much (wording, ordering a summary, choosing an example) → loose guidance; state the goal
  and the reason. Rigid steps here are a fix (they degrade current models' output).
- Consequential (money, deleting, sending, publishing, anything irreversible or externally visible)
  → an exact command or a script, with the authorization point immediately before the action and a
  stopping condition for any retry loop. Prose here is a P1 fix.

## E. Ordered workflows

**E1 Order-dependent jobs carry a checklist.** When steps must happen in order, give a checklist
Claude can copy into its response and tick off, plus the loop-back line for each check that can
fail ("If the totals don't reconcile, go back to step 2"). n.a. when order does not matter.

## F. Feedback loops

**F1 Quality is checked against something concrete.** Where output quality matters, the skill names
the concrete check — a validator script, a rubric, a reference file, the source data — then fix and
check again, proceeding only when it passes. A generic "double-check your work" is *not* this and is
a fix to remove: current Opus models already self-verify and over-verify when told to.

## G. Model calibration

**G1 Target models recorded.** `metadata` carries `target-models: "<model ids>"` naming the models
the skill was written and tested for, so a later reader knows which model's habits it assumes.
Revisit it when a new model generation ships: the value is a claim about testing, not a setting.

**G2 No shouting.** All-caps `MUST` / `NEVER` / `ALWAYS` / `CRITICAL` scattered through the text was a fix
for older models' under-triggering; current models over-apply it. Fix: plain imperative plus the
reason ("Use the ledger total, because the export double-counts refunds"). Keep emphasis for the
one or two genuinely dangerous rules. A severity label (`CRITICAL` / `HIGH` as data) is not shouting.

**G3 Not over-explained or over-prescribed.** Step-by-step railroading of judgment work, repeated
instructions, and paragraphs of motivation degrade current models. Fix: goal, constraints, reason.

**G4 No "write out your reasoning".** Instructions to show, echo, or transcribe thinking in the
response can be refused on current models. Fix: ask for a short explanation or a summary of the
actions taken.

**G5 Smaller-model safety.** If the skill targets a smaller model (Haiku-class), any step it could
plausibly skip — a check, a file it must read, a script it must run — is explicit or scripted, and
scope is stated outright (newer Sonnet models follow instructions literally). n.a. when the skill
targets only the largest models.

## H. Scripts and dependencies

**H1 Install line next to use.** Every third-party package has its install command and its import
or invocation together where the skill first uses it (`pip install pypdf`, then
`from pypdf import PdfReader`). Never assume a package is installed.

**H2 Run or read is stated.** Each script is mentioned in SKILL.md with whether Claude should run it
("Run `scripts/check.py`") or read it as reference, and when.

**H3 Scripts solve, don't defer.** They handle their own errors with messages that say what to do,
avoid unexplained constants, never prompt interactively, print structured results to stdout and
diagnostics to stderr, and keep output bounded. Consequential scripts offer a dry run.

**H4 MCP tools fully qualified.** Name tools as `Server:tool_name`, not a bare tool name that may
collide.

## I. Examples and templates

**I1 Concrete examples where output matters.** If the output has a house format or a quality bar,
there is at least one real input→output example or a template, and the template says whether it is
strict ("use exactly this structure") or a default ("adapt as needed").

## J. Gotchas

**J1 `## Gotchas` section in SKILL.md.** Present even if short; not hidden in a reference file.

**J2 Gotchas are real and narrow.** Each one names a specific failure and its fix. Generic advice
("be careful with dates") is a fix: make it specific or cut it.

## K. Evaluation

**K1 There is something to replay.** A `cases/` or `evals/` folder with at least one frozen input
and its expected output or rubric, ideally three scenarios including one that should *not* trigger.
Without it, no change can be proven to keep the skill working. Fix: capture one representative input
now (the audit can draft it; the builder confirms it).

## L. Factory extras

**L1 Factory-built skills keep the factory's records.** n.a. for skills the factory did not build.
`CHANGELOG.md` present (a deliberate factory exception to "no README/CHANGELOG in a skill folder" —
it keeps history out of SKILL.md); `cases/baseline/` present; a frozen skill marks it with top-level
`static: true` and carries no Improvement protocol block; credential-using skills ship `.env.example` and never `.env`.

## Sources and refreshing this rubric

Last refreshed 2026-10-02 against:

- Anthropic, Skill authoring best practices —
  platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices (A1–A3, B1–B3, B5,
  C1–C5, D1, E1, F1, H1–H4, I1, K1)
- Claude Code skills docs — code.claude.com/docs/en/skills (A2, A4, B4)
- Agent Skills specification — agentskills.io/specification (A1, A2, A4, C2)
- Anthropic prompting pages for current models (Opus 5 / 5.5, Fable 5 / 5.1, Sonnet 5 / 5.5) —
  platform.claude.com/docs/en/build-with-claude/prompt-engineering/ (F1, G2–G5)
- "Lessons from building Claude Code: How we use skills" (B1, J1–J2) and "The Complete Guide to
  Building Skills for Claude", January 2026 (A3, K1). The guide's advice to add `CRITICAL:` headers
  is superseded by the current-model pages (G2).
- OpenAI Codex bundled skill-creator and `plugin-eval` scorer (A3 boundaries, A4, B6, D1 stopping
  conditions).

To refresh: re-read those pages, change the rule text here, keep the IDs stable, and update
`scripts/lint_skills.py` and its tests if a mechanical threshold moved.
