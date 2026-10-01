#!/usr/bin/env bash
# Test for the links that `bin/restore-env.sh` makes: the skills in
# `~/.claude/skills/` and the memory in `~/.claude/projects/<folder>/memory`.
#
# The script is loaded only for its functions, with RESTORE_ENV_FUNCTIONS_ONLY=1, in a
# fabricated HOME: nothing here touches the machine.
set -u

R="${TESTS_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
export HOME="$T/home"
mkdir -p "$HOME/.claude/skills" "$T/space/skills/documentation" "$T/space/records/memory" \
         "$T/space/projects/game"
touch "$T/space/skills/documentation/SKILL.md" "$T/space/records/memory/MEMORY.md"

failed=0
check() {  # condition message
  if eval "$1"; then printf '  ✓ %s\n' "$2"; else failed=$((failed + 1)); printf '  ✗ %s\n' "$2"; fi
}

# shellcheck disable=SC1090
RESTORE_ENV_FUNCTIONS_ONLY=1 source "$R/bin/restore-env.sh"
check 'declare -F link_skill >/dev/null && declare -F link_memory >/dev/null && declare -F link_house_rules >/dev/null' \
  "the script lets itself be loaded for its functions only, without restoring anything"

# ── the skills ───────────────────────────────────────────────────
link_skill "$T/space/skills/documentation" "$HOME/.claude/skills/documentation" >/dev/null
check '[ "$(readlink "$HOME/.claude/skills/documentation")" = "$T/space/skills/documentation" ]' \
  "a missing link is created"

ln -sfn "$T/elsewhere" "$HOME/.claude/skills/documentation"
link_skill "$T/space/skills/documentation" "$HOME/.claude/skills/documentation" >/dev/null
check '[ "$(readlink "$HOME/.claude/skills/documentation")" = "$T/space/skills/documentation" ]' \
  "an old link is replaced"

# ⚠ A REAL folder with the skill's name belongs to the human. `ln -sfn` does not
#   replace it: it puts the link inside it, and the old skill stays active, silently.
rm "$HOME/.claude/skills/documentation"
mkdir -p "$HOME/.claude/skills/documentation"; touch "$HOME/.claude/skills/documentation/SKILL.md"
if link_skill "$T/space/skills/documentation" "$HOME/.claude/skills/documentation" 2>"$T/err" >/dev/null; then code=0; else code=$?; fi
check '[ "$code" -ne 0 ]' "a real folder in place of the link is refused, not overwritten (code $code)"
check '[ ! -e "$HOME/.claude/skills/documentation/documentation" ]' \
  "the link is not put inside the real folder"
check '[ -f "$HOME/.claude/skills/documentation/SKILL.md" ]' "the real folder stays untouched"
check 'grep -q "documentation" "$T/err"' "the refusal is said on stderr, with the skill's name"

# ── the house rules ──────────────────────────────────────────────
printf '# House\n' > "$T/space/records/house-rules.md"
printf '@records/house-rules.md\n' > "$T/space/CLAUDE.local.md"
link_house_rules "$T/space" >/dev/null
check '[ "$(readlink "$HOME/.claude/rules/house-rules.md")" = "$T/space/records/house-rules.md" ]' \
  "the house rules are linked as a user rule, loaded in every session"
check '[ ! -e "$T/space/CLAUDE.local.md" ]' "the old import, written by restore, goes away"
printf 'something else put by the human\n' > "$T/space/CLAUDE.local.md"
link_house_rules "$T/space" >/dev/null
check '[ -f "$T/space/CLAUDE.local.md" ]' "a CLAUDE.local.md with something else in it stays"
rm "$HOME/.claude/rules/house-rules.md"
printf '@records/house-rules.md\n' > "$T/space/CLAUDE.local.md"; chmod 555 "$HOME/.claude/rules"
if link_house_rules "$T/space" 2>/dev/null >/dev/null; then code=0; else code=$?; fi
chmod 755 "$HOME/.claude/rules"
check '[ "$code" -ne 0 ] && [ -f "$T/space/CLAUDE.local.md" ]' \
  "a link that cannot be made leaves the old import, so the house rules reach somewhere"
printf 'belongs to the human\n' > "$HOME/.claude/rules/house-rules.md"
if link_house_rules "$T/space" 2>/dev/null >/dev/null; then code=0; else code=$?; fi
check '[ "$code" -ne 0 ] && grep -qx "belongs to the human" "$HOME/.claude/rules/house-rules.md"' \
  "a real file in place of the link is refused, not overwritten"

# ── the memory ───────────────────────────────────────────────────
mem_root="$HOME/.claude/projects/$(printf '%s' "$T/space" | tr '/' '-')/memory"
mem_game="$HOME/.claude/projects/$(printf '%s' "$T/space/projects/game" | tr '/' '-')/memory"

link_memory "$T/space" "$T/space/records/memory" >/dev/null
check '[ "$(readlink "$mem_root")" = "$T/space/records/memory" ]' \
  "the root's memory is linked from records/memory, in a fresh HOME"

link_memory "$T/space/projects/game" "$T/space/records/memory" >/dev/null
check '[ "$(readlink "$mem_game")" = "$T/space/records/memory" ]' \
  "a project's memory is linked from the same records/memory"

link_memory "$T/space/projects/game" "$T/space/records/memory" >/dev/null
check '[ "$(readlink "$mem_game")" = "$T/space/records/memory" ]' "an existing link stays as it is"

mkdir -p "$T/space/projects/old"
mem_old="$HOME/.claude/projects/$(printf '%s' "$T/space/projects/old" | tr '/' '-')/memory"
mkdir -p "$mem_old"; echo "someone else's" > "$mem_old/MEMORY.md"
link_memory "$T/space/projects/old" "$T/space/records/memory" 2>"$T/err" >/dev/null || true
check '[ ! -L "$mem_old" ] && [ "$(cat "$mem_old/MEMORY.md")" = "someone else'"'"'s" ]' \
  "a real memory, with files, is not covered by the link"
check 'grep -q "files" "$T/err"' "and it is said on stderr"

# ── a machine with Antigravity only ──────────────────────────────
# Without Claude Code, restore has no one to confirm its plugins. With Antigravity
# linked, that is not a failure; with neither tool, it is.
mkdir -p "$HOME/.gemini/antigravity"
if PATH=/usr/bin:/bin finish_without_claude >"$T/out" 2>"$T/err"; then code=0; else code=$?; fi
check '[ "$code" -eq 0 ] && grep -q "Antigravity" "$T/out"' "without Claude Code but with Antigravity, restore ends with 0"
rm -rf "$HOME/.gemini/antigravity"
if PATH=/usr/bin:/bin finish_without_claude >"$T/out" 2>"$T/err"; then code=0; else code=$?; fi
check '[ "$code" -ne 0 ] && grep -q "the claude binary was not found" "$T/err"' "with neither tool, restore fails and says why"

echo
if [ "$failed" -eq 0 ]; then echo "  ✓ all tests pass"; else echo "  ✗ $failed tests failed"; exit 1; fi
