#!/usr/bin/env bash
# Runs the verification commands from every IMPACT.md under the root.
#
# The format is the table in template/IMPACT.md: the fourth column is a command that
# must exit with 0 if the row is still true. The command runs with the folder of the
# IMPACT.md file as the current directory, so the paths in it are relative to the
# project.
#
# A command that exits with 77 is SKIPPED, not failed, by the same convention as the
# `test` collector: a check that cannot run on this machine says so and does not keep
# the map red.
#
# A literal `|` in a command is written `\|`, as the markdown table requires anyway.
#
# The commands come from files of the repository, written by us; `eval` is appropriate
# here and would not be if the source came from outside.
set -uo pipefail

root="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
ran=0
failed=0
skipped=0

while IFS= read -r map; do
  n=0
  while IFS= read -r line; do
    n=$((n + 1))
    case "$line" in '|'*) ;; *) continue ;; esac
    case "$line" in *---*) continue ;; esac
    # `\|` is a literal | inside a cell. It is hidden BEFORE splitting:
    # `awk -F'|'` cuts at the escaped one too, and then the fifth column is no longer
    # the command, but a piece from the middle of an earlier cell. Unescaping after
    # the extraction does not help — the wrong column has already been chosen.
    cmd="$(printf '%s\n' "$line" | sed 's/\\|/\x01/g' | awk -F'|' '{print $5}' \
           | sed 's/\x01/|/g; s/^[[:space:]]*//; s/[[:space:]]*$//; s/^`//; s/`$//')"
    [ -z "$cmd" ] && continue
    # The table header is not a command.
    case "$cmd" in verification) continue;; esac
    ran=$((ran + 1))
    ( cd "$(dirname "$map")" && eval "$cmd" ) >/dev/null 2>&1; code=$?
    case "$code" in
      0) ;;
      77) printf 'SKIPPED %s:%s\n        %s\n' "$map" "$n" "$cmd"
          skipped=$((skipped + 1)) ;;
      *)  printf 'FAILED  %s:%s\n        %s\n' "$map" "$n" "$cmd"
          failed=$((failed + 1)) ;;
    esac
  done < "$map"
done < <(find "$root" -maxdepth 4 -name IMPACT.md -not -path '*/.git/*' 2>/dev/null | sort)

printf 'commands run: %s, failed: %s, skipped: %s\n' "$ran" "$failed" "$skipped"
[ "$failed" -eq 0 ]
