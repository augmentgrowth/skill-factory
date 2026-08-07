# Failing case — the lock protocol's `pid:` is ambiguous, and the obvious reading is wrong

## How the skill was invoked

As the background anneal agent in an AE1 drill, against the plugin-resolved copy at
`~/.claude/plugins/cache/skill-factory/skill-factory/0.3.0/skills/improve-skill/SKILL.md`
(byte-identical to this repo's copy). The agent was told to follow the protocol exactly.

Target of that anneal: `support-ticket-digest` in the hub repo
(`~/code/hypergrowthagents/skills`). That anneal itself succeeded — this case is about the
lock step the agent had to hand-correct on the way through.

## The exact instruction that failed

From `## The lock protocol`, step 1:

> **Acquire** `<repo>/.anneal/locks/<skill>` by atomic create (fail if it already exists).
> Content, two lines exactly (this is the format the repo's audit tooling parses — do not
> improvise): `pid: <n>` then `started: <ISO-8601 timestamp>`.

And step 2:

> **Already held by a live holder** (its pid is a running process and its recorded
> `started:` is under two hours old) → **exit quietly.**

## What happened

The agent did the atomic create the natural way — a shell one-liner using `set -o noclobber`
and `$$`. `$$` in that context is the **bash subshell's** pid, which dies the instant the
command returns. The lock file was therefore born recording a dead process.

The agent noticed and hand-corrected it, rewriting the file (while still holding the lock)
with the long-lived Claude Code session pid so a concurrent sweep's liveness check would
read it as live. It reported the correction unprompted.

Nothing in `SKILL.md` told it to do that. A less careful agent — or the same agent under
less scrutiny — leaves the dead pid in place.
