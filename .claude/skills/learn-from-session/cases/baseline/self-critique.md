# Self-critique — learn-from-session

Backfill run on 2026-10-06 for a skill built before the self-critique record existed. The six
checks ran against SKILL.md as it stands (the skill has no references); there was no draft-stage
audit to precede. One check is not a pass and was left unfixed; its row says `weak` and it is
listed under "Still weak".

| Check | Verdict | Evidence (from the skill) | Fixed |
|---|---|---|---|
| Voice | pass | SKILL.md:13–16 "Error-annealing runs autonomously because behavior is observable… preference mining is judgment, so it is PROPOSE-FIRST"; :20–21 "Only the user knows whether you read them correctly" | — |
| Principles | fix | SKILL.md:70–71 declined signals: "The user already judged them; proposing one again asks them to say no twice."; :109–110 one skill per signal: "Two copies of one rule drift apart the first time either skill is edited." | Both rules were stated without a reason; added one sentence of why to each |
| Anti-Pattern | pass | SKILL.md:38 "Drop one-off phrasings, task-specific details, and restatements of existing content"; :107–108 a restating edit "is the top false-positive"; :70 never re-propose a declined signal | — |
| Example | pass | SKILL.md:79–95 worked example: two verbatim corrections become one HIGH proposal with the exact before/after line and the CHANGELOG line it would ship with | — |
| Model Calibration | pass | The three all-caps words (SKILL.md:15 PROPOSE-FIRST, :44 NOTHING, :75 ARE) all sit on the one approval rule, each with its reason (:13–16, :75–77); no request to write out reasoning; no generic "double-check" | — |
| Focus | weak | SKILL.md:97–103 "Scenario checks" restates Steps 2, 4 and 5 and the worked example; three of its four checks are also the replay rubric (cases/baseline/expected.md:3–12), and the fourth repeats Step 2 (:34–35) and the first Gotcha (:107) | — (see Still weak) |

## Still weak

- **Focus — "Scenario checks" duplicates the replay rubric.** Proposed fix: delete SKILL.md:97–103,
  first folding its one extra nuance — a single offhand phrasing is LOW at most — into Step 4's
  LOW line. Leaving it out of this backfill because removing a section is the builder's call.
