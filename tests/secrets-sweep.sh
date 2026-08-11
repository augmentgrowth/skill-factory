#!/bin/bash
# Secrets sweep — every blob in the whole history, not just the working tree.
#
# WHY THIS EXISTS. The release gate's `range` check walks every *outgoing*
# commit, so from the moment it was installed a committed-then-deleted secret
# cannot ship. It says nothing about what was already in history before it
# existed. This sweep is the other half: it reads every blob reachable from
# every ref, so a secret that lived for one commit two months ago is still
# found.
#
# Deliberately noisy. A sweep that under-reports is worse than one that makes
# you look at something benign, so the patterns are broad and the only way to
# quiet a finding is to allowlist its *path* -- never to weaken a pattern.
#
# Usage:  tests/secrets-sweep.sh [repo-path]
#         defaults to the repo this script lives in
#
# Exit:   0 clean, 1 findings, 2 usage/environment error

set -u

REPO="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$REPO" 2>/dev/null || { echo "not a directory: $REPO" >&2; exit 2; }
git rev-parse --git-dir >/dev/null 2>&1 || { echo "not a git repo: $REPO" >&2; exit 2; }

WORK="$(mktemp -d "${TMPDIR:-/tmp}/secrets-sweep.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

# ---------------------------------------------------------------- patterns --
#
# Filenames that should never be committed at any depth. `.env.example` is the
# documented convention and is excluded below, by name, at the match site.
FILENAME_RE='(^|/)\.env($|\.)|\.(pem|p12|pfx|key|keystore|jks)$|(^|/)id_(rsa|dsa|ecdsa|ed25519)$|(^|/)credentials(\.json)?$|(^|/)\.npmrc$|(^|/)\.pypirc$'

# Content shapes. Provider prefixes first (high confidence), then the generic
# assignment shape (lower confidence, kept anyway -- see "deliberately noisy").
CONTENT_RE='-----BEGIN [A-Z ]*PRIVATE KEY-----'
CONTENT_RE="$CONTENT_RE|sk-ant-api[0-9]{2}-[A-Za-z0-9_-]{24,}"
CONTENT_RE="$CONTENT_RE|sk-[A-Za-z0-9]{32,}"
CONTENT_RE="$CONTENT_RE|(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}"
CONTENT_RE="$CONTENT_RE|github_pat_[A-Za-z0-9_]{40,}"
CONTENT_RE="$CONTENT_RE|AKIA[0-9A-Z]{16}"
CONTENT_RE="$CONTENT_RE|xox[baprs]-[A-Za-z0-9-]{12,}"
CONTENT_RE="$CONTENT_RE|AIza[0-9A-Za-z_-]{35}"
CONTENT_RE="$CONTENT_RE|glpat-[A-Za-z0-9_-]{20,}"
Q=$'["\']'   # a quote character, either flavor
CONTENT_RE="$CONTENT_RE|(api[_-]?key|secret|token|password|passwd)${Q}?[[:space:]]*[:=][[:space:]]*${Q}[A-Za-z0-9/+_-]{24,}${Q}"

# Paths whose findings are known-benign. Path-scoped ONLY: a pattern is never
# weakened to quiet a file. Anchored full paths, one per line.
#
#   tests/test_release_gate.py  — fixture secrets, deliberately key-shaped: the
#                                 add-then-delete bypass test needs a string
#                                 that a scanner would flag.
#   tests/secrets-sweep.sh      — this file. It contains the patterns.
#   .claude/skills/fable-codex/scripts/tests/run.sh
#                               — HISTORY ONLY; the skill was moved out of this
#                                 repo and no longer exists at HEAD. Its
#                                 credential-scrubbing test asserts on a
#                                 deliberately synthetic AWS key,
#                                 AKIAABCDEFGHIJKLMNOP -- sequential alphabet,
#                                 never a real credential. Verified 2026-08-11;
#                                 this was the sweep's first real finding and
#                                 the reason to read findings rather than
#                                 assume them.
ALLOWLIST='^tests/test_release_gate\.py$|^tests/secrets-sweep\.sh$|^tests/credential-drill\.sh$'
ALLOWLIST="$ALLOWLIST|^\.claude/skills/fable-codex/scripts/tests/run\.sh$"

# ------------------------------------------------------------------- sweep --

# Every (blob, path) pair that ever existed in a tree.
#
# NOT `git rev-list --objects --all`, which attributes each blob to exactly ONE
# path even when the same content lived at several. That is a real evasion:
# identical content at an allowlisted path and at a forbidden one would report
# only the allowlisted attribution, and the forbidden path would never be named.
# Caught by the credential drill's control arm, which commits the same key to
# `.env` and `.claude/skills/<name>/.env` and saw only one of them.
#
# Walking every commit's tree is O(commits) and slower on a large repo; that is
# the right trade for a check whose whole job is not to miss things.
: > "$WORK/named"
for commit in $(git rev-list --all); do
  git ls-tree -r "$commit" | awk '$2=="blob" {sha=$3; $1=$2=$3=""; sub(/^[ \t]+/,""); print sha "\t" $0}'
done | sort -u > "$WORK/named"

if [ ! -s "$WORK/named" ]; then
  echo "sweep: no blobs in history -- nothing to scan"
  exit 0
fi

findings=0
scanned=0

report() {
  # report <kind> <sha> <path> <detail>
  local kind="$1" sha="$2" path="$3" detail="$4"
  local origin
  origin=$(git log --all --oneline --find-object="$sha" 2>/dev/null | tail -1)
  [ -z "$origin" ] && origin="(unreachable from any commit)"
  echo
  echo "  FINDING [$kind] $path"
  echo "    blob:       $sha"
  echo "    introduced: $origin"
  echo "    detail:     $detail"
  findings=$((findings + 1))
}

while IFS=$'\t' read -r sha path; do
  # A blob can live at several paths across history; judge each pairing.
  if printf '%s' "$path" | grep -Eq "$ALLOWLIST"; then
    continue
  fi

  base="${path##*/}"
  if [ "$base" != ".env.example" ] && printf '%s' "$path" | grep -Eq "$FILENAME_RE"; then
    report "filename" "$sha" "$path" "path matches a never-commit filename shape"
    continue
  fi

  # Binary blobs are read as text on purpose: a key pasted into a binary-ish
  # file is still a key. grep -a keeps it from bailing out.
  # -e is load-bearing: the private-key pattern starts with a dash, which grep
  # would otherwise read as a flag.
  hit=$(git cat-file blob "$sha" 2>/dev/null | grep -aEom1 -e "$CONTENT_RE")
  scanned=$((scanned + 1))
  if [ -n "$hit" ]; then
    # Never print the full match -- the sweep's own output would then carry the
    # secret into a log or a transcript.
    report "content" "$sha" "$path" "matched ${#hit} chars starting '${hit:0:8}...'"
  fi
done < "$WORK/named"

echo
if [ "$findings" -eq 0 ]; then
  echo "sweep: CLEAN -- $scanned blob/path pairs scanned across $(git rev-list --all --count) commits"
  exit 0
fi

echo "sweep: $findings finding(s) across $scanned blob/path pairs"
echo
echo "A finding is not automatically a leak -- read each one. If it IS a real"
echo "credential, rotate it FIRST. Do not rewrite history as a reflex: the"
echo "secret is already distributed to every clone and rotation is the only"
echo "control that actually works."
exit 1
