#!/usr/bin/env bash
# Verifies, without the network, that every SHA in plugins.lock.json really exists in
# the repository the lock names. installed_plugins.json does not say which repository
# that is: superpowers and rtk-plugin have their own repository, ponytail and caveman
# are the marketplace's repository itself.
set -uo pipefail

repo="$(cd "$(dirname "$0")/.." && pwd)"
lock="$repo/plugins.lock.json"
pl="$HOME/.claude/plugins"
fail=0

[ -f "$lock" ] || { echo "missing $lock"; exit 1; }

while IFS=$'\t' read -r market plugin version sha url; do
  if [ -d "$pl/cache/$market/$plugin/$version/.git" ]; then
    d="$pl/cache/$market/$plugin/$version"
  else
    d="$pl/marketplaces/$market"
  fi
  if git -C "$d" cat-file -e "${sha}^{commit}" 2>/dev/null; then
    printf 'ok       %-14s %s\n' "$plugin" "${sha:0:12}"
  else
    printf 'MISSING  %-14s %s  not in %s (%s)\n' "$plugin" "${sha:0:12}" "$d" "$url"
    fail=$((fail + 1))
  fi
done < <(python3 -c '
import json, sys
d = json.load(open(sys.argv[1]))
for p in d["plugins"]:
    print("\t".join([p["marketplace"], p["name"], p["version"], p["sha"], p["url"]]))
' "$lock")

[ "$fail" -eq 0 ] || { echo "SHAs not found: $fail"; exit 1; }
echo "all the SHAs are present"
