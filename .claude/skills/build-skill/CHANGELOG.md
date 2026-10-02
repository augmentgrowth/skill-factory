# Changelog

One line per change, newest last. Format: `[YYYY-MM-DD] What changed and why`.

- [2026-07-15] Initial skill created.
- [2026-07-15] Added write-time script efficiency pass to Step 5: script-backed drafts dispatch a fresh sub-agent to run graduate-skill's script-efficiency-review checklist; CRITICAL/HIGH fixed before the side-by-side test.
- [2026-07-15] Build-home model: skills are born in the invoking project's .claude/skills/ (the build home), not necessarily the factory clone; Step 2 and Step 7 updated. Unblocks plugin-path building.
- [2026-10-02] Drafts against the shared audit-skill rubric and runs its lint before self-critique; self-critique adds a model-calibration check; quality bar slimmed to factory-process items with the description rule reconciled (trigger phrases plus a boundary, no catch-all lists). Fixed frontmatter that failed YAML parsing (bare "Triggers on:"), which made Claude Code load this skill with no description.
- [2026-10-02] Audit: Step 7 saves, tags and publishes with exact commands, scoped to the skill folder, and handles a refused push (D1); copyable build checklist with loop-backs (E1); caps removed from non-dangerous lines (G2); target-models recorded (G1); Codex gotcha corrected — only `.claude/skills/` is invisible to Codex (J2).
- [2026-10-02] Evaluator round 1: lint path resolves from the skill's own folder (`${CLAUDE_SKILL_DIR}`); Step 7 asks once whether a new skill is safe to publish and sets `public_safe: true`, so a factory clone's gate no longer silently strands every new skill.
