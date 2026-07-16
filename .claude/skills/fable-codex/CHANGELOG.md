# fable-codex changelog

[2026-07-15] Birth: baseline captured (frozen pm-agent proposal-kind-registry task at commit 6eec1b8; Fable-only no-skill run, 545 tests green). Classified: workflow skill (internal references/scripts only, chains no sibling skills).
[2026-07-15] Skill complete: side-by-side gate won vs no-skill baseline (with-skill loop caught a DRILLS.md drill regression the baseline missed; Sol plan review forced a real plan revision). 14/14 stub scenarios, shellcheck clean, live loop end-to-end green (plan REVISE→APPROVED, code CHANGES_REQUIRED→APPROVED, fresh-thread final APPROVED, 545 tests).
[2026-07-15] Merge-gate review fixes (Sol fresh-thread review, 2 P1 + 4 P2): verdict tag must be final non-blank line; secret/auth scans fail closed on scanner errors; unquoted credential assignments scrubbed; collision-proof hashed repo slugs; denylist entries canonicalized (~, symlinks); jq checked before any send. Tests 14→19 scenarios.
