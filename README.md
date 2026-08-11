# Skill Factory

> **Start here:**
> 1. Clone this repo and open the folder in Claude Code.
> 2. Say: **"help me build a skill"**
> 3. The factory takes it from there — you'll leave with a working, tested skill.

A factory-in-a-box for building top-tier [Claude skills](https://docs.claude.com/en/docs/claude-code/skills). It guides you — beginner or power user — through turning a real workflow into a skill that provably beats what Claude does without it, then keeps that skill improving over time. All version control happens silently; you never need to learn git.

## What you get

- **Guided build** (`build-skill`) — three intake paths: describe your workflow, do the work live and extract the skill from the session, or research what great looks like first. Every build captures a no-skill baseline before drafting, so "done" means *visibly better than the baseline*, side by side.
- **Self-annealing** (`improve-skill`) — when a skill fails in real use, the agent fixes it, re-tests against the captured failing case, documents the gotcha, and commits. One failure, one commit, permanently learned.
- **Preference mining** (`learn-from-session`) — corrections you make during a session become proposed skill edits, ranked by confidence. Nothing is applied without your approval.
- **Graduation** (`graduate-skill`) — install a finished skill for use everywhere, with an efficiency review for script-backed skills and an optional formal eval gate.

## Requirements

- [Claude Code](https://claude.com/claude-code) (desktop app or CLI). Codex is also supported — it reads the same spec via `AGENTS.md`.
- git (macOS: the factory offers a guided install if it's missing).
- No API keys or credentials are needed to use the factory. Skills you build that need keys get a committed `.env.example` and guided setup at build time; real `.env` files are gitignored and never committed.

## Instantiation

Two paths, and both can build. **Clone** for a self-contained factory: skills are born inside the clone, next to the machinery. **Install as a plugin** to carry the factory into your own projects: the factory skills load everywhere, and skills you build are born in the `.claude/skills/` of whatever git repo you're standing in — your repo, your history. Either way, the repo a skill is born in (its *build home*) stays its permanent system of record; the factory never builds into the plugin's read-only cache.

### Clone (the working factory)

```bash
git clone https://github.com/augmentgrowth/skill-factory.git
cd skill-factory
# open the folder in Claude Code and say: help me build a skill
```

That's the whole setup — under 10 minutes on a fresh machine, most of it the clone. Your clone commits your skills to your own local git history.

Publishing is narrower than committing, and deliberately so. Your clone pushes only when the remote is yours and you can write to it — if you cloned this template and cannot push to it, everything stays local and the factory tells you so once. Write access alone isn't enough either: every push runs a release gate (`scripts/release-gate.py`) that fails closed, so a push carrying an unauthorized path, a version mismatch, or an unclassified new skill is blocked rather than published.

The gate runs from a git hook, and **git will not let a repository install its own hooks.** The factory installs it for you the first time you build or fix a skill in the clone, which covers the normal path. If you push by hand from a clone you've never run the factory in, run this once so the gate is actually in the loop:

```bash
git config core.hooksPath githooks
```

### Install as a plugin (the skills, everywhere)

```bash
claude plugin marketplace add augmentgrowth/skill-factory
claude plugin install skill-factory@skill-factory
```

The four factory skills then load in every session, namespaced as `skill-factory:build-skill`, `skill-factory:improve-skill`, and so on. The marketplace is named `skill-factory`, not `augmentgrowth` — hence `skill-factory@skill-factory`.

Skills you build via the plugin are committed to whatever git repo you're in — so stand in the repo you want to own the skill before you say "build me a skill." Don't run both paths against the same folder: a clone that's open as a project already auto-loads these skills from `.claude/skills/`, and installing the plugin on top registers a second, namespaced copy of each.

**If the factory skills don't auto-load** (unusual setups): tell the agent directly — *"read `.claude/skills/build-skill/SKILL.md` and follow it."* This manual path is a degraded fallback, not the normal route; if you need it regularly, check that you opened the repo folder itself (not a parent directory) in Claude Code.

**Note on symlinks:** `AGENTS.md` and `skills/` are symlinks (to `CLAUDE.md` and `.claude/skills/` respectively). They work on macOS and Linux clones. Windows clones without symlink support, and GitHub's web viewer or ZIP downloads, will show them as one-line path stubs — the content lives at the link target.

## Layout

```text
skill-factory/
├── .claude/skills/        # factory skills + every skill you build (auto-loading, git-tracked)
├── skills -> .claude/skills   # plugin-compatibility symlink (the loader follows it)
├── .claude-plugin/plugin.json      # plugin identity
├── .claude-plugin/marketplace.json # marketplace listing (the install path)
├── templates/             # skill template, changelog template, taxonomy guidance
├── CLAUDE.md              # the factory spec (canonical)
├── AGENTS.md -> CLAUDE.md # same spec for Codex and other harnesses
└── README.md
```

## Skill home template

Building skills is one half of the picture; where they *live* across every harness you use (Claude Code, Codex, Hermes, ...) is the other. `templates/skill-home/` ships the generic version of that pattern: a personal tier (`.claude/skills/`), a never-self-annealed external tier (`vendor/skills/`) for vendored skills, a `bin/skills` CLI (stdlib-only Python — `status`/`link`/`unlink`/`doctor`) for placing per-skill symlinks at global, folder, or repo scope instead of copying content everywhere, and the anneal-queue conventions the factory's own `improve-skill` relies on. See `templates/skill-home/README.md` for the full layout, init steps, and harness-by-harness discovery notes. `docs/publish-path.md` sketches (design only, nothing built) how such a hub can later export as a Claude Code plugin.

## Appendix: agent-driven bootstrap (fallback when you can't clone)

If you can't reach this repo from the target machine, an agent can rebuild the factory from the spec alone.

**Prerequisites:** Claude Code (or Codex) with file-write access; git installed; an empty target directory; a copy of this repo's `CLAUDE.md` and the contents of `templates/` and `.claude/skills/` (e.g., from a ZIP download or another machine).

**Procedure:** give the agent the files and say: *"Recreate the skill-factory repo layout in this directory per the spec's Layout section, then run `git init` and make the initial commit."*

**Verification checklist — the bootstrap succeeded when:**

- [ ] The tree matches the Layout section above (including both symlinks).
- [ ] `python3 -c "import json; json.load(open('.claude-plugin/plugin.json'))"` exits clean.
- [ ] `git status` is clean after the initial commit.
- [ ] A file named `.env` placed inside any skill folder is ignored by git; `.env.example` is tracked. (`tests/credential-drill.sh` checks this and more, without you hand-verifying it.)
- [ ] A fresh Claude Code session in the folder responds to "help me build a skill" by starting the guided flow.
