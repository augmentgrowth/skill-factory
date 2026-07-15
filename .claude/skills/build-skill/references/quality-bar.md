# Quality bar — audit checklist

Run this against every draft at Step 4 and again before the done gate. Anchors:
Anthropic's "Lessons from building Claude Code: How we use skills" (2026-06-03) and
"The Complete Guide to Building Skills for Claude" (January 2026). A draft that fails
any item is not ready — fix it, don't ship it.

- [ ] **Description is a trigger mechanism, not a summary.** It's packed with the literal
      activation keywords a builder would actually say, plus "Use when…" phrasing. Missing
      trigger conditions is the top reason skills fail to load. A one-line summary of what
      the skill does is a fail.
- [ ] **Never restates what Claude already knows.** Every token spent moves Claude off its
      defaults — domain judgment, house rules, the sharp edges. "Claude already knows how
      to code"; don't re-teach it. Cut anything that reads like general documentation.
- [ ] **Under 500 lines.** SKILL.md stays lean; deep material moves into `references/`.
- [ ] **References one level deep** from SKILL.md. Nested references get partial-read only,
      so anything load-bearing lives one hop away, not two.
- [ ] **Degrees-of-freedom matching.** Prose where many paths are valid and the agent
      should adapt; exact text or a `scripts/` file where the operation is fragile or
      irreversible. A wrong flag paraphrased into prose fails silently — match specificity
      to fragility.
- [ ] **`## Gotchas` scaffolded at birth.** The heading is present even if it holds one
      placeholder line. It's the highest-signal section in a skill; every anneal grows it.
- [ ] **Changelog present.** A `CHANGELOG.md` exists in the skill folder with line one
      written (`[YYYY-MM-DD] What changed and why`), kept out of SKILL.md so context stays lean.
- [ ] **`cases/baseline/` present.** Both `input.md` (frozen sample input + invocation
      context) and `output-baseline.md` (Claude's captured no-skill output) exist and were
      written before drafting — so the side-by-side at the done gate is literal.
- [ ] **Type-appropriate content.** Classified capability / knowledge / workflow per
      `templates/taxonomy.md`, and the skill emphasizes what that type demands
      (exact invocations / decision rules / chaining) rather than the wrong material.
- [ ] **One-or-many applied.** Reusable logic is split into its own atomic skill and
      referenced by name, not inlined.
- [ ] **Credentials lazy and safe** (only if the skill needs them): a committed
      `.env.example` documents every variable, `.env` is gitignored, and no secret value is
      ever committed, logged, or echoed.
- [ ] **Portable core.** Authoring stays on `name`, `description`, and plain markdown so
      any SKILL.md-compatible harness stays compatible.
