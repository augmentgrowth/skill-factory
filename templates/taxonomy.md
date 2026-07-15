# Skill Taxonomy

Every skill is one of three types. Classify before you draft — the type
decides what the skill must emphasize and what it can leave out. Guessing the
type is how skills end up bloated with the wrong content.

## Pre-draft check: one or many?

Before writing anything, apply the **one-or-many rule**:

> If a piece of logic would be reusable in another workflow, it becomes its
> own atomic skill. Workflow skills reference atomic skills by name — they do
> not inline them.

Run this test on each chunk of the work: "Would I want this on its own
somewhere else?" If yes, split it out now. Inlining reusable logic into a
larger skill is the most common way skills rot — you end up maintaining three
copies of the same step. Decide the split first; then draft each piece as the
right type below.

## Capability skills — teach Claude to do something new

Tools, scripts, integrations, APIs. The skill exists because Claude *can't*
do the thing without it, or does it unreliably.

Emphasize:
- **Exact invocations.** Literal commands, flags, endpoints, model IDs. No
  paraphrase — a wrong flag fails silently. Push deterministic/fragile steps
  into `scripts/` (see sub-agent-vs-script.md).
- **API gotchas.** Rate limits, pagination, auth refresh, undocumented quirks.
  These belong in `## Gotchas` and grow with every anneal.
- **Error handling at system boundaries.** What to do when the call fails,
  returns partial data, or times out — retry vs. abort vs. escalate.

Leave out: general explanation of what the tool is. Claude can read a happy-
path doc; the skill's value is the sharp edges.

## Knowledge skills — encode judgment Claude can't know

Company context, domain expertise, house style, the judgment a senior person
carries in their head. The skill exists because the information isn't public
and isn't in the model.

Emphasize:
- **Decision rules.** When to do X vs. Y, with the WHY. Rules that transfer to
  new situations beat a list of past answers.
- **Vocabulary.** The specific terms the domain/company uses, so Claude sounds
  like an insider rather than a generalist.
- **Good vs. bad examples.** Concrete before/after. Contrast teaches faster
  than description.
- **Boundaries of the knowledge.** Where it stops applying — so Claude doesn't
  over-extend a rule into a context it was never meant for.

Leave out: procedure. Knowledge skills teach how to think, not steps to run.

## Workflow skills — orchestrate multi-step processes

A process with several stages: intake → do → check → deliver. The skill exists
to sequence and coordinate.

Emphasize:
- **Chaining, not inlining.** Reference atomic capability/knowledge skills by
  name at each step. The workflow is the conductor; the atomic skills are the
  players. If you find yourself pasting another skill's logic in, stop — that
  logic should be its own skill you call.
- **The sequence and its gates.** What must be true to move from one step to
  the next; where to stop and flag for review.
- **Handoffs.** What each step hands the next, in what shape.

Leave out: the internals of the steps themselves. Those live in the atomic
skills you chain.

## Quick reference

| Type | Exists because | Emphasize |
|------|----------------|-----------|
| Capability | Claude can't do it reliably | Exact invocations, API gotchas, boundary error handling |
| Knowledge | Info isn't public/in-model | Decision rules, vocabulary, good/bad examples, limits |
| Workflow | Process needs sequencing | Chain atomic skills by name, gates, handoffs |
