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
migration step. One warning to pass on when relevant: a build home with an automated **commit**
cron will corrupt the factory's one-commit transaction discipline — prefer a repo without one.
This is about auto-commit, not pushing: an auto-commit races the anneal transaction mid-flight,
while pushing already-committed state is safe and is what the factory does by default.

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
- **Push when the build home is yours.** If the build home has a remote you own and can write to,
  the factory commits *and* pushes — closeout is part of the task, not a later step. If origin is a
  public template you cannot push to (a stranger's clone of this repo), commit locally only and say
  so plainly once. Pushing is authorized per release by the release gate, not by write access
  alone: `scripts/release-gate.py --release`, enforced on every push by `githooks/pre-push`.
  A gate nothing invokes is documentation. Running the script by hand is a *diagnostic*: it exits
  non-zero even when clean, so `release-gate.py && git push` can never stand in for the hook.
  The gate also scans the **content** of every outgoing commit for credential shapes, because path
  authorization and content safety are different questions: a key committed under `docs/` or inside
  a skill's own folder sits at a perfectly authorized path. That scan is scoped to what is
  outgoing; sweep all history by hand with `tests/secrets-sweep.sh` after history surgery or on a
  clone of unknown provenance.
- **Install the hook yourself, in preflight — under all three conditions.** Nothing inside a git
  repo can set its own `core.hooksPath`, so a fresh clone starts unguarded, and that install is
  YOUR job rather than a setup step left to the builder. Before any git work in a build home, run
  `git -C <repo> config core.hooksPath githooks` **only when every one of these holds**:
  1. `<repo>/githooks/pre-push` exists **and its body invokes `scripts/release-gate.py`**, which
     also exists. Setting `core.hooksPath` arms *every* hook in that directory, so keying on the
     filename alone would execute a stranger's `pre-commit` on your first commit. Git refuses to
     honor cloned hooks precisely to prevent this; do not hand that protection away. This matters
     most under a plugin install, where the build home is whatever repo the builder happens to be
     standing in.
  2. `core.hooksPath` is currently **unset or already `githooks`**. Anything else means another
     hook manager (husky, pre-commit) owns it — escalate in plain language, never clobber.
  3. The command is **repo-local**. Never `--global`: that would disable hooks in every other repo
     on the machine, silently, since this check makes no announcement.

  Same posture as the identity check — no announcement, no git vocabulary. **The residual is real
  and must not be papered over:** a clone that nobody ever drives through the factory stays
  unguarded, which is why `README.md` states the install as a plain command for anyone who pushes
  by hand. Every skill that pushes runs this preflight — `build-skill`, `improve-skill`,
  `graduate-skill`, `learn-from-session` — because the gap belongs to whichever one touches git
  first, not to the one that happens to be documented.
- **Never rewrite history.** Rollback is a path-scoped restore committed as a *new* commit. Repo
  HEAD never moves, and no published commit is ever amended, rebased, or force-pushed.
- **Per-skill tags.** `<skill>/rollback-<n>` marks the last accepted state before a gated change;
  `<skill>/review-<n>` marks the shipped candidate; `<skill>/known-good-<n>` is added only after the
  builder accepts the output. Tags are immutable and push with their commits.
- **Birth history.** Commit 1 = baseline captured. Commit 2 = skill done (plus the first known-good tag).
- **Escalate — do not proceed — when:** uncommitted files exist outside the target skill's folder, edits
  look like another session's work, or a fix is uncertain. Report in plain language and ask.

## The review gate

Most changes ship without asking. The gate exists for the few that need a human judgment the
machine cannot make — and even then it does not hold up the push.

**Gated (three categories only):**

- a new skill's **first release**,
- a rewrite of a skill's **behavior or judgment** — its SKILL.md prose, triggers, or decision logic,
- **graduation**.

**Everything else ships silently:** script fixes, anneal patches, gotchas, changelogs, docs, cases,
refactors. Do not ask about these; committing and pushing them is the job.

**The gate is post-ship, never a block.** Ship the change, then hand the builder an **output
receipt** to evaluate. The receipt is the previous accepted output and the candidate output, run
against the same frozen fixtures from the skill's `cases/`, presented side by side. It is never a
diff — the builder reviews what the skill *produces*, not how it is written. No file paths, no git
vocabulary, no severity ratings.

Bracket every gated change with tags so the receipt has a rollback target: `<skill>/rollback-<n>`
before, `<skill>/review-<n>` on the shipped candidate. On acceptance, add `<skill>/known-good-<n>`.
On rejection, path-scoped restore from the rollback tag as a new commit, then release again.

**One exception, and it is not a human gate:** graduation's CRITICAL script-efficiency stop. That
tests an operational property — scale, quota, silent truncation — which output review cannot
observe. The agent fixes it and re-runs; the builder is never asked to judge it.

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

**Undo has three shapes.** All three restore the one skill's folder and land as a new commit; repo
HEAD never moves backwards:

- **Normal** — restore the folder from that skill's latest `rollback-<n>` tag.
- **A rejected first release** — there is no earlier accepted state, so undo means a path-scoped
  deletion of the skill folder, committed and released like any other change.
- **A rejected graduation** — restore the build home *and* reinstall the personal copy. The
  installed copy is a frozen copy that never auto-updates, so a build-home-only restore leaves the
  rejected version live wherever it was graduated to.

**Tags are immutable.** Never move, reuse, or force-update one. `git push` does not carry tags by
default — publish the branch and its new tags together, or the release is not complete. A tag that
exists only locally protects nothing on another machine.

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
| Project skill discovery | `.claude/skills/` (auto-discovered, incl. nested) | **Repo-root `.agents/skills/` IS auto-discovered** (verified 2026-08-05 vs Codex CLI 0.144.0; the upward scan from cwd stops at the repo root, so a link placed in an *ancestor* of the repo, e.g. `~/code/.agents/skills/`, is not reached). `.claude/skills/` is still completely invisible to Codex regardless of location — this factory's own skills live there, so Codex still reaches them only because `AGENTS.md` instructs it to read `.claude/skills/<name>/SKILL.md` by path. Codex's other native auto-discovery tier is personal-only (`~/.codex/skills`), where symlinks resolve correctly. |
| Personal install target | `~/.claude/skills/` | `~/.codex/skills/` (or `$CODEX_HOME/skills`) — auto-discovered there |
| Ignored frontmatter | — | Everything except `name` + `description` is read-inert — so `context: fork`, `allowed-tools`, `hooks`, and `static:` are all ignored (Codex's own skill-creator docs: "the only fields that Codex reads"). The `static:` flag stays portability-free. |
| Extra manifest | none | `agents/openai.yaml` is **optional** UI metadata only (display name, icon, chips, `policy.allow_implicit_invocation`). Never required — build + anneal ran green with none present. |

**Gotcha:** adding a new skill directory mid-session may not hot-load into the `/` menu. Run with-skill
tests by explicit invocation — name the skill or point the agent at its `SKILL.md` — not by relying on
the menu. Under Codex this is not merely a hot-load caveat: project `.claude/skills/` skills (which is
where this factory's own skills live) are *never* auto-loaded as invocable `$skill` entries, so
with-skill testing there is **always** by explicit `SKILL.md` read (which is exactly how `AGENTS.md`
routes into them). This is now a `.claude/skills/`-specific limitation, not a blanket "Codex has no
project skill discovery" statement — a repo that instead places skills at `.agents/skills/` gets
real auto-discovery, verified above.
