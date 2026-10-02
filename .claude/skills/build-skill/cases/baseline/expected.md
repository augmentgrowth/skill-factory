# Judgment rubric — replay of build-skill on the baseline input

Replay = follow build-skill end to end against `input.md`, playing the builder as described there.
Judge the *process* and the *skill it produces*; never byte-diff.

## Process
- [ ] Preflight ran first; no factory release-gate hook was installed (the repo has none).
- [ ] The new skill's `cases/baseline/input.md` and `output-baseline.md` were written **before** any
      draft, and saved on their own as the birth save.
- [ ] The type was named (workflow or knowledge) and the one-or-many split decided before drafting.
- [ ] Step 5 ran the lint and the independent rubric review on the draft, and every P1/P2 finding was
      fixed (or explicitly argued down) before the builder saw anything.
- [ ] The side-by-side (baseline vs with-skill, same input) was shown and the builder judged it
      before the done save; a loss or tie went back to drafting.
- [ ] The done save touched only the new skill's folder; nothing was pushed without the remote being
      the builder's; no git vocabulary reached the builder.

## The skill it produces
- [ ] Frontmatter parses as YAML; description is third person with "Use when…", real trigger phrases,
      and a boundary; `metadata` → `target-models` is set.
- [ ] Lint: zero `fix` findings.
- [ ] Encodes what Claude would not do by default (verdict vs the $65 target first, five bullets, each
      ending in an action, no tables, no hedging) — and does not explain what CPA is.
- [ ] Has a concrete check of the draft against those house rules before handing it over (rubric F1).
- [ ] `## Gotchas` present; `CHANGELOG.md` line one written.
