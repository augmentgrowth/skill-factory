# Self-critique — learn-from-session

Backfill run on 2026-10-06 for a skill built before the self-critique record existed. The six
checks ran against SKILL.md as it stands (the skill has no references); there was no draft-stage
audit to precede. The one failing check (Focus) was fixed on 2026-10-06 after the builder approved the cut.

| Check | Verdict | Evidence (from the skill) | Fixed |
|---|---|---|---|
| Voice | pass | SKILL.md:13–16 "Error-annealing runs autonomously because behavior is observable… preference mining is judgment, so it is PROPOSE-FIRST"; :20–21 "Only the user knows whether you read them correctly" | — |
| Principles | fix | SKILL.md:70–71 declined signals: "The user already judged them; proposing one again asks them to say no twice."; :109–110 one skill per signal: "Two copies of one rule drift apart the first time either skill is edited." | Both rules were stated without a reason; added one sentence of why to each |
| Anti-Pattern | pass | SKILL.md:38 "Drop one-off phrasings, task-specific details, and restatements of existing content"; :107–108 a restating edit "is the top false-positive"; :70 never re-propose a declined signal | — |
| Example | pass | SKILL.md:79–95 worked example: two verbatim corrections become one HIGH proposal with the exact before/after line and the CHANGELOG line it would ship with | — |
| Model Calibration | pass | The three all-caps words (SKILL.md:15 PROPOSE-FIRST, :44 NOTHING, :75 ARE) all sit on the one approval rule, each with its reason (:13–16, :75–77); no request to write out reasoning; no generic "double-check" | — |
| Focus | fix | Step 4's LOW bullet now carries the offhand-phrasing rule; the replay rubric (cases/baseline/expected.md) holds the scenario checks | Deleted the "Scenario checks" section, which repeated Steps 2, 4 and 5 and the replay rubric; moved its one unique rule into Step 4 |
