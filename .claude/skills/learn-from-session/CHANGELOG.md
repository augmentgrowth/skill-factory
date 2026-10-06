# Changelog

One line per change, newest last. Format: `[YYYY-MM-DD] What changed and why`.

- [2026-07-15] Initial skill created.
- [2026-08-11] Autonomous-push policy: approved edits now commit AND push with no second ask. Propose-first still governs what gets learned — only the user knows whether a mined preference read them correctly — but that one approval now carries the edit all the way out.
- [2026-10-02] Audit: applying an approved edit now checks the folder for someone else's unsaved work, brackets the change with rollback/review tags, commits only the skill folder, and publishes branch and tags in one exact push (D1); description is third person with a "Not for" boundary naming improve-skill and audit-skill, catch-all dropped (A3); target-models recorded (G1).
- [2026-10-02] Audit: one changelog step, inside the save, instead of a duplicate after publishing.
- [2026-10-02] Saved baseline case (input + judging rubric) so later changes to this skill can be replayed and proven safe.
- [2026-10-02] Baseline case signals reworded so a replay can't pass by copying the worked example.
- [2026-10-06] Backfilled the six-check self-critique record (cases/baseline/self-critique.md). Fix from it: the declined-signal rule and the one-skill attribution gotcha now say why. Still weak: the Scenario checks section repeats the replay rubric.
