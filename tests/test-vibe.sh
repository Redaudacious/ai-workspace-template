#!/usr/bin/env bash
# Test for `bin/vibe.sh`, in a fabricated HOME and workspace. Nothing here touches the
# `~/.vibe` of the machine or starts Vibe.
set -u

python3 -c 'import tomllib' 2>/dev/null || { echo "skipped: python3 has no tomllib, which comes with 3.11"; exit 77; }

R="${TESTS_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
export HOME="$T/home"; unset VIBE_HOME
S="$T/a space"
C="$HOME/.claude/plugins/cache/m"
V="$HOME/.vibe"
mkdir -p "$S/bin" "$S/skills/documentation" "$S/records/memory" "$S/agents" "$V"
cp "$R/bin/vibe.sh" "$S/bin/" 2>/dev/null
for a in executor escalation reader; do
  printf -- '---\nname: %s\n---\n\nYou are %s-witness. You run with the skill `execute`.\n' "$a" "$a" > "$S/agents/$a.md"
done
printf -- '---\nname: reader\n---\n\nYou are reader-witness.\n' > "$S/agents/reader.md"
printf '@AGENTS.md\n\n## Only for Mistral Vibe\n\nMARKER-MODULE\n' > "$S/MISTRAL.md"
printf '# House rules\n\nMARKER-HOUSE\n' > "$S/records/house-rules.md"
printf -- '- [Fact](fact.md) - MARKER-MEMORY\n' > "$S/records/memory/MEMORY.md"
printf -- '---\nname: documentation\n---\n' > "$S/skills/documentation/SKILL.md"
skill() {  # plugin skill text - a SKILL.md with a header, in the fabricated clone
  mkdir -p "$C/$1/1/skills/$2"
  printf -- '---\nname: %s\ndescription: x\n---\n\n%s\n' "$2" "$3" > "$C/$1/1/skills/$2/SKILL.md"
}
skill superpowers using-superpowers MARKER-SUPERPOWERS
skill superpowers brainstorming MARKER-BRAINSTORMING
skill ponytail ponytail MARKER-PONYTAIL
python3 -c 'import json,sys; json.dump({"plugins": [{"name": n, "marketplace": "m", "version": "1"} for n in ("superpowers","ponytail")]}, open(sys.argv[1], "w"))' "$S/plugins.lock.json"
# What the human had before: a key, a model and a hook of their own, and a house model with another price.
cat > "$V/config.toml" <<'EOT'
theme = "textual-dark"

[[models]]
name = "human-own"
provider = "mistral"
alias = "human-own"

[[models]]
name = "mistral-large-4"
provider = "mistral"
alias = "large-4"
input_price = 9.99
EOT
cat > "$V/hooks.toml" <<'EOT'
[[hooks]]
name = "human-own"
type = "post_tool"
command = "echo human-own"
EOT

failed=0
check() {  # condition message
  if eval "$1"; then printf '  ✓ %s\n' "$2"; else failed=$((failed + 1)); printf '  ✗ %s\n' "$2"; fi
}
toml() {  # file expression - a Python expression on the dictionary read; `m` holds the models by alias
  python3 -c 'import os, sys, tomllib; d = tomllib.load(open(sys.argv[1], "rb")); m = {x["alias"]: x for x in d.get("models", [])}; sys.exit(0 if eval(sys.argv[2]) else 1)' "$1" "$2"
}
run() {  # runs the copied script; the exit code goes in $code, the errors in $T/err
  if "$S/bin/vibe.sh" >"$T/out" 2>"$T/err"; then code=0; else code=$?; fi
}

run
check '[ "$code" -eq 0 ]' "the script passes on a complete workspace (code $code)"

# ── the global rules file ─────────────────────────────────────────
g="$V/AGENTS.md"
check '[ "$(grep -o "MARKER-[A-Z]*" "$g" 2>/dev/null | tr "\n" " ")" = "MARKER-MODULE MARKER-HOUSE MARKER-MEMORY MARKER-SUPERPOWERS MARKER-PONYTAIL " ]' \
  "the global file has all of them, in order: module, house, memory, superpowers, ponytail"
check '! grep -qx "@AGENTS.md" "$g" && ! grep -qx "name: ponytail" "$g"' \
  "no import of the module and no skill headers"
check 'grep -qF "$S/records/memory/" "$g"' "the memory index says where its files are"

# ── config.toml: the keys of the house, the rest is the human's ───
c="$V/config.toml"
check 'toml "$c" "d[\"include_commit_signature\"] is False and d[\"active_model\"] == \"large-4\""' \
  "commits without the Vibe signature, Large 4 active"
check 'toml "$c" "d[\"theme\"] == \"textual-dark\" and \"human-own\" in m"' "the key and the model of the human stay"
check 'toml "$c" "sorted(m) == [\"human-own\", \"large-4\", \"large-4-low\", \"small-4\"] and len(d[\"models\"]) == 4"' \
  "the old house model is replaced, not duplicated"
check 'toml "$c" "m[\"large-4\"][\"name\"] == \"mistral-large-4\" and m[\"large-4\"][\"auto_compact_threshold\"] == 400000 and m[\"large-4\"][\"input_price\"] == 0.68 and m[\"large-4\"][\"thinking\"] == \"high\""' \
  "large-4: mistral-large-4, with thinking, today's price, compaction at 400000"
check 'toml "$c" "m[\"large-4-low\"][\"name\"] == \"mistral-large-4\" and m[\"large-4-low\"][\"thinking\"] == \"low\""' \
  "large-4-low: the same model, with low thinking"
check 'toml "$c" "m[\"small-4\"][\"name\"] == \"mistral-small-2603\" and m[\"small-4\"][\"auto_compact_threshold\"] == 200000"' \
  "small-4: mistral-small-2603, compaction at 200000"

# ── trust ─────────────────────────────────────────────────────────
t="$V/trusted_folders.toml"
check 'S="$S" toml "$t" "d[\"trusted\"] == [os.environ[\"S\"]] and d[\"untrusted\"] == []"' \
  "the root of the workspace is a trusted folder"
check '[ "$(stat -c %a "$t" 2>/dev/null)" = 600 ]' "the trust file belongs only to the human, 0600"

# ── the house reminder ────────────────────────────────────────────
h="$V/hooks.toml"
check 'S="$S" toml "$h" "[x[\"name\"] for x in d[\"hooks\"]] == [\"human-own\", \"reminder\"] and d[\"hooks\"][1][\"type\"] == \"post_agent\" and os.environ[\"S\"] + \"/bin/reminder.py\" in d[\"hooks\"][1][\"command\"] and d[\"hooks\"][1][\"command\"].endswith(\"--tool vibe || true\")"' \
  "hooks.toml: the house reminder after each reply, next to the hook of the human"

# ── the profiles and the skills ───────────────────────────────────
for p in spec:large-4 plans:large-4 orchestration:large-4 execute:large-4 escalation:large-4 \
         execute-fast:large-4-low reader:small-4 helper:large-4; do
  check 'toml "$V/agents/${p%%:*}.toml" "d[\"active_model\"] == \"${p#*:}\""' "the profile ${p%%:*} is on ${p#*:}"
done
check 'toml "$V/agents/execute.toml" "d[\"instructions\"].startswith(\"You are executor-witness.\") and \"the \`skill\` tool\" in d[\"instructions\"]"' \
  "execute gets the instructions of the executor, with the loading of the skill"
check 'toml "$V/agents/execute-fast.toml" "\"executor-witness\" in d[\"instructions\"]" && toml "$V/agents/escalation.toml" "\"escalation-witness\" in d[\"instructions\"]"' \
  "execute-fast and escalation, the same"
check 'toml "$V/agents/reader.toml" "d[\"instructions\"] == \"You are reader-witness.\"" && toml "$V/agents/spec.toml" "\"instructions\" not in d"' \
  "the reader without the addition about the skill; the session roles without instructions"
check '[ "$(readlink "$V/skills/documentation")" = "$S/skills/documentation" ] && [ "$(readlink "$V/skills/brainstorming")" = "$C/superpowers/1/skills/brainstorming" ]' \
  "the skills of the house and of the plugins are linked"
check '[ -d "$V/tmp" ]' "the temporary folder of the sessions exists"

# ── the second run ────────────────────────────────────────────────
run
check '[ "$code" -eq 0 ] && toml "$c" "len(d[\"models\"]) == 4" && toml "$t" "len(d[\"trusted\"]) == 1" && toml "$h" "len(d[\"hooks\"]) == 2"' \
  "the second run duplicates nothing"

# ── VIBE_HOME and a workspace without the personal layer ──────────
mv "$S/records" "$T/records-moved"
if VIBE_HOME="$T/other" "$S/bin/vibe.sh" >/dev/null 2>&1; then code=0; else code=$?; fi
mv "$T/records-moved" "$S/records"
check '[ "$code" -eq 0 ] && [ -f "$T/other/agents/reader.toml" ] && grep -q MARKER-MODULE "$T/other/AGENTS.md" && ! grep -q MARKER-HOUSE "$T/other/AGENTS.md"' \
  "VIBE_HOME moves everything; without the personal layer, the global file is written without it"

# ── what belongs to the human is not overwritten ──────────────────
printf 'description = "mine"\nactive_model = "human-own"\n' > "$V/agents/spec.toml"
run
check '[ "$code" -eq 1 ] && grep -q "human-own" "$V/agents/spec.toml" && grep -q "belongs to the human" "$T/err"' \
  "a profile written by the human is not overwritten, and the script says so with its exit code"
rm "$V/agents/spec.toml"

cp "$c" "$T/good.toml"; printf 'not = = toml\n' > "$c"
run
check '[ "$code" -eq 1 ] && grep -qx "not = = toml" "$c"' "a broken config.toml is not overwritten"
cp "$T/good.toml" "$c"

rm "$V/skills/documentation"; mkdir "$V/skills/documentation"
run
check '[ "$code" -eq 1 ] && [ ! -e "$V/skills/documentation/documentation" ]' \
  "a real folder with the name of a skill is refused, not overwritten"
rmdir "$V/skills/documentation"

# ── the house models, from the config of the human, by level ──────
cat >> "$V/config.toml" <<'EOT'

[[models]]
name = "qwen-agent"
provider = "home"
alias = "qwen-agent"
thinking = "off"
thinking_levels = ["off", "low", "medium", "high"]
max_context_length = 262144

[[providers]]
name = "home"
api_base = "http://127.0.0.1:8091/v1"
api_style = "openai"
EOT
rm -f "$V/agents/spec.toml"
before=$(sha256sum "$V/config.toml")
if VIBE_HOME="$T/home-model" "$S/bin/vibe.sh" >"$T/out" 2>"$T/err"; then code=0; else code=$?; fi
q="$T/home-model/config.toml"
check '[ "$code" -eq 0 ] && toml "$q" "[p[\"name\"] for p in d[\"providers\"]] == [\"home\"] and d[\"providers\"][0][\"api_base\"] == \"http://127.0.0.1:8091/v1\""' \
  "the miniature house gets the home provider of the human (code $code)"
check 'toml "$q" "sorted(m) == [\"large-4\", \"large-4-low\", \"qwen-agent\", \"qwen-agent-high\", \"qwen-agent-low\", \"qwen-agent-medium\", \"small-4\"]"' \
  "qwen-agent, plus an alias for each level, next to the Mistral models"
check 'toml "$q" "m[\"qwen-agent\"][\"thinking\"] == \"off\" and all(m[\"qwen-agent-\" + n][\"thinking\"] == n and m[\"qwen-agent-\" + n][\"name\"] == \"qwen-agent\" and m[\"qwen-agent-\" + n][\"provider\"] == \"home\" for n in (\"low\", \"medium\", \"high\"))"' \
  "each alias has its own level and asks for the same model, at the home provider"
for p in qwen-agent qwen-agent-low qwen-agent-medium qwen-agent-high; do
  check 'toml "$T/home-model/agents/$p.toml" "d[\"active_model\"] == \"$p\""' "the profile $p is on $p"
done
check '[ "$(sha256sum "$V/config.toml")" = "$before" ]' "the config of the human, read as a source, stays untouched"
if VIBE_HOME="$T/home-model" "$S/bin/vibe.sh" >/dev/null 2>&1; then code=0; else code=$?; fi
check '[ "$code" -eq 0 ] && toml "$q" "len(d[\"models\"]) == 7 and len(d[\"providers\"]) == 1"' \
  "the second run does not duplicate the house models"
run
check '[ "$code" -eq 0 ] && toml "$c" "sorted(m) == [\"human-own\", \"large-4\", \"large-4-low\", \"qwen-agent\", \"qwen-agent-high\", \"qwen-agent-low\", \"qwen-agent-medium\", \"small-4\"]"' \
  "on the Vibe of the human, the aliases by level are added once, next to their model"

# ── the profiles of the house models and the helper ───────────────
a="$T/home-model/agents"
check '[ "$(ls "$a" | grep -c "^qwen-agent")" -eq 16 ]' \
  "four profiles for each alias of the house: the alias, the executor and the two of the GVS5H method"
check 'toml "$a/qwen-agent-execute-low.toml" "d[\"active_model\"] == \"qwen-agent-low\" and d[\"instructions\"].startswith(\"You are executor-witness.\") and \"vibe --agent reader\" in d[\"instructions\"] and \"vibe --agent qwen-agent-execute-low\" in d[\"instructions\"]"' \
  "the executor of the house by level: the instructions of the executor, then those of the house models, naming its executor"
check 'toml "$a/qwen-agent.toml" "d[\"active_model\"] == \"qwen-agent\" and \"vibe --agent helper\" in d[\"instructions\"] and \"vibe --agent qwen-agent-execute\`\" in d[\"instructions\"]"' \
  "the alias without a level: the instructions of the house, with the executor without a level"
check 'toml "$a/qwen-agent-gvs5h-medium.toml" "d[\"active_model\"] == \"qwen-agent-medium\" and \"GVS5H\" in d[\"instructions\"] and \"vibe --agent qwen-agent-worker-medium\" in d[\"instructions\"]" && toml "$a/qwen-agent-worker-high.toml" "d[\"active_model\"] == \"qwen-agent-high\" and d[\"instructions\"].startswith(\"You are a worker\")"' \
  "the GVS5H method: the leader names the worker of the same level; the worker has its own text"
check 'toml "$a/helper.toml" "d[\"active_model\"] == \"large-4\" and d[\"enabled_tools\"] == [\"grep\", \"read_file\"] and d[\"instructions\"].startswith(\"You are the helper\")"' \
  "the helper: Large 4, read-only"

rm -rf "$C/ponytail"
run
check '[ "$code" -eq 1 ] && grep -q "the clone of ponytail is missing" "$T/err"' \
  "a missing plugin clone is reported and gives code 1"

[ "$failed" -eq 0 ] && echo "  all passed" || { echo "  $failed failed"; exit 1; }
