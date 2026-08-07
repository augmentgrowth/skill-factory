# Anneal coordination

Place this file at `.anneal/README.md` in your skill home once you create the
`.anneal/locks/` directory (the gitignore template above already excludes it).

Anneal-from-anywhere works because every serving path (a Claude Code or Codex
symlink, a `scopes/hermes/` farm entry) resolves back into this hub. A session on
any harness runs `realpath` on the `SKILL.md` it was served, lands here, and does
its `git -C <hub>` work regardless of where the session's cwd is.

## Queue

A queued failure is a directory `cases/<YYYY-MM-DD>-<slug>/` inside a
personal-tier skill that has **no `.annealed` marker file**.

- `cases/baseline/` and `cases/experiments/` are never queue items.
- The capturing session serializes the failing case, commits it, and stops or
  spawns the background anneal agent. It never takes the lock.
- The anneal transaction writes `.annealed` on completion — green *or*
  escalated-terminal. That marker is what drains the queue.
- `bin/skills doctor` reports undrained cases as **warnings** (exit 0). An
  undrained queue is work waiting, not a broken hub.

## Locks

`.anneal/locks/<skill>` is held by the anneal agent for the duration of one
anneal, so two sessions never rewrite the same skill at once.

- The lock file records the holder: `pid: <n>` and `started: <iso8601>`. `<n>` is
  the anneal agent's own durable process — **not** the shell that wrote the file,
  whose pid dies as soon as its command returns and would make the lock look
  stale from birth. When no durable pid is available, `pid: unknown` is correct.
- TTL is 2 hours. `bin/skills doctor` warns about any lock past TTL or whose
  holder PID is confirmed dead, so it can be reclaimed. An unknown or
  unverifiable pid is not treated as dead — the timestamp governs.
- `.anneal/locks/` is gitignored — locks are machine-local runtime state, never
  repo content.
