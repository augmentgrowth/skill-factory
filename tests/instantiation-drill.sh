#!/bin/bash
# Instantiation drill — measure the ten-minute claim instead of repeating it.
#
# WHY THIS EXISTS. README.md says a fresh clone gets you to a working skill in
# under ten minutes, and LAB-223 has carried "10-minute instantiation target
# confirmed" as an unchecked box since July. Nobody had ever put a clock on it.
#
# WHAT THIS MEASURES, AND WHAT IT DOES NOT. This times the *agent's* path: fresh
# clone, one frozen prompt, stop when a committed skill exists. A real builder
# also reads, thinks, and types, so this number is a FLOOR for the README's
# claim, not the claim itself. Report it that way. A drill that quietly inflates
# into "the 10-minute promise is verified" is the rubber-stamp this whole
# exercise exists to avoid.
#
# The prompt is frozen in this file on purpose. A different description on every
# run measures a different thing each time, and then the number cannot be
# compared to the last one.
#
# Usage:  tests/instantiation-drill.sh [target-seconds]
#         default target: 600
#
# Exit:   0 within target, 1 over target or no skill produced, 2 environment error

set -u

TARGET="${1:-600}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

command -v claude >/dev/null 2>&1 || { echo "claude CLI not found" >&2; exit 2; }

WORK="$(mktemp -d "${TMPDIR:-/tmp}/instantiation-drill.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

REPO="$WORK/clone"
BARE="$WORK/clone.git"

# The clone is part of what the README's claim covers, so it is inside the
# clock. --no-hardlinks keeps it honest: a hardlinked clone is faster than the
# network clone a real user does, but the local copy is the floor either way.
echo "Cloning..."
start=$(date +%s)

git clone --quiet --no-hardlinks "$SRC" "$REPO" || { echo "clone failed" >&2; exit 2; }

# Its own bare remote: a dirty or unpushed tree makes the closeout guard fire,
# and that response would land inside the measured window. Same reason the
# cold-read audit does this.
git init --quiet --bare "$BARE"
git -C "$REPO" remote remove origin 2>/dev/null
git -C "$REPO" remote add origin "$BARE"
git -C "$REPO" push --quiet -u origin HEAD 2>/dev/null
git -C "$REPO" config user.email drill@example.invalid
git -C "$REPO" config user.name "Instantiation Drill"

# The starting point, captured before the session runs, so "what was built" is
# measured against what was actually here rather than a hardcoded skill list.
START_COMMIT="$(git -C "$REPO" rev-parse HEAD)"

# Frozen builder input: one workflow description, deliberately ordinary and
# describable, in the voice of someone who is not a programmer.
read -r -d '' PROMPT <<'__P__'
help me build a skill

Every Monday I go through last week's customer support tickets and write a short
summary for the team. I pull the ticket export, read through them, and group them
into themes -- billing problems, login problems, feature requests, that sort of
thing. Then I write up the top three themes with a couple of example quotes each,
and flag anything that looks like it's getting worse compared to the week before.

I want a skill that does that for me. Go ahead and make all the reasonable calls
yourself rather than asking me a lot of questions -- if you need a sample ticket
export, invent a representative one and use that as the frozen sample.
__P__

echo "Running the session (this is the measured part)..."

# --setting-sources project,local is load-bearing, and the drill's first run is
# why. A fresh CLONE is not a fresh SESSION: without this, the session still
# loads the operator's personal ~/.claude tier, and the very first run found an
# already-built skill for this exact workflow in the operator's personal skills
# and correctly declined to build a duplicate. Elapsed 58s, produced nothing —
# a measurement of the operator's machine, not of the factory.
#
# Not --safe-mode: that would also disable the project CLAUDE.md, which IS the
# factory. Dropping the user tier keeps the project spec and project skills
# while removing everything personal.
# bypassPermissions stands in for the human who clicks "yes" in a real session.
# Dropping the user setting tier also drops the operator's permission allowlist,
# so acceptEdits alone left the session unable to write into its own clone or
# run git — it built the skill correctly and then had nowhere to put it. That is
# a measurement artifact, not a factory defect.
#
# BE HONEST ABOUT WHAT THIS IS: permission checks are off process-wide, not
# sandboxed to the clone. The temp directory bounds where the drill *intends* to
# write, not where the session *can* write. And the session executes the cloned
# revision's own instructions, so this drill is only as safe as the revision
# under test.
#
# The real precondition is therefore trust in the revision, plus a frozen prompt
# and a throwaway remote that goes nowhere. Do not run it against a revision you
# would not run interactively, and do not parameterize the prompt without
# revisiting this.
( cd "$REPO" && claude -p "$PROMPT" \
    --permission-mode bypassPermissions \
    --setting-sources project,local ) \
  > "$WORK/transcript.txt" 2>&1
status=$?

end=$(date +%s)
elapsed=$((end - start))

# --------------------------------------------------------------- end state --
#
# Measure the outcome, never the clock alone. A run that finishes in ninety
# seconds because the agent gave up is a failure with a good-looking number.

# Which skills existed BEFORE the session, read from the clone's starting commit
# rather than hardcoded. A hardcoded list of the four factory skills silently
# grades the wrong folder the moment a fifth ships -- and the drill would then
# "pass" on a pre-existing skill it did not build.
: > "$WORK/preexisting"
git -C "$REPO" ls-tree -r --name-only "$START_COMMIT" -- .claude/skills \
  | awk -F/ 'NF>=4 && $4=="SKILL.md" {print $3}' | sort -u > "$WORK/preexisting"

built=""
extras=0
for dir in "$REPO"/.claude/skills/*/; do
  name="$(basename "$dir")"
  [ -f "$dir/SKILL.md" ] || continue
  grep -qxF "$name" "$WORK/preexisting" && continue
  extras=$((extras + 1))
  [ -z "$built" ] && built="$name"
done
[ "$extras" -gt 1 ] && echo "note: $extras new skill folders; grading '$built'"

echo
echo "───────────────────────────────────────────────────────"
printf 'elapsed:  %dm %02ds  (target %ds)\n' $((elapsed / 60)) $((elapsed % 60)) "$TARGET"
echo "session exit: $status"

fail=0

if [ -z "$built" ]; then
  echo "produced: NOTHING -- no new skill folder with a SKILL.md"
  fail=1
else
  echo "produced: $built"

  # ls-tree HEAD, not ls-files. ls-files reads the INDEX, so a skill that was
  # merely `git add`ed and never committed counted as committed -- the drill
  # would report a passing time for a run that never finished the one thing the
  # factory promises. Same reason cases/baseline is checked in the commit
  # rather than on disk.
  committed=$(git -C "$REPO" ls-tree -r --name-only HEAD -- ".claude/skills/$built" | wc -l | tr -d ' ')
  if [ "$committed" -gt 0 ] && git -C "$REPO" cat-file -e "HEAD:.claude/skills/$built/SKILL.md" 2>/dev/null; then
    echo "committed: yes ($committed file(s) in HEAD)"
  else
    staged=$(git -C "$REPO" ls-files ".claude/skills/$built" | wc -l | tr -d ' ')
    echo "committed: NO -- skill exists but SKILL.md is not in HEAD (staged: $staged)"
    fail=1
  fi

  if git -C "$REPO" ls-tree -r --name-only HEAD -- ".claude/skills/$built/cases/baseline" | grep -q .; then
    echo "baseline:  present in HEAD"
  else
    echo "baseline:  MISSING from HEAD -- cases/baseline/ is the factory's own contract"
    fail=1
  fi
fi

if [ "$elapsed" -gt "$TARGET" ]; then
  echo "verdict:   OVER TARGET"
  fail=1
fi

echo
echo "This is the agent's path only -- clone plus one frozen prompt. A human"
echo "also reads and types, so treat it as a floor under the README's claim,"
echo "not as confirmation of it."

if [ "$fail" -eq 0 ]; then
  echo
  echo "drill: PASS"
  exit 0
fi
echo
echo "drill: FAIL"
echo "transcript tail:"
tail -20 "$WORK/transcript.txt" | sed 's/^/    /'
exit 1
