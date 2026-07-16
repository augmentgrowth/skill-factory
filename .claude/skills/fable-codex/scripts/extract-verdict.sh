#!/usr/bin/env bash
set -euo pipefail

# Shared exit codes: 0 success; 2 usage; 3 codex/jq missing; 4 unauthenticated;
# 5 model probe failed; 6 repo denylisted; 7 secret detected; 8 output parse;
# 9 no verdict (extract-verdict.sh only); 10 codex invocation failed.

usage() {
  printf '%s\n' 'Usage: extract-verdict.sh [file]' >&2
  exit 2
}

[[ $# -le 1 ]] || usage

tmp_file=
input_file=${1:-}
if [[ -z "$input_file" ]]; then
  tmp_file=$(mktemp "${TMPDIR:-/tmp}/fable-verdict.XXXXXX")
  trap 'rm -f -- "$tmp_file"' EXIT
  cat > "$tmp_file"
  input_file=$tmp_file
elif [[ ! -f "$input_file" ]]; then
  printf 'Input file not found: %s\n' "$input_file" >&2
  exit 2
fi

record=$(awk '
  NF { last_nonblank = NR }
  /^VERDICT:[[:space:]]*APPROVED[[:space:]]*$/ { line = NR; tag = "APPROVED" }
  /^VERDICT:[[:space:]]*REVISE[[:space:]]*$/ { line = NR; tag = "REVISE" }
  /^VERDICT:[[:space:]]*CHANGES_REQUIRED[[:space:]]*$/ { line = NR; tag = "CHANGES_REQUIRED" }
  END { if (line && line == last_nonblank) printf "%d\t%s\n", line, tag }
' "$input_file")

if [[ -z "$record" ]]; then
  printf '%s\n' 'NO_VERDICT'
  printf '%s\n' 'Hint: add a trailing VERDICT: APPROVED, REVISE, or CHANGES_REQUIRED line.' >&2
  exit 9
fi

verdict_line=${record%%$'\t'*}
verdict_tag=${record#*$'\t'}
printf 'VERDICT: %s\n' "$verdict_tag"

section_line=$(awk -v last="$verdict_line" '
  NR > last { exit }
  /^(BLOCKERS|FINDINGS):/ { section = NR }
  END { if (section) print section }
' "$input_file")

if [[ -n "$section_line" ]]; then
  sed -n "${section_line},${verdict_line}p" "$input_file"
fi
