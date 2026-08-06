# Skill home template

A **skill home** is the one canonical git repo where every skill you own lives,
git-tracked from birth, served out to every harness you use (Claude Code, Codex,
Hermes, or others) by scoped symlinks instead of copies. One repo, one history,
one place the anneal loop ever writes to.

This template is the generic core of that pattern — the same layout and tooling
a personal skill hub uses, with every personal path, name, and skill stripped
out. Copy it into your own repo and it works standalone.

## Why a dedicated repo

- **One system of record.** A skill's content and history live in exactly one
  place. Every harness that serves it does so through a symlink back to that
  one place — never a copy that can drift.
- **Context is expensive.** Every skill description a harness loads costs
  tokens in every session, whether that session needs it or not. Scoped
  symlinks mean a skill's description loads only where it's relevant — global,
  a folder of related projects, or a single repo — not everywhere at once.
- **The anneal loop needs a stable home.** When a skill fails in real use, the
  fix has to land in the one canonical copy, not whichever symlinked copy the
  failing session happened to be running. Because every serving path resolves
  back to this repo via `realpath`, capture-and-anneal works from any session
  on any harness without a sync step.

## Layout

```text
skill-home/
├── .claude/skills/<name>/     personal tier — canonical, git-tracked, auto-annealed
├── vendor/skills/<name>/      external tier — vendored copies, static: true, never self-annealed
├── scopes/hermes/<name>       hub-side link farm Hermes reads via skills.external_dirs
├── docs/topology/scopes.txt   registry of every scope directory bin/skills has linked into
├── .anneal/
│   ├── README.md              anneal queue + lock contract (see anneal-README.md in this template)
│   └── locks/<skill>          per-skill anneal locks — gitignored, machine-local runtime state
├── bin/skills                 the master-map / link-surgery CLI (stdlib-only Python)
├── tests/test_skills_cli.py   its test suite
└── .gitignore                 from gitignore.template in this folder
```

- **Personal tier** (`.claude/skills/`) is where skills you write and maintain
  live. These are the skills the anneal loop is allowed to self-edit.
- **External tier** (`vendor/skills/`) is for skills you've vendored from
  somewhere else — a community skill, a client-supplied one, an installed
  plugin's skill you want tracked here too. Every vendored skill carries
  `static: true` in its `SKILL.md` frontmatter, which the anneal protocol
  reads as "propose a fix, never self-edit." `bin/skills vendor --refresh
  <name>` re-copies it from wherever its `upstream:` frontmatter field points.
- **Scopes** are where a skill actually gets served from — see below.

## Init

Two ways to start, both end at the same layout:

**A. Fresh, empty git repo.**

```bash
mkdir my-skill-home && cd my-skill-home
git init
```

Then copy this template's contents in: `bin/`, `tests/`, `gitignore.template`
(rename it to `.gitignore`), and `anneal-README.md` (place it at
`.anneal/README.md`, after creating that directory). Create
`.claude/skills/` and `vendor/skills/` as you add your first skills — `bin/skills`
creates everything else (`scopes/`, `docs/topology/`, `.anneal/locks/`) on demand.

**B. An existing repo you already use.**

Copy the same files into it at the same relative paths. `bin/skills` only ever
touches paths under its own tree plus the harness roots you point it at — it
won't disturb unrelated content already in the repo.

Either way, commit the template files as your first commit, then commit each
skill you add as its own commit — path-scoped to that skill's folder, never a
repo-wide `git add`.

## The link / status / doctor workflow

`bin/skills` is a single stdlib-only Python 3 script — no install step, no
dependencies. Run it from the repo root (or pass `--root`):

```bash
bin/skills status              # the master map: every skill, its tier, every place it's linked
bin/skills status --json       # same, machine-readable

bin/skills link <name> --scope global          # ~/.claude/skills + ~/.codex/skills
bin/skills link <name> --scope hermes          # this repo's scopes/hermes/ farm
bin/skills link <name> --scope /path/to/repo   # that repo's .claude/skills + .agents/skills

bin/skills unlink <name> --scope <same-scope>  # remove that one link
bin/skills disable <name>                      # remove every link everywhere; content stays
bin/skills enable <name> [--scope <s>]         # re-link, or print how if no scope given

bin/skills doctor               # broken-link + vendored-drift audit; exits non-zero on real problems
bin/skills vendor --refresh <name>   # re-copy an external-tier skill from its recorded upstream
```

`doctor` treats broken links and vendored drift as failures (non-zero exit);
an undrained anneal queue or a stale lock is a warning only — work waiting,
not a broken hub.

Every real filesystem location `bin/skills` touches is overridable by
environment variable, which is what makes the test suite (and this template's
smoke test) safe to run without touching your actual `~/.claude` or
`~/.codex`:

```text
SKILLS_HUB_ROOT, SKILLS_CLAUDE_ROOT, SKILLS_CODEX_ROOT,
SKILLS_HERMES_ROOT, SKILLS_HERMES_CONFIG, SKILLS_VAULT_ROOT
```

Run the test suite from the repo root: `python3 -m pytest tests/` (or
`python3 -m unittest discover tests` if you don't have pytest installed — the
suite is stdlib `unittest`, pytest just gives nicer output).

## Harness notes

Scopes map onto each harness's own native discovery — there's no proprietary
sync mechanism, just symlinks (or, for Hermes, a config pointer) placed where
each harness already looks.

| Harness | Global scope | Folder / repo scope |
|---|---|---|
| **Claude Code** | `~/.claude/skills/<name>` — loads in every session | `<dir>/.claude/skills/<name>` — Claude Code discovers `.claude/skills/` in cwd-ancestor directories, so a link at `~/code/.claude/skills/<name>` reaches every repo under `~/code`, and a link at `<repo>/.claude/skills/<name>` reaches just that repo |
| **Codex** | `~/.codex/skills/<name>` (or `$CODEX_HOME/skills`) — personal-tier auto-discovery, symlinks resolve correctly | `<repo>/.agents/skills/<name>` — **repo-root auto-discovery is live**, verified 2026-08-05 against Codex CLI 0.144.0: the upward scan from cwd stops at the repo root, so a link at a repo's own `.agents/skills/` is picked up, but a link in an *ancestor* of the repo (e.g. `~/code/.agents/skills/`) is not reached. `.claude/skills/` is invisible to Codex regardless of where it sits. |
| **Hermes** | n/a (Hermes has no unscoped "everywhere" tier) | `skills.external_dirs` in `~/.hermes/config.yaml` points at this repo's `scopes/hermes/` farm — a hub-side directory of per-skill symlinks populated by `bin/skills link <name> --scope hermes`. Hermes scans that farm recursively; a local Hermes skill with a colliding name still resolves local-first. |

Because Codex's repo-root scan doesn't reach ancestor directories, "folder
scope" (many repos under one parent directory sharing a skill) only works
natively for Claude Code. To give a set of Codex repos the same skill, link it
into each repo's own `.agents/skills/` individually, or keep it at Codex's
global personal tier if it should apply everywhere.

## What this template deliberately leaves out

- No skills. You bring your own; `.claude/skills/` and `vendor/skills/`
  start empty.
- No populated `docs/topology/scopes.txt`, `scopes/hermes/`, or
  `.anneal/locks/` — `bin/skills` creates these the first time it needs them.
- No personal machine paths anywhere in this template or in `bin/skills`
  itself — every real location is either a same-shape default under `$HOME`
  (e.g. `~/.claude/skills`) or an explicit environment-variable override.
