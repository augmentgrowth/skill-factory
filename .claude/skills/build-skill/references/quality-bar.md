# Quality bar — audit checklist

Run this against every draft at Step 4 and again before the done gate. A draft that fails any
item is not ready — fix it, don't ship it.

The authoring rules themselves live in one place, the factory rubric
(`../audit-skill/references/rubric.md`) — the same rubric `audit-skill` audits existing skills
against and `graduate-skill` gates on. It was last refreshed 2026-10-02 against Anthropic's skill
authoring best practices, the Claude Code skills docs, the Agent Skills spec, the current-model
prompting pages, and OpenAI's Codex skill-creator. This file adds only what the factory's own
process requires on top of it.

- [ ] **Lint is clean of `fix` findings.** Run
      `python3 "${CLAUDE_SKILL_DIR}/../audit-skill/scripts/lint_skills.py" <skill-folder>` (stdlib only, no install) and
      resolve every `fix`; judge every `check`. It covers the mechanical rubric rules: name and
      description limits, size, nested or orphaned references, Contents lists on long references,
      shouty language, undeclared script dependencies.
- [ ] **Rubric judgment rules pass.** Walk the rubric's judgment rules against the draft — above
      all the seven core ones: Contents lists (C4), strictness matches fragility (D1), target model
      and current-model writing (G1–G5), size and reference links (C1–C3), checklist with loop-back
      for ordered jobs (E1), concrete check loop where quality matters (F1), install line next to
      every script (H1).
- [ ] **Description is a trigger, not a summary.** Third-person what, an explicit "Use when…",
      the phrases a builder would actually say, and a boundary where a neighbouring skill could
      misroute — but no exhaustive catch-all lists, which attract unrelated requests (rubric A3).
      Missing trigger conditions is still the top reason skills fail to load.
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
- [ ] **Portable core.** Authoring stays on `name`, `description`, `metadata`, and plain markdown
      so any SKILL.md-compatible harness stays compatible. The factory's `static:` flag is ignored
      by Claude Code and Codex at runtime but rejected by strict upload validators (claude.ai, the
      Skills API) — strip it from any copy uploaded there.
