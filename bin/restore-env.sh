#!/usr/bin/env bash
# Restores the Claude environment on a new machine, from plugins.lock.json.
#
# It bypasses `claude plugin install`, which does not accept a pinned version
# (verified: the options are only --config, --scope, --yes). It clones directly at the
# SHA and places the result where Claude Code looks for it.
#
# It clones over HTTPS, not SSH. The remotes configured locally are
# git@github.com: — on a machine without a key in the agent, those fail with an
# authentication error that looks nothing like the real cause.
#
# With RESTORE_ENV_FUNCTIONS_ONLY=1 the script lets itself be loaded with `source` and
# stops after the functions: that is how `tests/test-restore-links.sh` exercises them,
# in a fabricated HOME, without restoring anything.

link_skill() {  # source destination
  local source="$1" dest="$2" name
  name="$(basename "$source")"
  # A REAL folder with the skill's name belongs to the human. `ln -sfn` does not replace
  # it: it puts the link inside it, and the old skill stays active, without a word.
  if [ -e "$dest" ] && [ ! -L "$dest" ]; then
    echo "skill   $name: $dest is a real folder, not a link; nothing is linked over it" >&2
    return 1
  fi
  ln -sfn "$source" "$dest"
  echo "skill   $name linked"
}

# The agent's memory is per starting folder: `~/.claude/projects/<the path with - for
# />/memory`. A session opened in a project's folder would get a different memory than
# one opened at the root, so all of them are linked from the same `records/memory`.
# Nothing is deleted: a real memory in place of the link is someone else's memory, or
# another workspace's. What was found is said and it moves on.
link_memory() {  # starting-folder memory-source
  local mem
  mem="$HOME/.claude/projects/$(printf '%s' "$1" | tr '/' '-')/memory"
  [ -L "$mem" ] && return 0
  if [ -d "$mem" ] && [ -n "$(ls -A "$mem" 2>/dev/null)" ]; then
    echo "memory   $mem has files; nothing is linked over them" >&2
    return 1
  fi
  # `rmdir` on a folder that does not exist exits with 1, and `set -e` would stop the
  # script without a word: exactly the case of a fresh HOME, where the folder is missing.
  mkdir -p "$(dirname "$mem")"; rmdir "$mem" 2>/dev/null || true
  ln -s "$2" "$mem"
  echo "memory   $(basename "$1") linked from records/memory"
}

# The house rules are linked as a user rule, `~/.claude/rules/`, which loads in
# every session. The old import in `CLAUDE.local.md` did not expand in a session
# opened in a project, because it climbed out of its folder: the house rules never
# reached there, measured on 1 October 2026 in the session logs.
link_house_rules() {  # root
  local dest="$HOME/.claude/rules/house-rules.md"
  mkdir -p "$HOME/.claude/rules"
  if [ -e "$dest" ] && [ ! -L "$dest" ]; then
    echo "rules    $dest is a real file; nothing is linked over it" >&2
    return 1
  fi
  # Without the link, the old import stays: otherwise the house rules would reach nowhere.
  ln -sfn "$1/records/house-rules.md" "$dest" || return 1
  # The old import would bring in the rules a second time in root sessions; it leaves
  # only if it is the exact line written by restore, not something else put by the human.
  if [ "$(cat "$1/CLAUDE.local.md" 2>/dev/null)" = "@records/house-rules.md" ]; then
    rm -f "$1/CLAUDE.local.md"
  fi
  echo "rules    house rules linked in ~/.claude/rules/"
}

# Antigravity is installed: `agy`, the application folder or the binary in `~/opt`.
# `~/.gemini/` alone is not enough: the Gemini CLI also creates it, without Antigravity.
has_antigravity() {
  command -v agy >/dev/null 2>&1 || [ -d "$HOME/.gemini/antigravity" ] || [ -x "$HOME/opt/antigravity/antigravity" ]
}

# Without Claude Code, no one can confirm its plugins. On a machine with Antigravity
# only, that is not a failure: the rest of the restore is done and Antigravity is linked.
finish_without_claude() {
  if has_antigravity; then
    echo "Claude Code is not installed: its plugins are not confirmed; Antigravity is linked"
    return 0
  fi
  echo "the claude binary was not found" >&2
  return 1
}

if [ "${RESTORE_ENV_FUNCTIONS_ONLY:-}" = 1 ]; then
  return 0 2>/dev/null || exit 0
fi

set -euo pipefail

repo="$(cd "$(dirname "$0")/.." && pwd)"
lock="$repo/plugins.lock.json"
pl="$HOME/.claude/plugins"

command -v node >/dev/null 2>&1 || {
  echo "node is missing. ponytail, caveman and rtk-plugin are inert without it." >&2
  exit 1
}
echo "node $(node --version)"

mkdir -p "$pl/cache" "$pl/marketplaces" "$HOME/.claude/skills"

tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
python3 - "$lock" "$tmp" <<'PY'
import json, pathlib, sys
d = json.load(open(sys.argv[1])); t = pathlib.Path(sys.argv[2])
(t / "markets.tsv").write_text("".join(
    "\t".join([m["name"], m["url"], m["sha"]]) + "\n" for m in d["marketplaces"]))
(t / "plugins.tsv").write_text("".join(
    "\t".join([p["name"], p["marketplace"], p["version"], p["sha"], p["url"]]) + "\n"
    for p in d["plugins"]))
PY

clone_at() {  # url sha destination
  local url="$1" sha="$2" dest="$3"
  [ -d "$dest/.git" ] || git clone --quiet "$url" "$dest"
  git -C "$dest" fetch --quiet origin
  git -C "$dest" checkout --quiet --detach "$sha"
}

while IFS=$'\t' read -r name url sha; do
  clone_at "$url" "$sha" "$pl/marketplaces/$name"
  echo "market  $name @ ${sha:0:12}"
done < "$tmp/markets.tsv"

while IFS=$'\t' read -r name market version sha url; do
  clone_at "$url" "$sha" "$pl/cache/$market/$name/$version"
  echo "plugin  $name @ ${sha:0:12}"
done < "$tmp/plugins.tsv"

python3 "$repo/bin/merge-claude-config.py" "$lock" "$HOME"

missing=0
for s in documentation end-of-session execute local-workers; do
  link_skill "$repo/skills/$s" "$HOME/.claude/skills/$s" || missing=1
done

# Only when it is missing: an existing `records/` is the clone of someone's
# repository and is never touched. The indexes copied from the template talk about
# "the project"; they stay so until the human rewrites them, because an empty skeleton
# is a starting point, not a statement.
if [ ! -e "$repo/records" ]; then
  cp -r "$repo/template/records" "$repo/records"
  mkdir -p "$repo/records/memory"
  : > "$repo/records/local-workers.md"
  echo "records  empty skeleton created"
fi

if [ -f "$repo/records/house-rules.md" ]; then
  link_house_rules "$repo" || missing=1
fi

if [ -d "$repo/records/memory" ]; then
  link_memory "$repo" "$repo/records/memory" || true
  for p in "$repo"/projects/*/; do
    [ -d "$p" ] && { link_memory "${p%/}" "$repo/records/memory" || true; }
  done
fi

# Antigravity, only where it is installed: its module has its own script, which can
# also be run on its own, after a project is born.
if has_antigravity; then
  "$repo/bin/antigravity.sh" || missing=1
fi

# The binary lookup swallows its exit code. `find` exits with 1 when the folder does
# not exist, `pipefail` carries the code through `| head`, and `set -e` would stop the
# script right in the chain of fallbacks — that is, exactly when the first fallback is
# missing, the normal case in a fresh HOME. Without `|| true`, the third fallback, the
# only one that finds the binary in a test HOME, is never executed.
#
# ponytail: the highest version is taken. When several variants are installed
#           (claude-code, claude-code-vm), any of them lists the plugins correctly —
#           verified on 2.1.229 and 2.1.247. It only matters that the choice does not
#           depend on the order in which `find` returns the folders.
claude_bin="$(command -v claude || true)"
if [ -z "$claude_bin" ]; then
  for base in "$HOME/.config/Claude" \
              "$HOME/Library/Application Support/Claude" \
              "$(getent passwd "$(id -un)" | cut -d: -f6)/.config/Claude"; do
    claude_bin="$(find "$base" -name claude -type f 2>/dev/null | sort -V | tail -1 || true)"
    if [ -n "$claude_bin" ]; then break; fi
  done
fi
if [ -z "$claude_bin" ]; then
  finish_without_claude || exit 1
  [ "$missing" -eq 0 ] || { echo "the restore was not confirmed" >&2; exit 1; }
  exit 0
fi

# `plugin list` does not read known_marketplaces.json, so it passes even when Claude
# Code rejects the file as "corrupted". `plugin details` reads it. The reason is taken
# from the output without `| head`, for the same reason as in the binary lookup above.
# `</dev/null` keeps the binary away from the list the loop is reading.
listing="$("$claude_bin" plugin list 2>&1)"
while IFS=$'\t' read -r name market version _ _; do
  printf '%s' "$listing" | grep -q "$name@$market" || { echo "missing from the list: $name@$market" >&2; missing=1; }
  details="$("$claude_bin" plugin details "$name@$market" </dev/null 2>&1)" \
    || { echo "does not load: $name@$market: ${details%%$'\n'*}" >&2; missing=1; }
done < "$tmp/plugins.tsv"
[ "$missing" -eq 0 ] || { echo "the restore was not confirmed" >&2; exit 1; }
echo "all four plugins respond"
