# Static-skill proposals: where they go

Read by improve-skill Step 1 when a vendored/external skill fails. Moved verbatim from SKILL.md.
The proposal file is the only record that the failure was ever found, so its address, its save,
and the cases where it must not be saved are all spelled out here.

- **Where:** `<repo>/docs/proposals/<YYYY-MM-DD>-<skill>-<slug>.md`. Create `docs/proposals/` if
  absent. `<repo>` is the repo that owns the skill — resolve it now the way Step 2 does
  (`realpath` the serving path, then `rev-parse --show-toplevel`); it is never the repo you happen
  to be standing in. Use this path even when the repo has some other proposals directory for a
  different genre — one predictable location beats a well-reasoned guess, because the next agent
  will guess differently. The date prefix matters: a recurrence with the same slug must not
  silently overwrite the earlier proposal.
- **Durability:** save it permanently, path-scoped and alone —
  `git -C <repo> add docs/proposals/<YYYY-MM-DD>-<skill>-<slug>.md` then
  `git -C <repo> commit -m "Proposal for <skill>: <slug> (static — not self-edited)" -- docs/proposals/<YYYY-MM-DD>-<skill>-<slug>.md`.
  A proposal left loose in a busy repo is one cleanup away from gone, and nothing in the queue
  will notice it is missing.
- **When the repo publishes, redirect the save — do not skip it.** A proposal quotes real paths
  and machine detail, so it must never land in a repo that publishes (a public remote, or an
  auto-sync cron). Write it to the private hub's (a personal skill-home repo; see
  the factory's `templates/skill-home/README.md` — under a plugin install, at
  `${CLAUDE_PLUGIN_ROOT}/templates/skill-home/README.md`) proposal queue instead, at the same
  `docs/proposals/<YYYY-MM-DD>-<skill>-<slug>.md` path, and tell the builder in plain language
  where it went. Leaving it unsaved was the old remedy and it was wrong: the proposal is the only
  failure record a static skill ever gets, and a loose file is one cleanup away from gone.
- **Do not save it at all when** the repo is not yours to write to (a background run that hit
  stray paths, or another session's branch) and no private hub is reachable. Leave the file where
  it is, tell the builder its location, and say plainly that it is not saved permanently yet.
  This is the one save in the protocol that happens before any preflight has run.
