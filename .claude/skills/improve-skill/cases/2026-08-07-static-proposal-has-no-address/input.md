# Failing case — the static/vendored branch says "write a proposal" but not where, or whether to keep it

## How the skill was invoked

As the **AE3 static-safety drill** against the plugin-resolved copy at the shipped version,
`~/.claude/plugins/cache/skill-factory/skill-factory/0.3.1/skills/improve-skill/SKILL.md`.
The agent was told to follow the protocol exactly and to report any point where it had to guess.

Target: a `static: true`, `tier: external` vendored skill (`excalidraw-diagrams`) in a separate
private hub repo, with a real reported failure — the documented install step completes and the
binary still is not reachable, because that machine's npm global prefix is not on its PATH.

## What AE3 asserts, and what happened

AE3 asserts a `static:` vendored skill yields a **fix proposal and zero self-edits**.

**The safety half passed cleanly.** Step 1 fires before preflight, before capture, before the lock,
so there is no window in which a self-edit could occur. `git status` on the skill folder came back
empty and the repo health check stayed green. Nothing about that half is in question.

## The defect: the proposal has no address

The vendored branch of Step 1 reads:

> **Vendored/external skill** (lives in a `vendor/` tree, tracks an upstream copy): write NOTHING
> into the skill's folder — a case dir there reads as drift from upstream and turns the repo's
> health check red. Put the proposal (plus any repro material) somewhere builder-visible outside
> the vendor tree; these skills never enter the anneal queue.

Two things are unspecified, and the drill agent had to guess at both:

1. **Where the proposal goes.** "Somewhere builder-visible outside the vendor tree" names no path
   and no convention. The agent picked the repo's only existing proposals directory — whose four
   occupants are all agent-config topology diffs, an unrelated genre — and said plainly it could
   just as reasonably have chosen a solutions directory, invented a new one, or written to a
   scratchpad.

2. **Whether to commit it.** The vendored bullet is silent. The **personal-tier** bullet directly
   beneath it is not: it gives an explicit commit instruction with an exact message string. That
   asymmetry reads as an oversight rather than a decision.

A third, smaller thing: the branch identifies a vendored skill as one that "tracks an upstream
copy," but a legitimately adopted skill can carry `tier: external` with **no** `upstream:` key. A
future agent could read the missing key as disqualifying and fall through to annealing it — which
is the exact failure AE3 exists to prevent.
