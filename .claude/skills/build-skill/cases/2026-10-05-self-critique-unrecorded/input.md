# Input

Run build-skill end to end on a describe-first workflow skill. At Step 5 the agent runs the lint
(no `fix` findings) and dispatches the independent audit (no P1/P2), but never runs the six checks
in `references/self-critique.md`. The draft has no anti-pattern list and no concrete examples.
