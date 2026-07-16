#!/usr/bin/env bash
set -euo pipefail

# Shared exit codes: 0 success; 2 usage; 3 codex/jq missing; 4 unauthenticated;
# 5 model probe failed; 6 repo denylisted; 7 secret detected; 8 output parse;
# 9 no verdict (extract-verdict.sh only); 10 codex invocation failed.

CODEX_BIN=${FABLE_CODEX_BIN:-codex}
FABLE_HOME=${FABLE_CODEX_HOME:-"$HOME/.fable-codex"}

die() {
  local status=$1
  shift
  printf '%s\n' "$*" >&2
  exit "$status"
}

usage() {
  printf '%s\n' 'Usage: preflight.sh [--probe-model M]' >&2
  exit 2
}

target_repo() {
  local repo
  if repo=$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null); then
    (cd "$repo" && pwd -P)
  else
    pwd -P
  fi
}

repo_slug_for() {
  local path=$1
  local base=${path##*/}
  local sanitized digest

  [[ -n "$base" ]] || base=root
  sanitized=${base//[^A-Za-z0-9._-]/-}
  sanitized=${sanitized:0:40}
  digest=$(printf '%s' "$path" | shasum -a 256)
  digest=${digest%% *}
  printf '%s-%s\n' "$sanitized" "${digest:0:12}"
}

check_denylist() {
  local repo=$1
  local denylist=$FABLE_HOME/denylist
  local line prefix

  [[ -f "$denylist" ]] || return 0
  while IFS= read -r line || [[ -n "$line" ]]; do
    line=${line#"${line%%[![:space:]]*}"}
    line=${line%"${line##*[![:space:]]}"}
    [[ -z "$line" || "$line" == \#* ]] && continue
    case "$line" in
      '~') prefix=$HOME ;;
      \~/*) prefix=$HOME/${line:2} ;;
      *) prefix=$line ;;
    esac
    prefix=${prefix%/}
    [[ -n "$prefix" ]] || prefix=/
    if [[ -d "$prefix" ]]; then
      prefix=$(cd "$prefix" && pwd -P)
    fi
    if [[ "$repo" == "$prefix" || "$repo" == "$prefix/"* || "$prefix" == / ]]; then
      die 6 "Repository is denylisted: $repo"
    fi
  done < "$denylist"
}

probe_model=
if [[ $# -gt 0 ]]; then
  [[ $# -eq 2 && "$1" == --probe-model ]] || usage
  probe_model=$2
fi

command -v "$CODEX_BIN" >/dev/null 2>&1 || die 3 "Codex is not installed or not executable: $CODEX_BIN"
command -v jq >/dev/null 2>&1 || die 3 'jq is not installed; install jq before running fable-codex.'

if ! auth_output=$("$CODEX_BIN" login status 2>&1); then
  die 4 'Codex is not authenticated; run codex login first.'
fi
if printf '%s' "$auth_output" | grep -Eiq 'logged[[:space:]-]*out|not[[:space:]]+(logged[[:space:]]+in|authenticated)'; then
  auth_scan_status=0
else
  auth_scan_status=$?
fi
case "$auth_scan_status" in
  0) die 4 'Codex is not authenticated; run codex login first.' ;;
  1) ;;
  *) die 4 'could not verify authentication' ;;
esac

repo=$(target_repo)
check_denylist "$repo"

if [[ -n "$probe_model" ]]; then
  tmp_dir=$(mktemp -d "${TMPDIR:-/tmp}/fable-codex-preflight.XXXXXX")
  trap 'rm -rf -- "$tmp_dir"' EXIT
  events=$tmp_dir/events.jsonl
  errors=$tmp_dir/stderr
  if ! printf '%s\n' 'Reply with exactly: OK' | \
    "$CODEX_BIN" exec --json -s read-only -m "$probe_model" -c model_reasoning_effort=low - > "$events" 2> "$errors"; then
    cat "$errors" >&2
    die 5 "Model probe failed for $probe_model."
  fi
  if ! jq -e 'select(.type == "turn.completed")' "$events" >/dev/null 2>&1; then
    die 5 "Model probe failed for $probe_model: no turn.completed event."
  fi
fi

version=$("$CODEX_BIN" --version 2>/dev/null | sed -n '1p')
[[ -n "$version" ]] || version='version unknown'
printf 'PREFLIGHT: OK (%s)\n' "$version"

# First-run callers should use --probe-model gpt-5.6-sol once; later runs may skip it.
