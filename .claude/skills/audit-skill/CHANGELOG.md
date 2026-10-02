# Changelog

One line per change, newest last. Format: `[YYYY-MM-DD] What changed and why`.

- [2026-10-02] Initial skill created: propose-first audit of any skills folder against the factory rubric (refreshed against Anthropic's best-practices page, Claude Code skills docs, the Agent Skills spec, current-model prompting pages, and OpenAI's Codex skill-creator), with a stdlib lint for the mechanical rules and the builder's seven core rules always shown.
- [2026-10-02] Audit: saves commit only the skill folder (`commit -- <folder>`) so work staged elsewhere is never swept in; the review tag is created before the one push that publishes branch and both tags; tag fetch has an exact command (D1). Runtime stated as Python 3.9+, matching the script (H1).
- [2026-10-02] Audit: changelog line now written before the save so it rides in the same commit (the rule's own commit missed its line).
- [2026-10-02] Evaluator round 1: rollback/review tags in every git repo, not only factory clones, so "undo that" never rolls past earlier accepted work under a plugin install; hook preflight moved before the first git write and checks the gate script exists; lint reports SKILL.md folders it did not scan; rubric A4 corrected (OpenAI's validator also rejects `compatibility`); gotchas on ranking by the rubric and keeping empty Gotchas headings.
