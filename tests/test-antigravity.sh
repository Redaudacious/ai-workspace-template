#!/usr/bin/env bash
# Test for `bin/antigravity.sh` and `bin/antigravity-memento.py`, in a fabricated HOME
# and workspace. Nothing here touches the machine.
set -u

R="${TESTS_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
export HOME="$T/home"
S="$T/space"
mkdir -p "$HOME/.gemini/config" "$S/skills/documentation" "$S/records/memory" \
         "$S/projects/game/games/level"
printf '# R\n' > "$S/AGENTS.md"; printf '@AGENTS.md\n' > "$S/GEMINI.md"
printf '# P\n' > "$S/projects/game/AGENTS.md"; printf '# L\n' > "$S/projects/game/games/level/AGENTS.md"
touch "$S/skills/documentation/SKILL.md" "$S/records/house-rules.md" "$S/records/memory/MEMORY.md"
git -C "$S/projects/game" init -q

failed=0
check() {  # condition message
  if eval "$1"; then printf '  ✓ %s\n' "$2"; else failed=$((failed + 1)); printf '  ✗ %s\n' "$2"; fi
}

# shellcheck disable=SC1090
ANTIGRAVITY_FUNCTIONS_ONLY=1 source "$R/bin/antigravity.sh"
check 'declare -F link >/dev/null && declare -F local_file >/dev/null && declare -F version_from_url >/dev/null' \
  "the script lets itself be loaded for its functions only"

# ── the links ────────────────────────────────────────────────────
mkdir -p "$HOME/.gemini/config/skills"
link "$S/skills/documentation" "$HOME/.gemini/config/skills/documentation"
check '[ "$(readlink "$HOME/.gemini/config/skills/documentation")" = "$S/skills/documentation" ]' \
  "a missing link is created"
rm "$HOME/.gemini/config/skills/documentation"; mkdir "$HOME/.gemini/config/skills/documentation"
if link "$S/skills/documentation" "$HOME/.gemini/config/skills/documentation" 2>/dev/null; then code=0; else code=$?; fi
check '[ "$code" -ne 0 ] && [ ! -e "$HOME/.gemini/config/skills/documentation/documentation" ]' \
  "a real folder is refused, not overwritten"

# ── local files ──────────────────────────────────────────────────
# One file per include. Antigravity calculates the 24,000-byte limit after
# inclusion, and the root AGENTS.md alone nearly fills it.
mkdir -p "$S/projects/old"; printf '# Old rules\n' > "$S/projects/old/CLAUDE.md"
mkdir -p "$S/.agents/rules"; printf 'old\n' > "$S/.agents/rules/framework.md"
local_file "$S" "$S"
r="$S/.agents/rules"
check '[ ! -e "$r/framework.md" ]' "the old local file, a single one, goes away"
check 'head -3 "$r/framework-01.md" | grep -qx "trigger: always_on"' "each local file is an always-on rule"
check 'grep -q "](../../records/house-rules.md)" "$r/framework-01.md" && grep -q "](../../records/memory/MEMORY.md)" "$r/framework-02.md"' \
  "the root brings in house rules and the memory index, one per file"
check '[ "$(ls "$r" | wc -l)" -eq 2 ]' "the root does not bring in its own rules, which Antigravity reads on its own"

local_file "$S/projects/game/games/level" "$S"
n="$S/projects/game/games/level/.agents/rules"
check 'grep -q "](../../../../../../AGENTS.md)" "$n/framework-01.md"' "the game brings in the root AGENTS.md first"
check 'grep -q "](../../../../AGENTS.md)" "$n/framework-02.md"' "then the project AGENTS.md"
check 'grep -q "](../../../../../../GEMINI.md)" "$n/framework-03.md"' "then the root GEMINI.md"
check 'grep -q "house-rules.md)" "$n/framework-04.md" && grep -q "MEMORY.md)" "$n/framework-05.md" && [ "$(ls "$n" | wc -l)" -eq 5 ]' \
  "then house rules and memory, and nothing else: its own AGENTS.md is read on its own"

local_file "$S/projects/old" "$S"
check 'grep -q "](../../CLAUDE.md)" "$S/projects/old/.agents/rules/framework-03.md"' \
  "a project not yet moved to the pair brings in CLAUDE.md, which Antigravity does not read on its own"

local_file "$S/projects/game" "$S"; local_file "$S/projects/game" "$S"
ex="$S/projects/game/.git/info/exclude"
check '[ "$(grep -cxF "/.agents/rules/framework-[0-9][0-9].md" "$ex")" -eq 1 ]' \
  "local files are kept out of git, with a single line"
check '[ -z "$(git -C "$S/projects/game" status --porcelain -- .agents)" ]' "git does not see the local files"
check 'git -C "$S/projects/game" check-ignore -q games/level/.agents/rules/framework-01.md' \
  "nor those of a folder inside the repository"

# A file of the user that also starts with "framework" is not the script's. It is not deleted.
printf 'user file\n' > "$S/projects/game/.agents/rules/framework-custom.md"
local_file "$S/projects/game" "$S"
check '[ -f "$S/projects/game/.agents/rules/framework-custom.md" ] && ! git -C "$S/projects/game" check-ignore -q .agents/rules/framework-custom.md' \
  "a user rule with a similar name stays, and git sees it"

# An include that goes over 24,000 bytes with the local file header is reported.
mkdir -p "$S/projects/large"; head -c 23950 /dev/zero | tr '\0' 'x' > "$S/projects/large/CLAUDE.md"
if local_file "$S/projects/large" "$S" 2>"$T/err"; then code=0; else code=$?; fi
check '[ "$code" -ne 0 ] && grep -q "24,000" "$T/err"' "an include over the limit exits with an error code and a message"

# ── the whole script, in a workspace with a space in the path ────
# A path with a space blocked the folder loop: `xargs` cut it into relative pieces,
# and climbing from `.` never reached the root. The plugin clones are missing here,
# so the script exits with 1, but only after it writes the local files.
Z="$T/a space"; mkdir -p "$Z/bin" "$Z/skills" "$Z/projects/A Game/games/second" "$HOME/.gemini/antigravity"
cp "$R/bin/antigravity.sh" "$Z/bin/"
printf '# R\n' > "$Z/AGENTS.md"; git -C "$Z/projects/A Game" init -q
printf '# Old rules\n' > "$Z/projects/A Game/games/second/CLAUDE.md"
python3 -c 'import json,sys; json.dump({"plugins": [{"name": n, "marketplace": "m", "version": "1"} for n in ("superpowers","ponytail","rtk-plugin")]}, open(sys.argv[1], "w"))' "$Z/plugins.lock.json"
if timeout 60 "$Z/bin/antigravity.sh" >"$T/out" 2>"$T/err"; then code=0; else code=$?; fi
check '[ "$code" -ne 124 ]' "a path with a space does not hang the script (code $code)"
check '[ "$code" -eq 1 ] && grep -q "clone of superpowers is missing" "$T/err"' "a missing plugin clone is reported and gives code 1"
check '[ -f "$Z/projects/A Game/.agents/rules/framework-01.md" ] && [ -f "$Z/projects/A Game/games/second/.agents/rules/framework-01.md" ]' \
  "the repository and the folder with old rules receive their local files"
check '[ ! -e "$Z/projects/A Game/node_modules" ]' "nothing is written outside the chosen folders"

# ── a plugin removed from the lockfile ───────────────────────────
# The README says a plugin can leave the lockfile. Its global rule then goes away
# and the other rules are still written. Looking it up in an empty list stopped the whole script.
for n in superpowers ponytail; do mkdir -p "$HOME/.claude/plugins/cache/m/$n/1/skills"; done
c="$HOME/.claude/plugins/cache/m/superpowers/1/skills/using-superpowers"
mkdir -p "$c/references" "$HOME/.claude/plugins/cache/m/ponytail/1/skills/ponytail"
touch "$c/SKILL.md" "$c/references/antigravity-tools.md" "$HOME/.claude/plugins/cache/m/ponytail/1/skills/ponytail/SKILL.md"
printf 'old\n' > "$HOME/.gemini/config/rules/ponytail.md"
python3 -c 'import json,sys; json.dump({"plugins": [{"name": n, "marketplace": "m", "version": "1"} for n in ("superpowers",)]}, open(sys.argv[1], "w"))' "$Z/plugins.lock.json"
if timeout 60 "$Z/bin/antigravity.sh" >"$T/out" 2>"$T/err"; then code=0; else code=$?; fi
check '[ "$code" -eq 0 ] && [ -f "$HOME/.gemini/config/rules/superpowers.md" ]' \
  "without ponytail in the lockfile, the script passes and writes the other rules (code $code)"
check '[ ! -e "$HOME/.gemini/config/rules/ponytail.md" ]' "the rule of the removed plugin goes away with it"

# ── the memento: the hook before every model call ────────────────
# Gemini 3.1 Pro did not announce the skill in time, even with the rule written.
# The memento reads the last model response in the log. After a skill read or after
# an edit, it slips in a reminder. Otherwise it says nothing.
M="$R/bin/antigravity-memento.py"
log() {  # the calls of the last response, as JSON, in a log with one response
  printf '{"step_index": 0, "type": "USER_INPUT", "content": "x"}\n{"step_index": 1, "type": "PLANNER_RESPONSE", "tool_calls": %s}\n{"step_index": 2, "type": "GENERIC", "content": "result"}\n' "$1" > "$T/transcript.jsonl"
}
memento() {  # the output of the memento on the fabricated log
  printf '{"transcriptPath": "%s", "artifactDirectoryPath": "/brain/c1"}' "$T/transcript.jsonl" | python3 "$M" 2>/dev/null
}
log '[{"name": "view_file", "args": {"AbsolutePath": "/h/.gemini/config/skills/brainstorming/SKILL.md"}}]'
check 'memento | grep -qF "Using brainstorming to"' "after a skill is read, the memento asks for its announcement"
log '[{"name": "view_file", "args": {"AbsolutePath": "/h/.gemini/config/skills/using-superpowers/SKILL.md"}}]'
check '[ "$(memento)" = "{}" ]' "using-superpowers, read at every start, gets no memento"
log '[{"name": "replace_file_content", "args": {"TargetFile": "/p/calc.py"}}]'
check 'memento | grep -qF "calc.py"' "after an edit, the memento names the file"
log '[{"name": "write_to_file", "args": {"TargetFile": "/brain/c1/task.md"}}]'
check '[ "$(memento)" = "{}" ]' "the task list of the conversation gets no memento"
log '[{"name": "run_command", "args": {"CommandLine": "rtk git status"}}]'
check '[ "$(memento)" = "{}" ]' "after any other command, nothing"
# Bench spec stage, round 1: Gemini proposed `cron` and `systemd` with no search,
# although GEMINI.md requires one before an option that names a tool.
QUESTION='[{"name": "ask_question", "args": {"questions": [{"question": "How do we schedule?", "options": ["(Recommended) cron", "systemd"]}]}}]'
log "$QUESTION"
check 'memento | grep -qF "search_web"' "a question with options and no search before it gets the search memento"
printf '{"step_index": 0, "type": "PLANNER_RESPONSE", "tool_calls": [{"name": "search_web", "args": {"query": "systemd timer"}}]}\n{"step_index": 1, "type": "PLANNER_RESPONSE", "tool_calls": %s}\n' "$QUESTION" > "$T/transcript.jsonl"
check '[ "$(memento)" = "{}" ]' "after a search, the question with options gets no memento"
# Execute stage, round 0: the closing "yes", with a "Recommended" option, sent Gemini to
# search the web. Looking up the source before the options belongs to the spec session.
printf '{"step_index": 0, "type": "PLANNER_RESPONSE", "tool_calls": [{"name": "view_file", "args": {"AbsolutePath": "/h/.gemini/config/skills/execute/SKILL.md"}}]}\n{"step_index": 1, "type": "PLANNER_RESPONSE", "tool_calls": %s}\n' "$QUESTION" > "$T/transcript.jsonl"
check '[ "$(memento)" = "{}" ]' "in the plans or execute session, the question with options does not ask for the search"
# Round 2: a window that closed on its own, "User Skipped", was taken as a "yes".
printf '{"step_index": 0, "type": "PLANNER_RESPONSE", "tool_calls": [{"name": "ask_question", "args": {"questions": [{"question": "Did you read the spec?", "options": ["Yes", "No"]}]}}]}\n{"step_index": 1, "type": "GENERIC", "content": "A1: User Skipped"}\n' > "$T/transcript.jsonl"
check 'memento | grep -qF "so it is not a yes"' "a skipped answer gets the memento that stops the turn"
# Round 3: stopping alone replaced the search, because without an interface every question is skipped.
printf '{"step_index": 0, "type": "PLANNER_RESPONSE", "tool_calls": %s}\n{"step_index": 1, "type": "GENERIC", "content": "A1: User Skipped"}\n' "$QUESTION" > "$T/transcript.jsonl"
check 'memento | grep -qF "search_web" && memento | grep -qF "After the search, end your turn"' \
  "a skipped question with options not yet searched asks for the search first, then the stop"
check '[ "$(printf "{\"transcriptPath\": \"/does/not/exist\"}" | python3 "$M" 2>/dev/null)" = "{}" ]' \
  "a missing log still gives {}: the memento does not stop the agent"

# The hook is merged by name. A hook of the user in the same file stays.
printf '{"user-hook": {"Stop": [{"command": "true"}]}}\n' > "$HOME/.gemini/config/hooks.json"
cp "$M" "$Z/bin/"
timeout 60 "$Z/bin/antigravity.sh" >"$T/out" 2>"$T/err"
check 'python3 -c "import json,sys; h=json.load(open(sys.argv[1])); c=h[\"memento\"][\"PreInvocation\"][0][\"command\"]; assert \"user-hook\" in h and sys.argv[2] in c" "$HOME/.gemini/config/hooks.json" "$Z/bin/antigravity-memento.py"' \
  "the memento enters the global hooks.json, next to the hooks of the user"
printf 'not json\n' > "$HOME/.gemini/config/hooks.json"
if timeout 60 "$Z/bin/antigravity.sh" >"$T/out" 2>"$T/err"; then code=0; else code=$?; fi
check '[ "$code" -ne 0 ] && grep -qx "not json" "$HOME/.gemini/config/hooks.json"' \
  "a broken hooks.json is not overwritten, and the script says so with its code"

# ── update, with a fake curl ─────────────────────────────────────
# curl serves the download page and the archive from files. Nothing leaves the machine.
mkdir -p "$T/fake"
cat > "$T/fake/curl" <<'EOT'
#!/usr/bin/env bash
for a in "$@"; do last="$a"; done
case "$last" in
  */download/) cat "$FAKE_PAGE" ;;
  *Antigravity.tar.gz) cat "$FAKE_ARCHIVE" ;;
esac
EOT
chmod +x "$T/fake/curl"
archive() {  # destination with-binary
  local a="$T/archive/Antigravity-x64"; rm -rf "$T/archive"; mkdir -p "$a"
  [ "$2" = yes ] && { printf '#!/bin/sh\n' > "$a/antigravity"; chmod +x "$a/antigravity"; }
  touch "$a/LICENSE"; tar czf "$1" -C "$T/archive" Antigravity-x64
}
O="$HOME/opt/antigravity"; mkdir -p "$O"; printf '#!/bin/sh\n' > "$O/antigravity"; chmod +x "$O/antigravity"
printf 'href="https://storage.googleapis.com/antigravity-public/antigravity-hub/2.19.1-1/linux-x64/Antigravity.tar.gz"\n' > "$T/page"
printf 'nothing here\n' > "$T/empty-page"
upd() { PATH="$T/fake:$PATH" FAKE_PAGE="$1" FAKE_ARCHIVE="$T/archive.tgz" update >"$T/out" 2>"$T/err"; }

printf '2.19.1\n' > "$O/.version"
if upd "$T/empty-page"; then code=0; else code=$?; fi
check '[ "$code" -eq 1 ] && grep -q "no longer on the page" "$T/err"' "a page without a URL: code 1, with a message"
if upd "$T/page"; then code=0; else code=$?; fi
check '[ "$code" -eq 0 ] && grep -q "up to date" "$T/out"' "the same version: nothing to do"
printf '3.0.0\n' > "$O/.version"
if upd "$T/page"; then code=0; else code=$?; fi
check '[ "$code" -eq 1 ] && grep -q "not downgrading" "$T/err"' "an older version on the page is not installed"
printf '2.0.0\n' > "$O/.version"; archive "$T/archive.tgz" no
if upd "$T/page"; then code=0; else code=$?; fi
check '[ "$code" -eq 1 ] && grep -qx 2.0.0 "$O/.version" && [ -x "$O/antigravity" ]' \
  "an archive without a binary is refused, and the old installation stays whole"
archive "$T/archive.tgz" yes
if upd "$T/page"; then code=0; else code=$?; fi
check '[ "$code" -eq 0 ] && grep -qx 2.19.1 "$O/.version" && [ ! -e "$O.old" ] && [ ! -e "$O.new" ]' \
  "a new version is installed, with no leftovers"

# ── the version from the archive URL ─────────────────────────────
v="$(version_from_url https://storage.googleapis.com/antigravity-public/antigravity-hub/2.19.1-6046815158665216/linux-x64/Antigravity.tar.gz)"
check '[ "$v" = 2.19.1 ]' "the version is read from the URL ($v)"

[ "$failed" -eq 0 ] && echo "  all passed" || { echo "  $failed failed"; exit 1; }
