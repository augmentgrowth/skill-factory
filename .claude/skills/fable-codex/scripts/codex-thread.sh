#!/usr/bin/env bash
set -euo pipefail

# Shared exit codes: 0 success; 2 usage; 3 codex/jq missing; 4 unauthenticated;
# 5 model probe failed; 6 repo denylisted; 7 secret detected; 8 output parse;
# 9 no verdict (extract-verdict.sh only); 10 codex invocation failed.

CODEX_BIN=${FABLE_CODEX_BIN:-codex}
FABLE_HOME=${FABLE_CODEX_HOME:-"$HOME/.fable-codex"}

usage() {
  printf '%s\n' \
    'Usage: codex-thread.sh <reviewer|implementer> <start|resume|fresh|reset|show> [deliverable-slug] [--model M] [--effort E] [--network]' >&2
  exit 2
}

die() {
  local status=$1
  shift
  printf '%s\n' "$*" >&2
  exit "$status"
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
  local slug=${path//\//-}
  slug=${slug#-}
  if [[ -z "$slug" ]]; then
    slug=root
  fi
  printf '%s\n' "$slug"
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
    prefix=${line%/}
    [[ -n "$prefix" ]] || prefix=/
    if [[ "$repo" == "$prefix" || "$repo" == "$prefix/"* || "$prefix" == / ]]; then
      die 6 "Repository is denylisted: $repo"
    fi
  done < "$denylist"
}

check_prompt_for_secrets() {
  local prompt=$1
  local class=

  if grep -Eq 'AKIA[0-9A-Z]{16}' <<< "$prompt"; then
    class=AWS_ACCESS_KEY
  elif grep -Eq -- '-----BEGIN [A-Z ]*PRIVATE KEY-----' <<< "$prompt"; then
    class=PRIVATE_KEY
  elif grep -Eq 'ghp_[A-Za-z0-9]{36}' <<< "$prompt"; then
    class=GITHUB_TOKEN
  elif grep -Eq 'github_pat_[A-Za-z0-9_]{22,}' <<< "$prompt"; then
    class=GITHUB_FINE_GRAINED_TOKEN
  elif grep -Eq 'sk-[A-Za-z0-9_-]{20,}' <<< "$prompt"; then
    class=API_SECRET_KEY
  elif grep -Eq 'xox[baprs]-[A-Za-z0-9-]{10,}' <<< "$prompt"; then
    class=SLACK_TOKEN
  elif grep -Eq 'AIza[0-9A-Za-z_-]{35}' <<< "$prompt"; then
    class=GOOGLE_API_KEY
  elif grep -Eiq "(password|passwd|secret|token)[[:space:]]*[=:][[:space:]]*['\"][^'\"]{8,}['\"]" <<< "$prompt"; then
    class=QUOTED_CREDENTIAL_ASSIGNMENT
  fi

  if [[ -n "$class" ]]; then
    die 7 "Outbound prompt blocked: secret pattern class $class detected; nothing was sent."
  fi
}

ensure_state_dir() {
  mkdir -p "$state_dir"
  chmod 700 "$FABLE_HOME" "$FABLE_HOME/state" "$FABLE_HOME/state/$repo_slug" "$state_dir"
}

log_invocation() {
  local network_flag=$1
  local log_file=$state_dir/invocations.log
  touch "$log_file"
  chmod 600 "$log_file"
  printf '%s\trole=%s\tsubcommand=%s\tmodel=%s\tsandbox=%s\tnetwork=%s\n' \
    "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$role" "$subcommand" "$model" "$sandbox" "$network_flag" >> "$log_file"
}

write_thread_id() {
  local destination=$1
  local thread_id=$2
  local tmp_file=$state_dir/.thread-id.$$
  printf '%s\n' "$thread_id" > "$tmp_file"
  chmod 600 "$tmp_file"
  mv -f "$tmp_file" "$destination"
  chmod 600 "$destination"
}

show_state() {
  local primary=none
  local fresh=none
  if [[ -f "$state_dir/$role.thread_id" ]]; then
    primary=$(< "$state_dir/$role.thread_id")
  fi
  if [[ -f "$state_dir/$role.fresh.thread_id" ]]; then
    fresh=$(< "$state_dir/$role.fresh.thread_id")
  fi
  printf 'repo-slug: %s\n' "$repo_slug"
  printf 'deliverable: %s\n' "$deliverable"
  printf '%s.thread_id: %s\n' "$role" "$primary"
  printf '%s.fresh.thread_id: %s\n' "$role" "$fresh"
  printf 'last invocations:\n'
  if [[ -f "$state_dir/invocations.log" ]]; then
    tail -n 5 "$state_dir/invocations.log"
  else
    printf '(none)\n'
  fi
}

[[ $# -ge 2 ]] || usage
role=$1
subcommand=$2
shift 2

case "$role" in
  reviewer)
    sandbox=read-only
    model=gpt-5.6-sol
    effort=xhigh
    ;;
  implementer)
    sandbox=workspace-write
    model=gpt-5.6-luna
    effort=xhigh
    ;;
  *) usage ;;
esac

case "$subcommand" in
  start|resume|fresh|reset|show) ;;
  *) usage ;;
esac

deliverable=default
if [[ $# -gt 0 && "$1" != --* ]]; then
  deliverable=$1
  shift
fi
[[ "$deliverable" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || die 2 'Deliverable slug must contain only letters, digits, dots, underscores, and hyphens.'

network_requested=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)
      [[ $# -ge 2 ]] || usage
      model=$2
      shift 2
      ;;
    --effort)
      [[ $# -ge 2 ]] || usage
      effort=$2
      shift 2
      ;;
    --network)
      network_requested=true
      shift
      ;;
    *) usage ;;
  esac
done

repo=$(target_repo)
repo_slug=$(repo_slug_for "$repo")
state_dir=$FABLE_HOME/state/$repo_slug/$deliverable

if [[ "$subcommand" == reset ]]; then
  rm -rf -- "$state_dir"
  printf 'RESET: %s\n' "$deliverable"
  exit 0
fi

if [[ "$subcommand" == show ]]; then
  show_state
  exit 0
fi

# This is deliberately the first action for any operation that could send a prompt.
check_denylist "$repo"

prompt=$(cat)
check_prompt_for_secrets "$prompt"

command -v "$CODEX_BIN" >/dev/null 2>&1 || die 3 "Codex binary not installed or not executable: $CODEX_BIN"

if [[ "$subcommand" == resume && ! -f "$state_dir/$role.thread_id" ]]; then
  die 2 "No stored $role thread for '$deliverable'; run start first."
fi

umask 077
ensure_state_dir

network_flag=false
network_config=
if [[ "$role" == implementer ]]; then
  if [[ "$network_requested" == true ]]; then
    network_flag=true
    network_config=sandbox_workspace_write.network_access=true
    printf '%s\n' 'NETWORK: enabled for this run — report outbound activity in the completion report' >&2
  else
    network_config=sandbox_workspace_write.network_access=false
  fi
fi

tmp_dir=$(mktemp -d "${TMPDIR:-/tmp}/fable-codex.XXXXXX")
trap 'rm -rf -- "$tmp_dir"' EXIT
json_file=$tmp_dir/events.jsonl
stderr_file=$tmp_dir/codex.stderr
message_tmp=$tmp_dir/last-message.md

args=()
case "$subcommand" in
  start|fresh)
    args=(exec --json -s "$sandbox" -m "$model" -c "model_reasoning_effort=$effort")
    ;;
  resume)
    thread_id=$(< "$state_dir/$role.thread_id")
    args=(exec resume "$thread_id" --json -c "sandbox_mode=$sandbox" -m "$model" -c "model_reasoning_effort=$effort")
    ;;
esac
if [[ -n "$network_config" ]]; then
  args+=(-c "$network_config")
fi
args+=(-o "$message_tmp" -)

log_invocation "$network_flag"
if ! printf '%s' "$prompt" | "$CODEX_BIN" "${args[@]}" > "$json_file" 2> "$stderr_file"; then
  cat "$stderr_file" >&2
  die 10 "Codex invocation failed."
fi
cat "$stderr_file" >&2

if ! thread_id=$(jq -r 'select(.type == "thread.started") | .thread_id // empty' "$json_file" 2>/dev/null | sed -n '1p'); then
  die 8 'Could not parse codex JSON output.'
fi
[[ -n "$thread_id" ]] || die 8 'Codex output did not contain a thread.started event.'
[[ -f "$message_tmp" ]] || die 8 'Codex did not write the requested last-message file.'

last_message=$state_dir/$role.last-message.md
mv -f "$message_tmp" "$last_message"
chmod 600 "$last_message"
if [[ "$subcommand" == fresh ]]; then
  write_thread_id "$state_dir/$role.fresh.thread_id" "$thread_id"
else
  write_thread_id "$state_dir/$role.thread_id" "$thread_id"
fi

printf 'THREAD_ID: %s\n' "$thread_id"
cat "$last_message"
