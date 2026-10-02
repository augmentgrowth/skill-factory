# Draining the queue

Read by improve-skill when asked to drain the anneal queue. Moved verbatim from SKILL.md.

A factory session may work through everything waiting in the repo it is standing in — "drain the
anneal queue", or just noticing a backlog.

- **A queue entry** is a dated case directory (`cases/<YYYY-MM-DD>-<slug>/`) with **no `.annealed`
  file**. `cases/baseline/` is never a queue entry, and neither is anything undated.
- For each entry, oldest first: run Step 1 (static check), Step 2 (resolve + scoped preflight —
  this is a background-style run, so abort-and-requeue rather than ask), take the lock, then Steps
  5-7. Skip the capture step — the case already exists — and Step 4 is moot: you are already the
  annealing agent, so there is no dispatch decision to make.
- **One skill at a time.** Anything whose lock is held by a live holder is skipped silently and
  stays queued.
- Report at the end in plain language: how many failures were waiting, which are fixed, which still
  need the builder.
