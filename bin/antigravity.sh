#!/usr/bin/env bash
# Connects the workspace to Antigravity: skills, mode global rules, and local
# files for each folder with rules. With `update`, fetches the latest 2.0 application
# version into `~/opt/antigravity/`.
#
# Full details: docs/reference/antigravity.md. Paths come from tests on
# 1 October 2026: Antigravity reads skills only from `~/.gemini/config/skills/`
# and follows symlinks; it does not climb above the opened folder, so parent
# rules are provided by `.agents/rules/framework-NN.md` files using `@[label](path)`,
# one per include, because the 24,000-byte limit is calculated after inclusion.
#
# With ANTIGRAVITY_FUNCTIONS_ONLY=1 it lets itself be loaded via `source` for testing.

link() {  # source destination
  # A REAL folder with the skill's name belongs to the user: `ln -sfn` would put the link
  # inside it, and the old skill would stay active without a word.
  if [ -e "$2" ] && [ ! -L "$2" ]; then
    echo "antigravity: $2 is a real folder; refusing to link over it" >&2
    return 1
  fi
  ln -sfn "$1" "$2"
}

include() {  # label target rule-dir — a line of `@[…](…)`, with a relative path
  printf '@[%s](%s)\n' "$1" "$(realpath -m --relative-to="$3" "$2")"
}

rules_from() {  # dir — the rules file Antigravity does not find on its own
  # A project not yet moved to the pair has its full rules in CLAUDE.md, which
  # Antigravity does not read; after moving, CLAUDE.md is only the Claude Code module.
  if [ -f "$1/AGENTS.md" ]; then echo "$1/AGENTS.md"
  elif [ -f "$1/CLAUDE.md" ]; then echo "$1/CLAUDE.md"; fi
}

local_file() {  # dir workspace-root
  local f="$1" r="$2" d="$1/.agents/rules" up t n=0 git_dir prefix
  local parents=() included=()
  if [ "$f" != "$r" ]; then
    # Parents, from the root down, excluding the directory itself.
    up="$(dirname "$f")"
    while :; do
      t="$(rules_from "$up")"; [ -n "$t" ] && parents=("$t" "${parents[@]}")
      # `/` stops climbing even for a folder outside the workspace, which otherwise
      # would never reach the root.
      [ "$up" = "$r" ] || [ "$up" = / ] || [ "$up" = . ] && break
      up="$(dirname "$up")"
    done
    included+=("${parents[@]}")
    [ -f "$r/GEMINI.md" ] && included+=("$r/GEMINI.md")
  fi
  # Its own AGENTS.md is read on its own; its own CLAUDE.md, without AGENTS.md, is not.
  [ -f "$f/AGENTS.md" ] || { t="$(rules_from "$f")"; [ -n "$t" ] && included+=("$t"); }
  [ -f "$r/records/house-rules.md" ] && included+=("$r/records/house-rules.md")
  [ -f "$r/records/memory/MEMORY.md" ] && included+=("$r/records/memory/MEMORY.md")
  # One file per include: Antigravity calculates the 24,000-byte limit after
  # inclusion, and the root AGENTS.md alone nearly fills it. The numbers keep
  # the order: parents from top to bottom, the module, house rules, memory.
  mkdir -p "$d"; rm -f "$d"/framework-[0-9][0-9].md
  local large=0 f_new
  for t in "${included[@]}"; do
    n=$((n + 1)); f_new="$d/framework-$(printf '%02d' "$n").md"
    printf -- '---\ntrigger: always_on\n---\n\n<!-- Written by bin/antigravity.sh; do not edit and do not track in git. -->\n\n%s\n' \
      "$(include "${t#"$r"}" "$t" "$d")" > "$f_new"
    # Antigravity measures the file after inclusion: header plus target.
    if [ $(( $(stat -c %s "$f_new") + $(stat -c %s "$t") )) -ge 24000 ]; then
      echo "antigravity: $t, included in $f_new, exceeds 24,000 bytes; Antigravity would truncate it" >&2
      large=1
    fi
  done
  # Kept out of git without touching the repository: its info/exclude, not .gitignore.
  git_dir="$(cd "$f" && cd "$(git rev-parse --git-common-dir 2>/dev/null || echo /not-a-repo)" 2>/dev/null && pwd)" || return "$large"
  prefix="$(git -C "$f" rev-parse --show-prefix)"
  mkdir -p "$git_dir/info"
  grep -qxF "/${prefix}.agents/rules/framework-[0-9][0-9].md" "$git_dir/info/exclude" 2>/dev/null \
    || printf '/%s.agents/rules/framework-[0-9][0-9].md\n' "$prefix" >> "$git_dir/info/exclude"
  return "$large"
}

global_rule() {  # name content
  printf -- '---\ntrigger: always_on\n---\n\n<!-- Written by bin/antigravity.sh. -->\n\n%s\n' "$2" \
    > "$HOME/.gemini/config/rules/$1.md"
}

version_from_url() {  # archive-url
  local v="${1#*antigravity-hub/}"
  printf '%s\n' "${v%%-*}"
}

update() {
  local opt="$HOME/opt/antigravity" page url ver current arch
  case "$(uname -m)" in
    x86_64) arch=linux-x64 ;; aarch64|arm64) arch=linux-arm ;;
    *) echo "antigravity: unknown architecture, $(uname -m)" >&2; return 1 ;;
  esac
  if pgrep -f "$opt/antigravity" >/dev/null; then
    echo "antigravity: application is running; close it first" >&2; return 1
  fi
  # ponytail: the URL is read from the download page's HTML; if Google changes
  #           the page, the command fails with a message. Switch to apt once 2.x arrives there.
  page="$(curl -fsSL --compressed https://antigravity.google/download/)" || return 1
  # `|| true`: under `pipefail`, a `grep` without a match would exit the script before
  # the message below — that is, in the exact case the message explains.
  url="$(printf '%s' "$page" | grep -o "https://storage.googleapis.com/antigravity-public/antigravity-hub/[^\"' ]*/$arch/Antigravity.tar.gz" | head -1 || true)"
  [ -n "$url" ] || { echo "antigravity: archive URL is no longer on the page" >&2; return 1; }
  ver="$(version_from_url "$url")"
  current="$(cat "$opt/.version" 2>/dev/null || echo 0)"
  if [ "$ver" = "$current" ]; then echo "Antigravity $current is up to date"; return 0; fi
  if [ "$(printf '%s\n%s\n' "$ver" "$current" | sort -V | tail -1)" != "$ver" ]; then
    echo "antigravity: page has $ver, which is older than $current; not downgrading" >&2; return 1
  fi
  echo "Antigravity: $current -> $ver"
  rm -rf "$opt.new" && mkdir -p "$opt.new" || return 1
  curl -fL --progress-bar "$url" | tar xz -C "$opt.new" --strip-components=1 || { rm -rf "$opt.new"; return 1; }
  # The new archive is verified before replacing the old one: a different layout,
  # stripped with `--strip-components=1`, would otherwise leave an app without a binary.
  [ -x "$opt.new/antigravity" ] || { rm -rf "$opt.new"; echo "antigravity: new archive missing binary in expected location" >&2; return 1; }
  printf '%s\n' "$ver" > "$opt.new/.version"
  rm -rf "$opt.old"; [ -d "$opt" ] && mv "$opt" "$opt.old"
  mv "$opt.new" "$opt" || { mv "$opt.old" "$opt"; return 1; }
  rm -rf "$opt.old"
}

if [ "${ANTIGRAVITY_FUNCTIONS_ONLY:-}" = 1 ]; then
  return 0 2>/dev/null || exit 0
fi

set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"

if [ "${1:-}" = update ]; then update; exit; fi

cache="$HOME/.claude/plugins/cache"
mkdir -p "$HOME/.gemini/config/skills" "$HOME/.gemini/config/rules"
missing=0

# ── skills: house skills, then pinned plugins ─────────────────────
for s in "$repo"/skills/*/; do
  link "${s%/}" "$HOME/.gemini/config/skills/$(basename "$s")" || missing=1
done
while IFS=$'\t' read -r name market version; do
  if [ ! -d "$cache/$market/$name/$version" ]; then
    echo "antigravity: clone of $name is missing; restore-env will fetch it" >&2; missing=1; continue
  fi
  for s in "$cache/$market/$name/$version"/skills/*/; do
    [ -f "$s/SKILL.md" ] || continue
    link "${s%/}" "$HOME/.gemini/config/skills/$(basename "$s")" || missing=1
  done
done < <(python3 -c 'import json,sys; [print(p["name"], p["marketplace"], p["version"], sep="\t") for p in json.load(open(sys.argv[1]))["plugins"]]' "$repo/plugins.lock.json")
echo "skills linked in ~/.gemini/config/skills/: $(ls "$HOME/.gemini/config/skills" | wc -l)"

# ── global rules: superpowers startup, modes, rtk ────────────────
plugin() {  # name — pinned clone folder, relative to cache; 1 if it left the lockfile
  python3 -c 'import json,sys; p=[p for p in json.load(open(sys.argv[1]))["plugins"] if p["name"]==sys.argv[2]]; p or sys.exit(1); print(p[0]["marketplace"], p[0]["name"], p[0]["version"], sep="/")' \
    "$repo/plugins.lock.json" "$1"
}
rules="$HOME/.gemini/config/rules"
exists() {  # file... — a rule that includes a missing file would produce nothing, silently
  local f; for f in "$@"; do [ -f "$f" ] || { echo "antigravity: missing $f" >&2; missing=1; return 1; }; done
}
# A plugin removed from the lockfile, as README.md allows, loses its global rule too;
# the others are still written.
sp='' cv='' pt=''
p="$(plugin superpowers)" && sp="$cache/$p/skills/using-superpowers" || rm -f "$rules/superpowers.md"
p="$(plugin caveman)" && cv="$cache/$p/skills/caveman/SKILL.md" || rm -f "$rules/caveman.md"
p="$(plugin ponytail)" && pt="$cache/$p/skills/ponytail/SKILL.md" || rm -f "$rules/ponytail.md"
if [ -n "$sp" ] && exists "$sp/SKILL.md" "$sp/references/antigravity-tools.md"; then
  global_rule superpowers "$(include "superpowers: using-superpowers" "$sp/SKILL.md" "$rules")
$(include "superpowers: tool map for Antigravity" "$sp/references/antigravity-tools.md" "$rules")"
fi
if [ -n "$cv" ] && exists "$cv"; then
  global_rule caveman "The default level is \`full\`.

$(include "caveman" "$cv" "$rules")"
fi
if [ -n "$pt" ] && exists "$pt"; then
  global_rule ponytail "The default level is \`full\`.

$(include "ponytail" "$pt" "$rules")"
fi
if command -v rtk >/dev/null; then
  global_rule rtk "Development commands — git, grep, ls, find, tests, build — are written with \`rtk\` in front, for example \`rtk git status\`: rtk shortens output before it reaches the conversation. \`rtk proxy <command>\` gives the full output."
fi
echo "global rules: $(ls "$rules" | tr '\n' ' ')"

# ── local files: root, each repository and each folder with rules ──
# A repository without AGENTS.md also receives local files: otherwise, opened
# there, Antigravity would see neither framework rules, nor house rules, nor memory.
local_file "$repo" "$repo" || missing=1
# `-printf '%h'` gives the full path including spaces; `xargs` would have split it.
while IFS= read -r d; do
  local_file "$d" "$repo" || missing=1
done < <(find "$repo/projects" \( -name node_modules -o -name .venv -o -name records \
           -o -name .claude -o -name template \) -prune \
           -o \( -name .git -printf '%h\n' -prune \) -o \( -name AGENTS.md -o -name CLAUDE.md \) -printf '%h\n' 2>/dev/null \
         | sort -u)
echo "folders with local files: $(find "$repo" -path '*/.agents/rules/framework-01.md' -not -path '*/.git/*' 2>/dev/null | wc -l)"

[ "$missing" -eq 0 ] || { echo "antigravity linking was incomplete" >&2; exit 1; }
