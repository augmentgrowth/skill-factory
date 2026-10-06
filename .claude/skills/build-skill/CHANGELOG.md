# Changelog

One line per change, newest last. Format: `[YYYY-MM-DD] What changed and why`.

- [2026-07-15] Initial skill created.
- [2026-07-15] Added write-time script efficiency pass to Step 5: script-backed drafts dispatch a fresh sub-agent to run graduate-skill's script-efficiency-review checklist; CRITICAL/HIGH fixed before the side-by-side test.
- [2026-07-15] Build-home model: skills are born in the invoking project's .claude/skills/ (the build home), not necessarily the factory clone; Step 2 and Step 7 updated. Unblocks plugin-path building.
- [2026-10-02] Drafts against the shared audit-skill rubric and runs its lint before self-critique; self-critique adds a model-calibration check; quality bar slimmed to factory-process items with the description rule reconciled (trigger phrases plus a boundary, no catch-all lists). Fixed frontmatter that failed YAML parsing (bare "Triggers on:"), which made Claude Code load this skill with no description.
- [2026-10-02] Audit: Step 7 saves, tags and publishes with exact commands, scoped to the skill folder, and handles a refused push (D1); copyable build checklist with loop-backs (E1); caps removed from non-dangerous lines (G2); target-models recorded (G1); Codex gotcha corrected — only `.claude/skills/` is invisible to Codex (J2).
- [2026-10-02] Evaluator round 1: lint path resolves from the skill's own folder (`${CLAUDE_SKILL_DIR}`); Step 7 asks once whether a new skill is safe to publish and sets `public_safe: true`, so a factory clone's gate no longer silently strands every new skill.
- [2026-10-02] Evaluator round 2: quality bar points at Step 5's lint command (reference files don't get `${CLAUDE_SKILL_DIR}` substituted); "factory clone" defined by its release gate; Codex fallback for the lint path.
- [2026-10-02] Saved baseline case (input + judging rubric) so later changes to this skill can be replayed and proven safe.
- [2026-10-02] Step 5 now dispatches a fresh sub-agent to run audit-skill's report on every draft (the author doesn't grade their own work); P1/P2 findings are fixed before the builder sees the draft.
- [2026-10-02] Gotcha: without a sub-agent tool, the fresh readers in Steps 2, 5 and 6 are headless sessions started from an empty folder (found by the first cold build run).
- [2026-10-02] Headless-session fallback gives the exact working command (a bare claude -p is denied file reads); Step 4 forbids quoting the fixture's answers in the skill (don't teach to the test); the Step 5 independent audit runs the draft's scripts, feeding any checker a bad output — a cold build's checker passed three bad drafts.
- [2026-10-02] 'Don't teach to the test' distinguishes the sample's data and answers (forbidden) from standing rules the builder states, like a target (belong in the skill); the independent auditor never runs anything that sends, posts, deletes or spends.
- [2026-10-02] Personal install leaves a personal config.json behind, matching graduate-skill.
- [2026-10-05] Step 5 writes the six self-critique results (pass/fix, one line of evidence, what was fixed) to the new skill's cases/baseline/self-critique.md before dispatching the independent audit, and the auditor verifies that record against the draft (missing or contradicted = P2). A real build skipped the checks silently and lint plus audit still passed; template added to references/self-critique.md.
- [2026-10-06] Backfilled the six-check self-critique record (cases/baseline/self-critique.md). Fixes from it: Step 4 now shows a before/after for strictness (prose post → dry-run script) and for current-model wording; the stale birth placeholder in Gotchas is gone.
