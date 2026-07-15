---
name: [skill-name-kebab-case]
description: [TRIGGER MECHANISM, not a summary. Write it so Claude fires the
  skill at the right moment: activation keywords + "Use when…" phrasing.
  Bad:  "Generates cold outreach emails."
  Good: "Write cold outreach that gets replies. Use when drafting a cold email,
         LinkedIn DM, or first-touch message to a prospect. Triggers on: cold
         email, cold outreach, first-touch, prospecting message."]
# static: true   # OPTIONAL. Default (this line absent) = self-annealing ON:
#                # the skill fixes itself on failure (see Improvement protocol).
#                # Set static: true to freeze the skill — it never self-modifies,
#                # and you MUST delete the Improvement protocol block below.
---

<!--
HOW TO USE THIS TEMPLATE
The frontmatter block above MUST stay the first thing in the file — harnesses
parse it only at the top. Fill every [bracketed] slot, then delete the guidance
comments. A finished SKILL.md teaches Claude to think like an expert at this
task — it is not documentation. Say WHY, not just WHAT. Cut anything that
doesn't change output.

SCOPE: One capability per skill. If a piece of logic would be reusable in
another workflow, split it into its own atomic skill and reference it by name
(see taxonomy.md, the one-or-many rule). Keep SKILL.md under 500 lines; move
deep material into references/ one level deep, loaded on demand.
-->

# [Skill Name]

<!--
OPENING (2-3 sentences): frame the problem and what Claude gets WRONG by
default. Establish the domain's voice. Do NOT restate what Claude already
knows how to do — only what it needs that it wouldn't reach for on its own.
-->
[What this makes Claude good at, and the default failure it corrects.]

## Instructions

<!--
DEGREES-OF-FREEDOM MATCHING — the core authoring choice:
- Judgment / interpretation / adapting to context  → PROSE. State the
  principle and the WHY; let Claude adapt. Don't script what needs thinking.
- Fragile / deterministic / exact operations (commands, API calls, file
  paths, formats) → EXACT text or a script in scripts/. Don't paraphrase what
  must be literal; a wrong flag fails silently.
Match the specificity of your writing to how much the agent should adapt.
-->
[Principles and process. Prose where the agent should think; exact commands or
`scripts/<name>` where the operation is fragile.]

## Gotchas

<!--
MANDATORY. Scaffolded at birth — never delete this section. This is where the
skill's hard-won knowledge accumulates: the non-obvious failure modes, the API
that lies about its rate limit, the input format that looks fine but breaks.
Every anneal adds a line here. Start with one placeholder until you hit the
first real one.
-->
- [Known trap and how to avoid it — replace this line with the first real gotcha.]

## Improvement protocol

<!--
OMIT THIS ENTIRE SECTION when frontmatter has `static: true`.
This block is what the skill CARRIES WITH IT when it graduates out of the
factory — its self-annealing contract, readable with zero prior context.
-->
When this skill fails during a run:
1. Fix the immediate problem so the current run succeeds.
2. Re-run the exact failing case; confirm it now passes before continuing.
3. Add a `## Gotchas` line capturing the trap so it can't recur.
4. Append one line to `CHANGELOG.md`: `[YYYY-MM-DD] What changed and why`.
5. Commit once — one anneal, one commit — touching only this skill's folder.

Skip this loop for one-off environmental failures (network timeout, rate
limit, disk full) — those aren't skill bugs. Escalate to the user when the fix
is uncertain, or when it would reach outside this skill's own folder.

## Changelog

Changes live in `CHANGELOG.md` in this folder — one line per change:
`[YYYY-MM-DD] What changed and why`. Keep them out of this file so the context
window stays lean.

## Cases

This skill owns a `cases/` directory. At birth it holds one baseline pair:
`cases/baseline/input.md` (the frozen sample input) and
`cases/baseline/output-baseline.md` (Claude's no-skill output on that input).
The with-skill test re-runs the same `input.md` and is judged against the
baseline. Annealing adds a `cases/<name>/` for each failure it fixes, so the
skill regression-tests itself over time.
