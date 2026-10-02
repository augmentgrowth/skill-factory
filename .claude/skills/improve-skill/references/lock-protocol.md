# The lock protocol

Read by improve-skill before Step 5 acquires the lock. Moved verbatim from SKILL.md so the
anneal steps stay within the part of the skill that survives a long session.

One skill anneals at a time. The lock belongs to whoever is annealing — **the capturing session
never takes it.**

1. **Acquire** `<repo>/.anneal/locks/<skill>` by atomic create (fail if it already exists). Content,
   two lines exactly (this is the format the repo's audit tooling parses — do not improvise):
   `pid: <n>` then `started: <ISO-8601 timestamp>`.

   **`<n>` is the pid of the long-lived process doing the anneal** — your agent/session process,
   the one that will still be alive through Step 6. It is **not** the pid of the shell that writes
   the file. Writing that shell's own `$$` from a one-liner is the natural move and it is **wrong**:
   each tool-call shell exits when its command returns, so its `$$` is dead almost immediately, the
   lock is born recording a dead process, and every later liveness check reads it as stale. Read
   your session's pid from the runtime rather than from the shell doing the write. If you cannot
   determine a pid that outlives the acquire command, write `pid: unknown` — never a pid you already
   know will be dead.
2. **Already held by a live holder** → **exit quietly.** Do not wait, do not double-anneal. The case
   stays queued and the holder or a later sweep handles it. "Live" means the recorded `started:` is
   under two hours old **and** the pid does not positively disprove it:
   - pid names a running process → the pid does not disprove liveness; the timestamp still governs.
   - `pid: unknown`, or a pid you cannot check on this platform → same: **treat as live** and back
     off while the timestamp is young. An unverifiable pid is not evidence of death.
   - pid names no running process → dead; go to 3.
3. **Stale** — the recorded `started:` is more than two hours old, **or** the recorded pid is
   confirmed dead → reclaim it: overwrite with your own pid and timestamp, and continue. (Audit
   tooling may also use the lock file's age as a fallback signal when the `started:` line is missing
   or unparseable.)
4. **Release** — delete the lock file — at *every* exit: green, exhausted, aborted preflight, or
   error. A lock outliving its run is the one failure mode that stalls a whole skill.
5. Locks are runtime state, never committed. The home repo ignores `.anneal/locks/`; if it does not
   yet, say so and let the builder's repo add it rather than committing lock files.
