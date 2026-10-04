# Changelog

One line per change, newest last. Format: `[YYYY-MM-DD] What changed and why`.

- [2026-07-15] Initial skill created.
- [2026-07-15] script-efficiency-review.md now documents its three run points (write time, anneal time, graduation) and the disposable sub-agent dispatch mode for the first two; graduation gate unchanged.
- [2026-07-15] Build-home model: system-of-record language generalized from "factory repo" to the skill's build home (spec: "Where skills are born").
- [2026-08-11] Autonomous-push policy: the CRITICAL efficiency stop is now agent-owned (fix it and re-run; never hand the builder a severity decision) with its rationale stated — it tests scale/quota properties output review cannot observe. Graduation is bracketed by rollback/review tags and hands over an output receipt; a rejected graduation must also reinstall the frozen personal copy.
- [2026-10-02] Step 1 quality gate now runs the audit-skill lint and rubric instead of a four-item subset; fixed its path to build-skill's quality bar, which did not resolve.
- [2026-10-02] Audit: the personal install is an exact rsync that leaves `.env` behind and the publish is one exact push of branch plus rollback/review tags (D1); copyable graduation checklist with loop-backs (E1); the efficiency reference now says to fix a CRITICAL yourself and re-run, matching Step 2 (F1); lint/rubric paths stated as relative to this skill's folder (C6); target-models recorded (G1).
- [2026-10-02] Evaluator round 1: graduation blocks on rubric P1 failures only (lint `fix` findings on P2/P3 rules are reported, the builder decides); lint path resolves from the skill's own folder.
- [2026-10-02] Saved baseline case (input + judging rubric) so later changes to this skill can be replayed and proven safe.
- [2026-10-02] Baseline case states how the skill treats API responses, so rubric D2 can be judged.
- [2026-10-02] Re-graduation keeps the installed copy's config.json as well as .env (rsync excludes both).
- [2026-10-03] Personal installation now includes absent tracked shared config, preserves installed settings at every depth, and rejects unsafe paths before copying.
