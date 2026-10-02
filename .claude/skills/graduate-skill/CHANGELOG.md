# Changelog

One line per change, newest last. Format: `[YYYY-MM-DD] What changed and why`.

- [2026-07-15] Initial skill created.
- [2026-07-15] script-efficiency-review.md now documents its three run points (write time, anneal time, graduation) and the disposable sub-agent dispatch mode for the first two; graduation gate unchanged.
- [2026-07-15] Build-home model: system-of-record language generalized from "factory repo" to the skill's build home (spec: "Where skills are born").
- [2026-08-11] Autonomous-push policy: the CRITICAL efficiency stop is now agent-owned (fix it and re-run; never hand the builder a severity decision) with its rationale stated — it tests scale/quota properties output review cannot observe. Graduation is bracketed by rollback/review tags and hands over an output receipt; a rejected graduation must also reinstall the frozen personal copy.
- [2026-10-02] Step 1 quality gate now runs the audit-skill lint and rubric instead of a four-item subset; fixed its path to build-skill's quality bar, which did not resolve.
