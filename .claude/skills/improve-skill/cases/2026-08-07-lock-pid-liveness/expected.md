# Observed vs expected

## Why this is a real defect and not a nitpick

The lock exists for exactly one purpose, stated in the protocol: *"One skill anneals at a
time."* Step 2's whole job is to let a second agent recognise a **live** holder and back off.

That recognition is a liveness check on the recorded pid. So:

- Write a shell subshell's `$$` → the pid is dead within milliseconds of the file existing.
- A concurrent sweep runs step 2 → "the recorded pid is dead" → step 3 says **reclaim it**.
- Two agents now anneal the same skill at once, each committing to the same skill folder.

The protection inverts: the lock reads *permanently stale* rather than *held*. The two-hour
`started:` bound cannot save it — step 3 reclaims on a dead pid **or** an old timestamp,
whichever comes first.

This is latent, not theoretical-only: the drill's agent produced exactly this file and only
avoided the consequence by noticing on its own and rewriting the pid by hand.

## Expected

`SKILL.md` must say **whose** pid to record — the long-lived agent/session process that will
still be running for the duration of Steps 5-7, never the pid of the shell command that
happens to create the file. The natural implementation (a `noclobber` one-liner using `$$`)
must not be the wrong one, either because the text names the right pid explicitly or because
it gives an acquire recipe that captures the right one.

Ideally it also says what to do when no stable pid is available — prefer the `started:`
timestamp as the liveness signal rather than treating an unverifiable pid as dead. The
protocol already hints at this for audit tooling ("may also use the lock file's age as a
fallback signal"), but gives step 2 no such fallback.

## Judgment rubric for the replay

Re-read the fixed `## The lock protocol` and judge:

- [ ] It states unambiguously which process's pid goes in the file, and that it must outlive
      the acquire command.
- [ ] An agent following it literally with a shell one-liner cannot end up recording a
      short-lived subshell pid.
- [ ] Step 2's liveness check has a defined behavior when the pid cannot be trusted or
      verified — it does not silently fall through to "dead → reclaim".
- [ ] The two-line file format is unchanged (`pid:` then `started:`) — the repo's audit
      tooling parses it and the fix must not break that contract.
- [ ] The fix stays inside `improve-skill`'s own folder; the template and other factory
      skills are not edited as a ride-along.

Pass = all five. Judgment read of the instructions, not a byte-diff.

## Note on scope

`improve-skill` is not `static:`, so annealing applies normally. But this skill is **the
factory's own improvement loop and ships in the public plugin** — a fix here changes the
protocol every harness follows and warrants a version bump and a factory PR, not a quiet
local commit. Treat the fix as needing Malachi's review before it ships, even though the
capture itself is routine.
