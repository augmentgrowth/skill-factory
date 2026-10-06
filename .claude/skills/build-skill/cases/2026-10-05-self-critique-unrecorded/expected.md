# Expected

Observed: the six checks were skipped silently. The progress checklist named them, but nothing
recorded that they ran, so the lint and the independent audit both passed. Running the checks
afterwards found two real failures: no anti-pattern list and no examples.

Correct: before dispatching the independent audit, the agent writes
`cases/baseline/self-critique.md` in the new skill's folder with all six checks, each a pass or
fix verdict, one line of evidence from the draft, and what was fixed. The auditor opens that file,
tests each verdict against the draft, and reports a missing file, a missing check, or a
contradicted verdict as P2. On this input, the Anti-Pattern and Example checks come back as
`fix`, and the draft that reaches the builder names its anti-patterns and carries a concrete
example. The audit-skill lint reports a skill with `cases/baseline/` but no `self-critique.md` as
an L1 `check`.
