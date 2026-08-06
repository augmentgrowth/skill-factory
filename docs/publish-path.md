# Publish path — design sketch (not built)

This document sketches how a skill home (see `templates/skill-home/`) can export
its skills as an installable Claude Code plugin, without restructuring the hub
to make that possible later. **Nothing here is built.** It exists so the hub
layout is chosen with publishing in mind, not designed into a corner.

## The mechanism: a generated manifest over a symlink

A Claude Code plugin needs exactly two things at its root: a
`.claude-plugin/plugin.json` (identity) and a `skills` entry pointing at a
directory of `SKILL.md`-bearing folders. It does not need the skills to live
at the plugin root natively — a symlink is enough, because the plugin loader
follows it.

**This factory is already the live example of the pattern:**

```text
skill-factory/
├── .claude/skills/              # real content
├── skills -> .claude/skills     # plugin-compatibility symlink
├── .claude-plugin/
│   ├── plugin.json              # {"name": "skill-factory", "skills": "./skills/", ...}
│   └── marketplace.json         # the install-path listing
```

Run `claude plugin marketplace add <owner>/<repo>` against this repo and
`claude plugin install skill-factory@skill-factory`, and Claude Code resolves
`skills` through the symlink straight into `.claude/skills/` — no copy, no
build step, no separate "packaged" tree to keep in sync.

A skill-home hub can export the same way:

```text
my-skill-home/
├── .claude/skills/<name>/       # canonical content, unchanged
├── skills -> .claude/skills     # same symlink pattern
├── .claude-plugin/
│   ├── plugin.json              # generated: name, version, description, "skills": "./skills/"
│   └── marketplace.json         # generated: one plugin entry pointing at "./"
```

Because the symlink points at the *same* canonical directory the anneal loop
already writes to, publishing never forks the content: a fix landed by
`improve-skill` is live in the plugin the next time a consumer pulls, with no
separate "publish the fix" step.

**Curation, not a straight export of everything.** A hub is not obligated to
publish its whole personal tier. The generated `plugin.json`'s `skills` entry
can point at a curated subdirectory (or a second symlink,
`published-skills -> .claude/skills`, listing only skills chosen for release)
so work-in-progress or client-scoped skills in the same hub never leak into a
published plugin by accident. Exactly which skills are curated in is a
decision for whoever runs the export step — this sketch only fixes the
mechanism, not the selection policy.

## Distribution channel: a private repo as a private marketplace

Claude Code's `plugin marketplace add` accepts any git remote the installing
machine can reach — a public GitHub repo is the common case, but a **private**
repo works identically as long as the installer has clone access (an SSH key,
a PAT, or an org membership). That makes "private marketplace" not a special
feature to build, but the same mechanism pointed at a repo with restricted
access:

- A team or client gets `claude plugin marketplace add <org>/<private-repo>`
  instead of a public slug.
- The exported hub (or a curated subset of it) lives in that private repo,
  generated fresh from the canonical skill home whenever a release is cut —
  not hand-maintained as a second copy.
- Version pinning, access revocation, and audit trail all inherit from
  whatever the private repo's own hosting already provides (branch
  protection, deploy keys, org membership) — nothing skill-specific to build.

## Versioning: plugin version bumps

The generated `plugin.json`'s `version` field is the release unit. A publish
step:

1. Regenerates `plugin.json` and `marketplace.json` from the hub's current
   curated skill set.
2. Bumps `version` (semver) — this factory's own precedent: the improve-skill
   protocol change in this same PR bumped `plugin.json` from `0.2.0` to
   `0.3.0` alongside the skill content it shipped.
3. Commits the export dir (or pushes to the export repo, if it's separate from
   the hub) as one release commit/tag.

No per-skill versioning is proposed here — the whole plugin ships as one unit,
matching how Claude Code plugins are already installed and updated (`claude
plugin install`, `claude plugin update`) as a single package, not per-skill.

## What stays out of scope

This sketch deliberately does not build, and does not commit to building:

- **An automated export command.** Whether the manifest generation above
  becomes a `bin/skills publish` subcommand, a separate script, or a manual
  step is undecided — the mechanism (symlink + generated manifest) is fixed;
  the tooling around it is not.
- **A curation UI or policy.** Which skills from a hub are publishable is a
  per-hub judgment call, not something this design prescribes.
- **Per-skill versioning, changelogs-as-release-notes, or a registry service.**
  The plugin-version-bump model above is the only versioning story sketched;
  anything finer-grained is future work.
- **Secret or credential handling for published skills.** A skill needing
  credentials still ships `.env.example` only (see the factory's Credential
  Handling contract); publishing does not change that contract or add a
  secrets-injection story.
- **Automatic sync between a hub and its export repo.** If the export lives in
  a separate repo from the hub (e.g. for the private-marketplace case), moving
  content between them is a manual or scripted step run at release time, not
  a standing sync job — standing sync jobs are exactly the automation class
  this factory's own operating spec warns against (auto-commit crons
  corrupting the one-commit anneal transaction).

## Relationship to other publish mechanisms

This sketch complements, and does not replace, a hub's own `graduate-skill`
flow (copying a finished skill to a personal install target) or any
separate curated-public-release pipeline a hub maintains for sanitized
snapshots. It is specifically the plugin-manifest path: turning a hub (or a
curated slice of one) into something `claude plugin install` can consume
directly.
