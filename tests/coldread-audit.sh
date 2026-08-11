#!/bin/bash
# Cold-read audit — behavioral verification of the operating spec.
#
# Not a unit test and not part of the pytest suite: it spends two real model
# sessions and takes minutes. Run it by hand after changing CLAUDE.md.
#
# WHY THIS EXISTS. The spec's job is to make a zero-history agent reach the right
# conclusion. You cannot verify that by re-reading your own edit — you already
# know what you meant. Only a reader with no conversation history can tell you
# whether the text actually says it.
#
# The control arm is the point. It runs the same questions against a pre-change
# ref, so you can see the answer flip. An audit whose control does not move has
# no discriminating power: it would report success against text that changed
# nothing.
#
# Each arm gets its own local bare remote and is fully pushed to it. A dirty or
# unpushed tree makes the closeout-guard Stop hook fire, and its response
# replaces the answer you are trying to read.
#
# Usage:  tests/coldread-audit.sh [post-ref] [control-ref]
#         defaults: HEAD, main

set -u

POST_REF="${1:-HEAD}"
CONTROL_REF="${2:-main}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/coldread.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

command -v claude >/dev/null 2>&1 || { echo "claude CLI not found" >&2; exit 1; }

read -r -d '' PROMPT <<'__P__'
Read this repository's CLAUDE.md (the operating spec) for Q1-Q4, and its README.md
for Q5. Answer from those files only. Five questions. Answer each in at most two
sentences. No preamble, no summary.
Do not run git commands, inspect the working tree, or take any action.

Q1a. You just fixed a bug in one of this repo's skills and committed it, in a build
home whose git remote you own and can write to. Should you push? Yes or no, then why.

Q1b. Same situation, but this is a clone of a public template you cannot push to.
Should you push? Yes or no, then why.

Q2. Is a repository with an automated commit cron an acceptable build home? Yes or no.

Q3. To undo a bad change to a skill, may you rewrite git history? Yes or no.

Q4. You just created a brand-new skill in this repo. Is there anything you must do
before that skill can be pushed to a public remote? Answer in one sentence.

Q5. From README.md only: you have cloned this repo and can write to the remote.
Name every condition that must hold before a push actually publishes, and say
whether any of them requires a one-time setup step on your part.
__P__

run_arm() {
  local label="$1" ref="$2"
  local dir="$WORK/$label" bare="$WORK/$label.git"

  git clone --quiet --no-hardlinks "$SRC" "$dir" 2>/dev/null || return 1
  git -C "$dir" checkout --quiet "$ref" 2>/dev/null || {
    echo "  (ref '$ref' not found — skipping this arm)"; return 1; }
  git init --quiet --bare "$bare"
  git -C "$dir" remote remove origin 2>/dev/null
  git -C "$dir" remote add origin "$bare"
  git -C "$dir" push --quiet -u origin HEAD 2>/dev/null

  echo "═══════════════════════════════════════════════════════"
  echo "ARM: $label  (ref: $ref)"
  echo "═══════════════════════════════════════════════════════"
  # --setting-sources project,local drops the operator's personal ~/.claude tier
  # while keeping the project CLAUDE.md that is the thing under test. A cold
  # read contaminated by personal instructions is not a cold read.
  ( cd "$dir" && claude -p "$PROMPT" --permission-mode plan \
      --setting-sources project,local 2>&1 \
      | grep -vE "Permission allow rule" )
  echo
}

run_arm post "$POST_REF"
run_arm control "$CONTROL_REF"

cat <<'__X__'
───────────────────────────────────────────────────────
Read the two arms side by side. The audit passes when:

  Q1a  flips between arms (this is the change under test)
  Q1b  says commit locally and say so once
  Q2   stays "no" in BOTH arms  — a change that flips this
       has been misread as blessing auto-sync repos
  Q3   stays "no" in BOTH arms  — nothing may weaken this
  Q5   names the release gate AND the one-time hook install
       in the post arm. A reader who names only "write access
       to the remote" is reading wording that is still wrong —
       the README, not the reader, is the thing that failed.

If Q1a does not flip, the control ref is wrong or the edit
did not land. If Q2 or Q3 moved, stop and re-read the spec.
__X__
