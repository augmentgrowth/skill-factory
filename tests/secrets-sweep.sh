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
# COVERAGE BOUNDARY, stated because "the whole history" overclaims: reachable
# from a ref. Objects reachable only from the reflog, a dropped stash, or a
# dangling commit are NOT scanned. Those are local-only and never pushed, so
# they cannot leak through a release -- but if you are auditing a machine rather
# than a release, `git fsck --lost-found` is the other half again.
#
# Deliberately noisy. A sweep that under-reports is worse than one that makes
# you look at something benign, so the patterns are broad and the only way to
# quiet a finding is to allowlist its *path* -- never to weaken a pattern.
#
# Usage:  tests/secrets-sweep.sh [repo-path] [--since <ref>]
#         repo-path defaults to the repo this script lives in
#
#   --since <ref>  scan only commits reachable from HEAD but not from <ref>,
#                  instead of all history. This is what the release gate uses on
#                  every push. Full history is O(commits) and already takes
#                  seconds on a small repo, so running it on every push would
#                  degrade into a minute-long stall as history grows -- and a
#                  check people learn to dread is a check they route around with
#                  --no-verify. History only grows, so once a full sweep is
#                  clean, scanning what is new keeps it clean.
#
# Exit:   0 clean, 1 findings, 2 usage/environment error

# pipefail is load-bearing, not hygiene. Without it a git failure mid-sweep
# yields a short blob list and the script still prints CLEAN -- a broken scan
# and a clean repo would be indistinguishable, which is the one outcome a
# fail-closed check must never allow.
set -u -o pipefail

REPO=""
SINCE=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --since) SINCE="${2:-}"; [ -n "$SINCE" ] || { echo "--since needs a ref" >&2; exit 2; }; shift 2 ;;
    -*)      echo "unknown option: $1" >&2; exit 2 ;;
    *)       [ -z "$REPO" ] || { echo "unexpected argument: $1" >&2; exit 2; }; REPO="$1"; shift ;;
  esac
done
REPO="${REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$REPO" 2>/dev/null || { echo "not a directory: $REPO" >&2; exit 2; }
git rev-parse --git-dir >/dev/null 2>&1 || { echo "not a git repo: $REPO" >&2; exit 2; }

WORK="$(mktemp -d "${TMPDIR:-/tmp}/secrets-sweep.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

# ---------------------------------------------------------------- patterns --
#
# Filenames that should never be committed at any depth. `.env.example` is the
# documented convention and is excluded below, by name, at the match site.
FILENAME_RE='(^|/)\.env($|\.)|\.(pem|p12|pfx|key|keystore|jks|ppk|p8)$|(^|/)id_(rsa|dsa|ecdsa|ed25519)$|(^|/)credentials(\.json)?$|(^|/)\.npmrc$|(^|/)\.pypirc$|(^|/)\.netrc$|(^|/)\.git-credentials$'

# Content shapes. Provider prefixes first (high confidence), then the generic
# assignment shape (lower confidence, kept anyway -- see "deliberately noisy").
CONTENT_RE='-----BEGIN [A-Z ]*PRIVATE KEY-----'
CONTENT_RE="$CONTENT_RE|sk-ant-api[0-9]{2}-[A-Za-z0-9_-]{24,}"
CONTENT_RE="$CONTENT_RE|sk-(proj-)?[A-Za-z0-9_-]{32,}"
CONTENT_RE="$CONTENT_RE|(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}"
CONTENT_RE="$CONTENT_RE|github_pat_[A-Za-z0-9_]{40,}"
CONTENT_RE="$CONTENT_RE|AKIA[0-9A-Z]{16}"
CONTENT_RE="$CONTENT_RE|xox[baprs]-[A-Za-z0-9-]{12,}"
CONTENT_RE="$CONTENT_RE|AIza[0-9A-Za-z_-]{35}"
CONTENT_RE="$CONTENT_RE|glpat-[A-Za-z0-9_-]{20,}"
CONTENT_RE="$CONTENT_RE|eyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\."
CONTENT_RE="$CONTENT_RE|[Aa]uthorization:[[:space:]]*(Bearer|Basic|token)[[:space:]]+[A-Za-z0-9._~+/=-]{16,}"

# The generic assignment shape. QUOTES ARE OPTIONAL ON BOTH SIDES, and that is
# the whole point of this line: requiring them is what let three genuine
# credentials through a CLEAN verdict --
#
#   AWS_SECRET_ACCESS_KEY=wJalr...        (unquoted, as every .env file writes it)
#   password: hunter2...                  (unquoted YAML)
#   export DB_PASSWORD=s3cret...          (unquoted shell)
#
# The value class admits . and = so base64 padding and dotted tokens match.
Q=$'["\']?'   # an optional quote, either flavor
CONTENT_RE="$CONTENT_RE|(api[_-]?key|secret([_-]?access[_-]?key)?|token|password|passwd|passphrase)${Q}[[:space:]]*[:=][[:space:]]*${Q}[A-Za-z0-9/+_.=-]{20,}"

# NOT scanned for, deliberately: bare high-entropy hex/base64 runs with no
# assignment context. A 40-char hex run is also every git SHA, and this repo's
# docs and commit messages are full of them -- that pattern would drown the
# real signal and train whoever runs this to ignore it. The assignment shapes
# above are how a credential actually appears in a file. Stated here so the
# boundary is a decision on the record rather than an oversight.

# Known-synthetic VALUES, not paths.
#
# This used to be a path allowlist, and that was the wrong primitive: exempting
# tests/credential-drill.sh meant a REAL key pasted into that file was invisible,
# and `tests/` is an authorized publish path, so the release gate would have
# shipped it. Blinding a whole file to protect one fixture string trades a large
# hole for a small convenience.
#
# Exempting the exact literal instead keeps every other secret in those same
# files in scope.
#
# THE RULE THAT MAKES THIS WORK: a value cannot be both exempt here and used to
# prove detection. Exempting every synthetic key in the suite broke every
# detection test at once, which is the correct failure -- the tests were then
# asserting that the sweep finds strings it had just been told to ignore.
#
# So the two roles are kept disjoint:
#
#   this list          values that physically exist in this repo's files or
#                      history, and are known-synthetic
#   the test suite     values that appear NOWHERE in the repo, assembled at
#                      runtime so committing the test does not put a
#                      key-shaped literal into a scanned file
#
# A real key pasted into any of these files is still caught -- verified by
# committing one to tests/credential-drill.sh and watching it fail. That is the
# whole reason this replaced a path allowlist, which blinded entire files and
# would have shipped such a key through an authorized publish path.
#
# Adding an entry is a deliberate, reviewable act, and the first question is
# whether the file could avoid the literal instead. Removing a PATTERN to quiet
# a file remains forbidden.
FIXTURES=(
  # fable-codex credential-scrubbing test (history only; the skill left this repo)
  "AKIAABCDEFGHIJKLMNOP"
  "TOKEN=abcdef0123456789abcdef"
  # The credential drill's synthetic key, and the detection fixtures the test
  # suite used before it switched to assembling secrets at runtime. All of these
  # are frozen in history, so no edit can reach them -- and rewriting history to
  # remove a fake key would break the rule that exists for real ones.
  "sk-ant-api03-FAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKE"
  "AKIA0987654321ZZZZZZ"
  "wJalrXUtnFEMIK7MDENGbPxRfiCYEXAMPLEKEY"
  "hunter2hunter2hunter2hunter2"
  "s3cretV4lueThatIsQuiteLongIndeed99"
  "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0"
)

# Containment is checked BOTH ways on purpose. A pattern's match does not always
# span the whole fixture -- the JWT rule ends at the final dot, so its match is a
# 49-char prefix of the 52-char fixture string -- and a one-directional check
# silently stopped recognizing it.
is_fixture() {
  local candidate="$1" known
  for known in "${FIXTURES[@]}"; do
    case "$candidate" in *"$known"*) return 0 ;; esac
    case "$known" in *"$candidate"*) return 0 ;; esac
  done
  return 1
}

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
#
# -z plus core.quotePath=false is not pedantry: without it git quotes paths
# containing non-ASCII or control characters, and awk's default whitespace
# splitting mangles paths containing runs of spaces. Either one turns a
# forbidden path into an unrecognizable string that the filename rules no
# longer match -- an evasion, not a cosmetic bug.
if [ -n "$SINCE" ]; then
  # An unknown ref must never quietly become "scan nothing" -- that is exactly
  # the fail-open shape this script exists to avoid.
  git rev-parse --verify --quiet "$SINCE^{commit}" >/dev/null \
    || { echo "sweep: --since ref not found: $SINCE" >&2; exit 2; }
  SCOPE="commits since ${SINCE:0:8}"
  git rev-list "$SINCE..HEAD" > "$WORK/commits" \
    || { echo "sweep: FAILED to list commits since $SINCE" >&2; exit 2; }
else
  SCOPE="all history"
  git rev-list --all > "$WORK/commits" || { echo "sweep: FAILED to list commits" >&2; exit 2; }
fi

if [ ! -s "$WORK/commits" ]; then
  echo "sweep: CLEAN -- no commits in scope ($SCOPE)"
  exit 0
fi

: > "$WORK/named"
while read -r commit; do
  git -c core.quotePath=false ls-tree -r -z "$commit" \
    || { echo "sweep: FAILED to read tree $commit" >&2; exit 2; }
done < "$WORK/commits" \
  | tr '\0' '\n' \
  | awk -F'\t' '{ split($1, m, " "); if (m[2] == "blob") print m[3] "\t" $2 }' \
  | sort -u > "$WORK/named"

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
  scanned=$((scanned + 1))

  # `.env.example` is exempt from the FILENAME rule only -- it is the documented
  # convention and must be committable. It is still content-scanned below,
  # because "the template file" is exactly where someone pastes a real key by
  # accident.
  base="${path##*/}"
  if [ "$base" != ".env.example" ] && printf '%s' "$path" | grep -Eq "$FILENAME_RE"; then
    report "filename" "$sha" "$path" "path matches a never-commit filename shape"
    continue
  fi

  # Binary blobs are read as text on purpose: a key pasted into a binary-ish
  # file is still a key. grep -a keeps it from bailing out.
  # -e is load-bearing: the private-key pattern starts with a dash, which grep
  # would otherwise read as a flag.
  blob=$(git cat-file blob "$sha" 2>/dev/null) \
    || { echo "sweep: FAILED to read blob $sha ($path)" >&2; exit 2; }
  # -i is load-bearing. Environment variables are UPPERCASE by convention --
  # AWS_SECRET_ACCESS_KEY, DB_PASSWORD -- so a case-sensitive keyword list
  # misses the single most common way a credential is written down.
  #
  # EVERY match, not just the first. `-m1` would stop at the first hit, so a
  # known fixture string appearing above a real key would clear the whole file
  # -- the exact shielding the value allowlist has to be careful not to create.
  while IFS= read -r hit; do
    [ -n "$hit" ] || continue
    is_fixture "$hit" && continue
    # Never print the full match -- the sweep's own output would otherwise carry
    # the secret into a log or a transcript.
    report "content" "$sha" "$path" "matched ${#hit} chars starting '${hit:0:8}...'"
    break   # one finding per blob/path is enough to fail it
  done < <(printf '%s' "$blob" | grep -aioE -e "$CONTENT_RE" || true)
done < "$WORK/named"

echo
if [ "$findings" -eq 0 ]; then
  echo "sweep: CLEAN -- $scanned blob/path pairs across $(wc -l < "$WORK/commits" | tr -d ' ') commit(s) ($SCOPE)"
  exit 0
fi

echo "sweep: $findings finding(s) across $scanned blob/path pairs"
echo
echo "A finding is not automatically a leak -- read each one. If it IS a real"
echo "credential, rotate it FIRST. Do not rewrite history as a reflex: the"
echo "secret is already distributed to every clone and rotation is the only"
echo "control that actually works."
exit 1
