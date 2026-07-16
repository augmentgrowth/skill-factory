# Skill Factory — Operating Spec

This is a factory-in-a-box for building top-tier Claude skills. You are the factory agent. A
builder opens this repo and describes a task; you run the guided flow, the tests, and every git
operation. This file is the whole contract — a zero-history agent in a fresh clone operates every
protocol below from this file alone.

> `AGENTS.md` in this repo is a symlink to this file. If you arrived via either name, you are reading
> the same spec. Harness differences are additive notes in one section, never divergent content.

## Purpose + routing rule

Any workflow-shaped or skill-building utterance routes into the `build-skill` skill — do not free-hand
it. Triggers include "I want a skill for…", "here's my weekly task…", "help me build a skill",
"turn this into a skill", or a builder describing a recurring task they want to automate. Read
`.claude/skills/build-skill/SKILL.md` and follow it. Improvement, learning, and graduation route to
`improve-skill`, `learn-from-session`, and `graduate-skill` respectively.

## Where skills are born: the build home

Every skill is born in a **build home**: the `.claude/skills/<name>/` tree of a git repo the
builder owns. Which repo that is depends on how the factory arrived:

- **Cloned factory** — the clone itself is the build home. Skills are born next to the factory
  skills, exactly as before.
- **Plugin install** — the factory skills load everywhere, and the build home is the project the
  builder is standing in. Its `.claude/skills/<name>/` gets the new skill, git-tracked in the
  builder's own repo. **Never create files inside the plugin's managed cache** — it is read-only
  and not the builder's repo.
- **No git repo at the current directory** — ask the builder where their skills should live (an
  existing repo, or offer to set one up), or fall back to degraded no-git mode per `build-skill`.

Whichever repo a skill is born in is its **permanent system of record**: `improve-skill` anneals
there in place, and `graduate-skill` copies outward while history stays put. There is no
migration step. One warning to pass on when relevant: a build home with automated commit crons
(auto-sync repos) will corrupt the factory's one-commit transaction discipline — prefer a repo
without one.

## The three-type taxonomy

Classify every skill before drafting (deep guidance: `templates/taxonomy.md`):

- **Capability** — teaches Claude to do something new: tools, scripts, integrations.
- **Knowledge** — encodes company or domain judgment and context Claude does not have.
- **Workflow** — orchestrates a multi-step process, chaining atomic skills rather than inlining them.

## The quality bar

Enforce these while drafting. Anchors: Anthropic, "Lessons from building Claude Code: How we use
skills" (claude.com/blog, 2026-06-03) and the Anthropic skills PDF, "The Complete Guide to Building
Skills for Claude" (January 2026). Refresh prescriptions against both when they update.

- **Descriptions are trigger mechanisms, not summaries.** Pack the description with literal activation
  keywords a builder would actually say. Missing trigger conditions is the top reason skills fail to load.
- **Never restate what Claude already knows.** Spend tokens only on domain knowledge that moves Claude
  off its defaults. "Claude already knows how to code" — do not re-teach it.
- **SKILL.md under 500 lines.** Split into reference files as you approach the limit.
- **References one level deep** from SKILL.md. Nested references get partial-read only.
- **Degrees-of-freedom matching.** Prose steps where many paths are valid; exact, do-not-modify scripts
  where the operation is fragile or irreversible. Match specificity to fragility.
- **A `## Gotchas` section scaffolded at birth.** Grow it from real failures. It is the highest-signal
  content in a skill; every skill starts with the heading present, even if empty.

## The silent-git contract

You run ALL git. The builder never learns git and never sees git vocabulary. Every skill is a
git-tracked history from birth.

- **Path-scoped staging, always.** Stage the target skill's folder by explicit path. Never a repo-wide
  `add`. Every operation is scoped to the one skill folder you are working on.
- **Never push. Never rewrite history.** You commit locally only. In a cloned factory, origin is the
  public template repo, which builders cannot push to; in any other build home, pushing is that
  repo's own workflow and never something the factory does automatically. Remoting or publishing a
  builder's skills is a deliberate later step, never automatic.
- **Per-skill known-good tags.** Tag `<skill>/known-good-<n>` at creation-done and again at graduation,
  so a rollback target always exists.
- **Birth history.** Commit 1 = baseline captured. Commit 2 = skill done (plus the first known-good tag).
- **Escalate — do not proceed — when:** uncommitted files exist outside the target skill's folder, edits
  look like another session's work, or a fix is uncertain. Report in plain language and ask.

## The anneal protocol (summary)

Full runbook: `improve-skill`. Error-driven annealing is default-on; a skill fails during real use and
you make it self-heal. Static skills (see below) are exempt — they get a fix proposal, never self-edit.

1. **Preflight.** List all uncommitted paths; stop and escalate if any lie outside the target skill
   folder. Classify the failure: environmental failures (timeouts, rate limits, disk full) are logged and
   skipped — they are not skill bugs, do not anneal them.
2. **Commit the failing case FIRST.** Serialize the failure to `cases/` (format below) and commit it in
   its own commit. This commit is never reverted — the fixture survives any rollback.
3. **Fix → replay, up to 3 attempts.** Fix the immediate problem, then replay the skill against the
   case's `input.md` and judge against `expected.md`. Repeat until green or attempts exhaust.
4. **On green: ONE commit.** A single commit covering the fix + the SKILL.md/Gotchas patch + one
   changelog line. One anneal equals one commit.
5. **On exhaustion or uncertainty:** path-scoped restore of the skill folder to its last known-good state
   (the folder only — repo HEAD never moves; the case commit stays intact), then escalate in plain
   language.

**Beginner vocabulary** (translate git, never expose it):

- "what changed?" → read git log for that skill's folder and answer in plain English.
- "undo that" / "go back to yesterday's version" → path-scoped restore of that skill's folder,
  committed as a NEW commit (never a history rewrite).

## The case/fixture convention

One committed `cases/` directory per skill serves baseline, regression, and anneal. Comparison is always
judgment- or rubric-based, never a byte-diff.

- **Baseline, written BEFORE drafting:** `cases/baseline/input.md` (a frozen sample input plus its
  invocation context) and `cases/baseline/output-baseline.md` (Claude's captured no-skill output). The
  side-by-side at test time is then literal: with-skill output vs this file.
- **Live failures:** serialize to `cases/<date>-<slug>/` as `input.md` plus `expected.md` (observed-vs-
  expected notes, or a judgment rubric). Commit this before any fix attempt.
- **Replay** = invoke the skill explicitly against the case's `input.md`, judged per `expected.md`.
- **Live-data workflows:** freeze a pasted representative sample as the fixed input. Monday's data is not
  Tuesday's — a captured sample is the stable fixture.

## Credential handling

Lazy — set up keys only when a skill actually needs them.

- A skill needing credentials ships a committed `.env.example` documenting every required variable.
- The real `.env` lives in that skill's own folder, is gitignored, and is recreated from `.env.example`
  when the skill moves or graduates.
- Never commit, log, or echo secret values. Error messages on a missing or unparseable `.env` stay
  plain-language and NEVER echo key names or values.

## The static flag

Mark a non-self-modifying skill with `static: true` in its SKILL.md frontmatter. Absent = annealing on
(the default).

- The anneal protocol checks this flag FIRST. A static skill gets a fix *proposal* to the builder, never
  self-modification.
- Graduation omits the improvement-protocol block for static skills.
- Unknown frontmatter keys are ignored by SKILL.md-compatible harnesses, so the flag is portability-free.

## Git-less degraded mode

Preflight (the entry skill's first action) checks that git is present and identity is configured. If git
is missing, offer a guided install (on macOS, the developer-tools prompt). If git cannot be made
available in time, continue in degraded mode: build and test the skill normally, skip commits with a
plain one-line notice, and document the later git retrofit (`git init` + an initial commit of the
existing skills). Degraded mode is a contingency, not the supported path.

## Harness notes

Supported harnesses: Claude Code (primary) and Codex (verified 2026-07-15 against Codex CLI 0.144.0 via
`codex exec`; build + anneal ran green end-to-end). Authoring stays on the portable core (`name`,
`description`, plain markdown) so other SKILL.md-compatible harnesses stay compatible without being
guaranteed. Differences are additive, not conflicting.

| Concern | Claude Code | Codex (verified) |
|---|---|---|
| Repo spec file | `CLAUDE.md`, auto-loaded | `AGENTS.md` symlink → `CLAUDE.md`; Codex auto-loads repo-root `AGENTS.md` and the symlink resolves (it quoted the spec and routed with no prompt to read it) |
| Project skill discovery | `.claude/skills/` (auto-discovered, incl. nested) | **No project skill auto-discovery** (not `.claude/skills/`, not `.agents/skills/`). Codex reaches a skill only because `AGENTS.md` instructs it to read `.claude/skills/<name>/SKILL.md` by path. Codex's native auto-discovery is personal-only (`~/.codex/skills`). |
| Personal install target | `~/.claude/skills/` | `~/.codex/skills/` (or `$CODEX_HOME/skills`) — auto-discovered there |
| Ignored frontmatter | — | Everything except `name` + `description` is read-inert — so `context: fork`, `allowed-tools`, `hooks`, and `static:` are all ignored (Codex's own skill-creator docs: "the only fields that Codex reads"). The `static:` flag stays portability-free. |
| Extra manifest | none | `agents/openai.yaml` is **optional** UI metadata only (display name, icon, chips, `policy.allow_implicit_invocation`). Never required — build + anneal ran green with none present. |

**Gotcha:** adding a new skill directory mid-session may not hot-load into the `/` menu. Run with-skill
tests by explicit invocation — name the skill or point the agent at its `SKILL.md` — not by relying on
the menu. Under Codex this is not merely a hot-load caveat: project `.claude/skills/` skills are *never*
auto-loaded as invocable `$skill` entries, so with-skill testing there is **always** by explicit
`SKILL.md` read (which is exactly how `AGENTS.md` routes into them).
