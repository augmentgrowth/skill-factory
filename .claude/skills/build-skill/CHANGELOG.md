# Changelog

One line per change, newest last. Format: `[YYYY-MM-DD] What changed and why`.

- [2026-07-15] Initial skill created.
- [2026-07-15] Added write-time script efficiency pass to Step 5: script-backed drafts dispatch a fresh sub-agent to run graduate-skill's script-efficiency-review checklist; CRITICAL/HIGH fixed before the side-by-side test.
- [2026-07-15] Build-home model: skills are born in the invoking project's .claude/skills/ (the build home), not necessarily the factory clone; Step 2 and Step 7 updated. Unblocks plugin-path building.
- [2026-10-02] Drafts against the shared audit-skill rubric and runs its lint before self-critique; self-critique adds a model-calibration check; quality bar slimmed to factory-process items with the description rule reconciled (trigger phrases plus a boundary, no catch-all lists). Fixed frontmatter that failed YAML parsing (bare "Triggers on:"), which made Claude Code load this skill with no description.
