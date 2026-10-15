#!/usr/bin/env bash
# Test for `bin/check-maps.sh`: a row that exits with 77 is skipped, not failed, by
# the same convention as the `test` collector. Without it, a check that cannot run on
# this machine keeps the map red forever.
set -u

R="${TESTS_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT

failed=0
check() {  # condition message
  if eval "$1"; then printf '  ✓ %s\n' "$2"; else failed=$((failed + 1)); printf '  ✗ %s\n' "$2"; fi
}

map() {  # folder, then the commands, one per row
  local d="$1"; shift
  mkdir -p "$d"
  { printf '| what | what | what | verification |\n|---|---|---|---|\n'
    for c in "$@"; do printf '| a | b | c | `%s` |\n' "$c"; done; } > "$d/IMPACT.md"
}

map "$T/mixed" true 'exit 77' false
out="$("$R/bin/check-maps.sh" "$T/mixed" 2>&1)"; code=$?
check '[ "$code" -eq 1 ]' "with a failed row it exits with 1 (it exited with $code)"
check 'printf "%s" "$out" | grep -q "commands run: 3, failed: 1, skipped: 1"' \
  "the skipped row is counted separately: $(printf '%s' "$out" | tail -1)"
check '[ "$(printf "%s\n" "$out" | grep -c "^FAILED")" -eq 1 ]' "exactly one row is FAILED"
check '[ "$(printf "%s\n" "$out" | grep -c "^SKIPPED")" -eq 1 ]' "the row with 77 is written SKIPPED, with its command"

map "$T/clean" true 'exit 77'
out="$("$R/bin/check-maps.sh" "$T/clean" 2>&1)"; code=$?
check '[ "$code" -eq 0 ]' "without failed rows it exits with 0, even with a skipped one (it exited with $code)"

echo
if [ "$failed" -eq 0 ]; then echo "  ✓ all tests pass"; else echo "  ✗ $failed tests failed"; exit 1; fi
