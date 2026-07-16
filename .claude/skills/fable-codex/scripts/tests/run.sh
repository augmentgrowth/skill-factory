#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
SCRIPTS_DIR=$(cd "$SCRIPT_DIR/.." && pwd -P)
THREAD_SCRIPT=$SCRIPTS_DIR/codex-thread.sh
PREFLIGHT_SCRIPT=$SCRIPTS_DIR/preflight.sh
VERDICT_SCRIPT=$SCRIPTS_DIR/extract-verdict.sh
STUB_CODEX=$SCRIPT_DIR/stub-codex

tmp_root=$(mktemp -d "${TMPDIR:-/tmp}/fable-codex-tests.XXXXXX")
trap 'rm -rf -- "$tmp_root"' EXIT

repo=$tmp_root/target-repo
mkdir -p "$repo"
git -C "$repo" init -q

export FABLE_CODEX_HOME=$tmp_root/fable-home
export FABLE_CODEX_BIN=$STUB_CODEX
export STUB_LOG=$tmp_root/stub.log
export STUB_STDIN_FILE=$tmp_root/stub.stdin
: > "$STUB_LOG"
: > "$STUB_STDIN_FILE"

repo_path=$(cd "$repo" && pwd -P)
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
repo_slug=$(repo_slug_for "$repo_path")
state_root=$FABLE_CODEX_HOME/state/$repo_slug

total=0
passed=0
failed=0
scenario_failed=0

note_failure() {
  printf '  %s\n' "$*" >&2
  scenario_failed=1
  return 1
}

run_scenario() {
  local name=$1
  local function_name=$2
  total=$((total + 1))
  scenario_failed=0
  "$function_name" || scenario_failed=1
  if [[ $scenario_failed -eq 0 ]]; then
    passed=$((passed + 1))
    printf 'PASS %02d - %s\n' "$total" "$name"
  else
    failed=$((failed + 1))
    printf 'FAIL %02d - %s\n' "$total" "$name"
  fi
}

mode_of() {
  local path=$1
  local mode
  if mode=$(stat -f '%Lp' "$path" 2>/dev/null) && [[ "$mode" =~ ^[0-7]{3,4}$ ]]; then
    printf '%s\n' "$mode"
  else
    stat -c '%a' "$path"
  fi
}

scenario_start_reviewer() {
  local output
  : > "$STUB_LOG"
  output=$(cd "$repo" && printf '%s' 'Review this.' | "$THREAD_SCRIPT" reviewer start start-reviewer) || \
    note_failure 'reviewer start returned non-zero'
  [[ $(< "$state_root/start-reviewer/reviewer.thread_id") == t123 ]] || \
    note_failure 'reviewer.thread_id did not contain t123'
  grep -Fq 'THREAD_ID: t123' <<< "$output" || note_failure 'stdout lacked thread marker'
  grep -Fq 'VERDICT: APPROVED' <<< "$output" || note_failure 'stdout lacked captured last message'
}

scenario_resume_reviewer() {
  local output log_line
  (cd "$repo" && printf '%s' 'First.' | "$THREAD_SCRIPT" reviewer start resume-reviewer >/dev/null) || \
    note_failure 'setup start failed'
  : > "$STUB_LOG"
  output=$(cd "$repo" && printf '%s' 'Continue.' | "$THREAD_SCRIPT" reviewer resume resume-reviewer) || \
    note_failure 'reviewer resume returned non-zero'
  log_line=$(tail -n 1 "$STUB_LOG")
  grep -Eq '(^|[[:space:]])exec[[:space:]]+resume[[:space:]]+t123([[:space:]]|$)' <<< "$log_line" || \
    note_failure 'resume argv lacked exec resume t123'
  grep -Eq '(^|[[:space:]])-c[[:space:]]+sandbox_mode="?read-only"?([[:space:]]|$)' <<< "$log_line" || \
    note_failure 'resume argv did not re-pin read-only sandbox'
  if grep -Eq '(^|[[:space:]])-s([[:space:]]|$)' <<< "$log_line"; then
    note_failure 'resume argv incorrectly contained -s'
  fi
  grep -Fq 'THREAD_ID: t123' <<< "$output" || note_failure 'resume stdout lacked thread marker'
}

scenario_start_implementer() {
  local log_line
  : > "$STUB_LOG"
  (cd "$repo" && printf '%s' 'Implement this.' | "$THREAD_SCRIPT" implementer start start-implementer >/dev/null) || \
    note_failure 'implementer start returned non-zero'
  log_line=$(tail -n 1 "$STUB_LOG")
  grep -Eq '(^|[[:space:]])-s[[:space:]]+workspace-write([[:space:]]|$)' <<< "$log_line" || \
    note_failure 'implementer argv lacked workspace-write sandbox'
  grep -Eq '(^|[[:space:]])-m[[:space:]]+gpt-5\.6-luna([[:space:]]|$)' <<< "$log_line" || \
    note_failure 'implementer argv lacked Luna model'
}

scenario_overrides() {
  local log_line
  : > "$STUB_LOG"
  (cd "$repo" && printf '%s' 'Override.' | "$THREAD_SCRIPT" reviewer start overrides \
    --model gpt-5.6-luna --effort medium >/dev/null) || note_failure 'override start returned non-zero'
  log_line=$(tail -n 1 "$STUB_LOG")
  grep -Eq '(^|[[:space:]])-m[[:space:]]+gpt-5\.6-luna([[:space:]]|$)' <<< "$log_line" || \
    note_failure 'model override did not reach argv'
  grep -Eq '(^|[[:space:]])-c[[:space:]]+model_reasoning_effort=medium([[:space:]]|$)' <<< "$log_line" || \
    note_failure 'effort override did not reach argv'
}

scenario_fresh_reviewer() {
  STUB_THREAD_ID=t-primary bash -c "cd \"$repo\" && printf '%s' First | \"$THREAD_SCRIPT\" reviewer start fresh-reviewer >/dev/null" || \
    note_failure 'setup start failed'
  STUB_THREAD_ID=t-independent bash -c "cd \"$repo\" && printf '%s' Fresh | \"$THREAD_SCRIPT\" reviewer fresh fresh-reviewer >/dev/null" || \
    note_failure 'fresh call failed'
  [[ $(< "$state_root/fresh-reviewer/reviewer.thread_id") == t-primary ]] || \
    note_failure 'fresh overwrote the primary thread id'
  [[ $(< "$state_root/fresh-reviewer/reviewer.fresh.thread_id") == t-independent ]] || \
    note_failure 'fresh thread id was not stored separately'
}

scenario_nonzero_preserves_state() {
  local status prior_message
  STUB_THREAD_ID=t-prior STUB_LAST_MSG='Prior last message' \
    bash -c "cd \"$repo\" && printf '%s' First | \"$THREAD_SCRIPT\" reviewer start nonzero >/dev/null" || \
    note_failure 'setup start failed'
  prior_message=$(< "$state_root/nonzero/reviewer.last-message.md")
  set +e
  (cd "$repo" && printf '%s' 'Fail now.' | STUB_THREAD_ID=t-bad STUB_LAST_MSG='Bad replacement' STUB_EXIT_CODE=42 \
    "$THREAD_SCRIPT" reviewer start nonzero) > "$tmp_root/nonzero.out" 2> "$tmp_root/nonzero.err"
  status=$?
  set -e
  [[ $status -eq 10 ]] || note_failure "expected exit 10, got $status"
  [[ $(< "$state_root/nonzero/reviewer.thread_id") == t-prior ]] || \
    note_failure 'failed invocation changed the prior thread id'
  [[ $(< "$state_root/nonzero/reviewer.last-message.md") == "$prior_message" ]] || \
    note_failure 'failed invocation changed the prior last message'
}

scenario_missing_thread_event() {
  local status
  rm -rf -- "$state_root/missing-event"
  set +e
  (cd "$repo" && printf '%s' 'No event.' | STUB_OMIT_THREAD_STARTED=1 \
    "$THREAD_SCRIPT" reviewer start missing-event) > "$tmp_root/missing.out" 2> "$tmp_root/missing.err"
  status=$?
  set -e
  [[ $status -eq 8 ]] || note_failure "expected exit 8, got $status"
  [[ ! -e "$state_root/missing-event/reviewer.thread_id" ]] || \
    note_failure 'missing event left a thread file behind'
}

scenario_reset_and_show() {
  local output before after
  (cd "$repo" && printf '%s' 'A.' | STUB_THREAD_ID=t-a "$THREAD_SCRIPT" reviewer start reset-a >/dev/null) || \
    note_failure 'reset-a setup failed'
  (cd "$repo" && printf '%s' 'B.' | STUB_THREAD_ID=t-b "$THREAD_SCRIPT" reviewer start reset-b >/dev/null) || \
    note_failure 'reset-b setup failed'
  (cd "$repo" && "$THREAD_SCRIPT" reviewer reset reset-a >/dev/null) || note_failure 'reset failed'
  [[ ! -e "$state_root/reset-a" ]] || note_failure 'target deliverable survived reset'
  [[ -f "$state_root/reset-b/reviewer.thread_id" ]] || note_failure 'sibling deliverable was removed'
  before=$(wc -c < "$STUB_LOG")
  output=$(cd "$repo" && "$THREAD_SCRIPT" reviewer show reset-b) || note_failure 'show failed'
  after=$(wc -c < "$STUB_LOG")
  [[ $before -eq $after ]] || note_failure 'show invoked codex'
  grep -Fq 'reviewer.thread_id: t-b' <<< "$output" || note_failure 'show did not print stored id'
}

scenario_scrub_gate() {
  local status secret='AKIAABCDEFGHIJKLMNOP'
  : > "$STUB_LOG"
  set +e
  (cd "$repo" && printf '%s' "credential $secret" | "$THREAD_SCRIPT" reviewer start scrub) \
    > "$tmp_root/scrub.out" 2> "$tmp_root/scrub.err"
  status=$?
  set -e
  [[ $status -eq 7 ]] || note_failure "expected exit 7, got $status"
  [[ ! -s "$STUB_LOG" ]] || note_failure 'scrubbed prompt invoked codex'
  grep -Fq 'AWS_ACCESS_KEY' "$tmp_root/scrub.err" || note_failure 'scrub error omitted pattern class'
  if grep -Fq "$secret" "$tmp_root/scrub.err"; then
    note_failure 'scrub error leaked the matched value'
  fi
}

scenario_denylist() {
  local start_status preflight_status
  mkdir -p "$FABLE_CODEX_HOME"
  printf '%s\n' "$repo_path" > "$FABLE_CODEX_HOME/denylist"
  set +e
  (cd "$repo" && printf '%s' 'Blocked.' | "$THREAD_SCRIPT" reviewer start denied) \
    > "$tmp_root/denied.out" 2> "$tmp_root/denied.err"
  start_status=$?
  (cd "$repo" && "$PREFLIGHT_SCRIPT") > "$tmp_root/deny-preflight.out" 2> "$tmp_root/deny-preflight.err"
  preflight_status=$?
  set -e
  rm -f -- "$FABLE_CODEX_HOME/denylist"
  [[ $start_status -eq 6 ]] || note_failure "start expected exit 6, got $start_status"
  [[ $preflight_status -eq 6 ]] || note_failure "preflight expected exit 6, got $preflight_status"
}

scenario_network_policy() {
  local default_args enabled_args
  : > "$STUB_LOG"
  (cd "$repo" && printf '%s' 'Offline.' | "$THREAD_SCRIPT" implementer start network-off >/dev/null) || \
    note_failure 'default network call failed'
  default_args=$(tail -n 1 "$STUB_LOG")
  grep -Eq 'sandbox_workspace_write\.network_access=false([[:space:]]|$)' <<< "$default_args" || \
    note_failure 'default implementer argv did not disable network'

  : > "$STUB_LOG"
  (cd "$repo" && printf '%s' 'Online.' | "$THREAD_SCRIPT" implementer start network-on --network >/dev/null) \
    2> "$tmp_root/network.err" || note_failure 'enabled network call failed'
  enabled_args=$(tail -n 1 "$STUB_LOG")
  grep -Eq 'sandbox_workspace_write\.network_access=true([[:space:]]|$)' <<< "$enabled_args" || \
    note_failure 'network override did not reach argv'
  grep -Fq 'NETWORK: enabled for this run' "$tmp_root/network.err" || \
    note_failure 'network override emitted no notice'
  grep -Fq 'network=true' "$state_root/network-on/invocations.log" || \
    note_failure 'network flag was not logged'
}

scenario_state_hygiene() {
  local path expected actual
  (cd "$repo" && printf '%s' 'Modes.' | "$THREAD_SCRIPT" reviewer start modes >/dev/null) || \
    note_failure 'state hygiene setup failed'
  for path in "$FABLE_CODEX_HOME" "$FABLE_CODEX_HOME/state" "$state_root" "$state_root/modes"; do
    expected=700
    actual=$(mode_of "$path")
    [[ "$actual" == "$expected" ]] || note_failure "$path mode was $actual, expected $expected"
  done
  for path in "$state_root/modes/reviewer.thread_id" "$state_root/modes/reviewer.last-message.md" \
    "$state_root/modes/invocations.log"; do
    expected=600
    actual=$(mode_of "$path")
    [[ "$actual" == "$expected" ]] || note_failure "$path mode was $actual, expected $expected"
  done
}

scenario_extract_verdict() {
  local status output
  printf '%s\n' 'Review complete.' 'VERDICT: APPROVED' > "$tmp_root/approved.md"
  output=$("$VERDICT_SCRIPT" "$tmp_root/approved.md") || note_failure 'approved verdict returned non-zero'
  [[ ${output%%$'\n'*} == 'VERDICT: APPROVED' ]] || note_failure 'approved tag was not first'

  printf '%s\n' 'Intro' 'FINDINGS:' '- Fix the edge case.' 'VERDICT: CHANGES_REQUIRED' > "$tmp_root/changes.md"
  output=$("$VERDICT_SCRIPT" "$tmp_root/changes.md") || note_failure 'changes verdict returned non-zero'
  [[ ${output%%$'\n'*} == 'VERDICT: CHANGES_REQUIRED' ]] || note_failure 'changes tag was not first'
  grep -Fq 'FINDINGS:' <<< "$output" || note_failure 'findings heading was omitted'
  grep -Fq -- '- Fix the edge case.' <<< "$output" || note_failure 'findings body was omitted'

  set +e
  output=$(printf '%s\n' 'No structured decision.' | "$VERDICT_SCRIPT" 2> "$tmp_root/no-verdict.err")
  status=$?
  set -e
  [[ $status -eq 9 ]] || note_failure "no verdict expected exit 9, got $status"
  [[ "$output" == NO_VERDICT ]] || note_failure 'no verdict did not print NO_VERDICT'
}

scenario_preflight_missing_codex() {
  local status
  set +e
  (cd "$repo" && FABLE_CODEX_BIN=/nonexistent/codex "$PREFLIGHT_SCRIPT") \
    > "$tmp_root/no-codex.out" 2> "$tmp_root/no-codex.err"
  status=$?
  set -e
  [[ $status -eq 3 ]] || note_failure "missing codex expected exit 3, got $status"
  grep -Eiq 'not installed|not executable' "$tmp_root/no-codex.err" || \
    note_failure 'missing codex message was not human-readable'
}

scenario_verdict_must_be_final() {
  local status output
  printf '%s\n' 'VERDICT: APPROVED' 'Trailing caveat.' > "$tmp_root/mid-verdict.md"
  set +e
  output=$("$VERDICT_SCRIPT" "$tmp_root/mid-verdict.md" 2> "$tmp_root/mid-verdict.err")
  status=$?
  set -e
  [[ $status -eq 9 ]] || note_failure "mid-file verdict expected exit 9, got $status"
  [[ "$output" == NO_VERDICT ]] || note_failure 'mid-file verdict did not print NO_VERDICT'

  printf '%s\n' 'Review complete.' 'VERDICT: APPROVED' '' '   ' > "$tmp_root/trailing-blanks.md"
  output=$("$VERDICT_SCRIPT" "$tmp_root/trailing-blanks.md") || \
    note_failure 'verdict followed only by blank lines returned non-zero'
  [[ ${output%%$'\n'*} == 'VERDICT: APPROVED' ]] || \
    note_failure 'trailing blank lines invalidated the verdict'
}

scenario_unquoted_credential_scrub() {
  local status
  : > "$STUB_LOG"
  set +e
  (cd "$repo" && printf '%s' 'API_TOKEN=abcdef0123456789abcdef' | \
    "$THREAD_SCRIPT" reviewer start unquoted-secret) \
    > "$tmp_root/unquoted-secret.out" 2> "$tmp_root/unquoted-secret.err"
  status=$?
  set -e
  [[ $status -eq 7 ]] || note_failure "unquoted credential expected exit 7, got $status"
  [[ ! -s "$STUB_LOG" ]] || note_failure 'unquoted credential invoked codex'
  grep -Fq 'UNQUOTED_CREDENTIAL_ASSIGNMENT' "$tmp_root/unquoted-secret.err" || \
    note_failure 'unquoted credential error omitted pattern class'

  : > "$STUB_LOG"
  (cd "$repo" && printf '%s' 'TOKEN=abc123' | "$THREAD_SCRIPT" reviewer start short-placeholder >/dev/null) || \
    note_failure 'short credential placeholder was blocked'
  [[ -s "$STUB_LOG" ]] || note_failure 'short credential placeholder did not invoke codex'
}

scenario_collision_proof_repo_slug() {
  local repo_one=$tmp_root/slug-collision/a-b/c
  local repo_two=$tmp_root/slug-collision/a/b-c
  local path_one path_two slug_one slug_two
  mkdir -p "$repo_one" "$repo_two"
  git -C "$repo_one" init -q
  git -C "$repo_two" init -q
  path_one=$(cd "$repo_one" && pwd -P)
  path_two=$(cd "$repo_two" && pwd -P)
  slug_one=$(repo_slug_for "$path_one")
  slug_two=$(repo_slug_for "$path_two")
  [[ "$slug_one" != "$slug_two" ]] || note_failure 'crafted repo paths produced the same slug'
  (cd "$repo_one" && printf '%s' 'One.' | STUB_THREAD_ID=t-one \
    "$THREAD_SCRIPT" reviewer start slug-test >/dev/null) || note_failure 'first slug setup failed'
  (cd "$repo_two" && printf '%s' 'Two.' | STUB_THREAD_ID=t-two \
    "$THREAD_SCRIPT" reviewer start slug-test >/dev/null) || note_failure 'second slug setup failed'
  [[ $(< "$FABLE_CODEX_HOME/state/$slug_one/slug-test/reviewer.thread_id") == t-one ]] || \
    note_failure 'first repo state was not isolated'
  [[ $(< "$FABLE_CODEX_HOME/state/$slug_two/slug-test/reviewer.thread_id") == t-two ]] || \
    note_failure 'second repo state was not isolated'
}

scenario_denylist_canonicalization() {
  local test_home=$tmp_root/test-home
  local home_repo=$test_home/real-repo
  local start_status preflight_status
  mkdir -p "$home_repo" "$FABLE_CODEX_HOME"
  git -C "$home_repo" init -q
  ln -s "$home_repo" "$test_home/repo-alias"
  printf '%s\n' '~/repo-alias' > "$FABLE_CODEX_HOME/denylist"
  set +e
  (cd "$home_repo" && printf '%s' 'Blocked alias.' | HOME=$test_home \
    "$THREAD_SCRIPT" reviewer start denied-alias) \
    > "$tmp_root/denied-alias.out" 2> "$tmp_root/denied-alias.err"
  start_status=$?
  (cd "$home_repo" && HOME=$test_home "$PREFLIGHT_SCRIPT") \
    > "$tmp_root/deny-alias-preflight.out" 2> "$tmp_root/deny-alias-preflight.err"
  preflight_status=$?
  set -e
  rm -f -- "$FABLE_CODEX_HOME/denylist"
  [[ $start_status -eq 6 ]] || note_failure "canonicalized start expected exit 6, got $start_status"
  [[ $preflight_status -eq 6 ]] || note_failure "canonicalized preflight expected exit 6, got $preflight_status"
}

scenario_missing_jq_before_invocation() {
  local minimal_bin=$tmp_root/no-jq-bin
  local tool status
  mkdir -p "$minimal_bin"
  for tool in bash cat git grep shasum; do
    ln -s "$(command -v "$tool")" "$minimal_bin/$tool"
  done
  : > "$STUB_LOG"
  set +e
  (cd "$repo" && printf '%s' 'No jq.' | PATH=$minimal_bin \
    "$THREAD_SCRIPT" reviewer start missing-jq) \
    > "$tmp_root/missing-jq.out" 2> "$tmp_root/missing-jq.err"
  status=$?
  set -e
  [[ $status -eq 3 ]] || note_failure "missing jq expected exit 3, got $status"
  [[ ! -s "$STUB_LOG" ]] || note_failure 'missing jq invoked codex'
  grep -Fq 'jq is not installed' "$tmp_root/missing-jq.err" || \
    note_failure 'missing jq message was not human-readable'
}

run_scenario 'start reviewer happy path' scenario_start_reviewer
run_scenario 'resume reviewer pins sandbox without -s' scenario_resume_reviewer
run_scenario 'start implementer defaults' scenario_start_implementer
run_scenario 'model and effort overrides' scenario_overrides
run_scenario 'fresh reviewer preserves primary thread' scenario_fresh_reviewer
run_scenario 'codex non-zero preserves prior state' scenario_nonzero_preserves_state
run_scenario 'missing thread.started is parse error' scenario_missing_thread_event
run_scenario 'reset isolation and show read-only behavior' scenario_reset_and_show
run_scenario 'secret scrub aborts before invocation' scenario_scrub_gate
run_scenario 'denylist blocks start and preflight' scenario_denylist
run_scenario 'implementer network policy' scenario_network_policy
run_scenario 'state permissions are private' scenario_state_hygiene
run_scenario 'verdict extraction outcomes' scenario_extract_verdict
run_scenario 'preflight reports missing codex' scenario_preflight_missing_codex
run_scenario 'verdict must be the final non-blank line' scenario_verdict_must_be_final
run_scenario 'unquoted credential assignments are scrubbed' scenario_unquoted_credential_scrub
run_scenario 'repo slug resists old path collisions' scenario_collision_proof_repo_slug
run_scenario 'denylist canonicalizes home and symlink paths' scenario_denylist_canonicalization
run_scenario 'missing jq aborts before codex invocation' scenario_missing_jq_before_invocation

printf 'SUMMARY: %d/%d scenarios PASS' "$passed" "$total"
if [[ $failed -gt 0 ]]; then
  printf ' (%d failed)\n' "$failed"
  exit 1
fi
printf '\n'
