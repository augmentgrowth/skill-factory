# Changelog

One line per change, newest last. Format: `[YYYY-MM-DD] What changed and why`.

- [2026-07-15] Initial skill created.
- [2026-07-15] Annealed from live drill findings: unclassifiable/disputed failures now still capture a case commit before escalating; pre-emptive escalation sanctioned when no fix could replay green; "no git vocabulary" promoted to a global rule; explicit undo requests execute immediately; fix scope bounded to what the case exercises.
- [2026-07-15] Anneal-time efficiency pass: fixes that touch a script get the script-efficiency-review checklist (via disposable sub-agent) before the green commit, scoped to the changed script and the case's bounds.
