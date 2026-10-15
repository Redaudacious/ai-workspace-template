#!/usr/bin/env bash
# Connects the workspace to Mistral Vibe, in `$VIBE_HOME` (default `~/.vibe/`): the global rules
# file, the models, the trust root, the role profiles and the skills.
# The house models, which are not Mistral, come from the human's `~/.vibe/config.toml`. Each gets
# one alias and one profile for each thinking level. Each alias also has its executor and the
# profiles of the GVS5H method. The helper is Large 4, read-only.
#
# Full details: docs/reference/vibe.md. Vibe reads only `AGENTS.md` files on its own: the global
# one, in `$VIBE_HOME`, and the project's, up to the trust folder. It does not include other
# files, so the module, the house rules, the memory and the modes are copied into the global
# one. Vibe follows the links of skills, so skills are linked.
#
# With VIBE_FUNCTIONS_ONLY=1 the script can be loaded with `source`, for tests.

HEADER="Written by bin/vibe.sh"

# What belongs only to the house models, which are not Mistral. It is added to the instructions
# of each of their profiles. `@EXECUTOR@` becomes the executor on the same model and level.
# Change this text here, not in MISTRAL.md, which belongs to all models.
INSTR_HOUSE=$(cat <<'EOF'
You run on a house model, on one of the human's machines, not at Mistral. You write slower than Large 4. You add nothing to the Vibe sum. The agents you call do.

- The reader reads in your place. Call it before any reading of your own. Web research belongs to the reader from the first page. Do not start with a search or a page. Start with the reader. If a folder has more than ten files, do not read them yourself, not one by one, not with `cat`, not with a script. Give the folder to the reader. Ask only for what you want back, for example the totals, not the sheets: `vibe --agent reader --trust -p "<the question and what you want back>" --max-price 0.20 </dev/null`. The reader can take a few minutes. Wait for its answer before you call another agent.
- When a test or a probe still fails after two attempts, ask the helper for advice before the third. The helper is Large 4, read-only: `vibe --agent helper -p "<the task, what you tried, what happened>" --max-price 0.50 </dev/null`. It tells you what to change. The work stays yours.
- Your session fails if it passes about 98,000 tokens. Then Vibe compacts your context, and compaction does not work on this machine. Read from files only what you need, with `sed -n`, `grep -n` and `head`. Shorten any output of more than one hundred lines.
- When you orchestrate, your executor is `vibe --agent @EXECUTOR@`, not `vibe --agent execute`.
- Write to the human in English, including the short status messages between tools.
- Before your first write or first commit in a repository, read its `IMPACT.md` with `read_file`, even when the plan does not name it. The plan you read and `git status` do not replace it.
- Announce each skill you call with one sentence of text, in the same response as the call and before it: `Using <skill> to <purpose>.` An announcement written only at the end does not replace it.
- Before the first commit, create the branch named in the plan header, with `git switch -c <branch>`, from the main branch of the repository, whatever its name (`main` or `master`). Never commit on the main branch, not even the report.
EOF
)
INSTR_HELPER=$(cat <<'EOF'
You are the helper: a bigger model, called by a smaller model that is stuck. You receive its task, what it tried and what happened.

Read from the project only what you need to understand why it fails. Then return short advice: what is wrong and what to try, with the file and the line, in English, in at most 300 words. Do not write the whole code and do not change anything. Your tools are read-only, and the work stays with the one who called you.
EOF
)
# The GVS5H method, with tools: the leader keeps the notebook, and a new worker does each step.
# `@WORKER@` becomes the worker on the same model and level.
INSTR_GVS5H=$(cat <<'EOF'
You work by the GVS5H method. You lead, and a new worker does each step. The worker starts with nothing from your conversation. The shared state sits in two files in `$VIBE_HOME/tmp/gvs5h/`: `plan.md`, the steps, without code, in at most 4,000 characters, and `notes.md`, what was learned, in at most 8,000.

1. Write `plan.md` from the task.
2. Give each step to a worker: `vibe --agent @WORKER@ -p "<the whole task>. Step: <the step>. Shared state: <the path of plan.md> and <the path of notes.md>." --max-price 0.20 </dev/null`.
3. After the worker, read `notes.md`, run the verifier and add two lines to `notes.md`, `STATUS:` and `NEXT:`. If the same approach failed twice, `NEXT` asks for another.
4. Stop when the verifier passes or after six workers. The commits and the report stay yours, as in any execution.
EOF
)
INSTR_WORKER=$(cat <<'EOF'
You are a worker of the GVS5H method. You know nothing except the request and the two files it names, `plan.md` and `notes.md`.

Do only the step requested, in the files of the project, and run its probe. At the end, add a paragraph to the end of `notes.md`: what you changed and what the probe returned. Do not commit and do not call other agents.
EOF
)

link() {  # source destination
  # A REAL folder with the name of the skill belongs to the human: `ln -sfn` would put the link
  # inside it, and the old skill would stay active, without a word.
  if [ -e "$2" ] && [ ! -L "$2" ]; then
    echo "vibe: $2 is a real folder. Not linking over it." >&2
    return 1
  fi
  ln -sfn "$1" "$2"
}

plugin() {  # repo name — the folder of the pinned clone, relative to the cache. Exit 1 if it left the lockfile
  python3 -c 'import json,sys; p=[p for p in json.load(open(sys.argv[1]))["plugins"] if p["name"]==sys.argv[2]]; p or sys.exit(1); print(p[0]["marketplace"], p[0]["name"], p[0]["version"], sep="/")' \
    "$1/plugins.lock.json" "$2"
}

link_skills() {  # repo home cache — the skills of the house, then those of the pinned plugins
  local repo="$1" d="$2/skills" cache="$3" s name market version incomplete=0
  mkdir -p "$d"
  for s in "$repo"/skills/*/; do
    link "${s%/}" "$d/$(basename "$s")" || incomplete=1
  done
  while IFS=$'\t' read -r name market version; do
    if [ ! -d "$cache/$market/$name/$version" ]; then
      echo "vibe: the clone of $name is missing. The restore brings it." >&2; incomplete=1; continue
    fi
    for s in "$cache/$market/$name/$version"/skills/*/; do
      [ -f "$s/SKILL.md" ] || continue
      link "${s%/}" "$d/$(basename "$s")" || incomplete=1
    done
  done < <(python3 -c 'import json,sys; [print(p["name"], p["marketplace"], p["version"], sep="\t") for p in json.load(open(sys.argv[1]))["plugins"]]' "$repo/plugins.lock.json")
  return "$incomplete"
}

without_header() {  # file — the content, without the YAML header of a SKILL.md
  awk 'NR == 1 && $0 == "---" { a = 1; next } a && $0 == "---" { a = 0; next } !a' "$1"
}

section() {  # title file [preamble] — a part of the global file. Exit 1 if the file is missing
  [ -f "$2" ] || { echo "vibe: $2 is missing" >&2; return 1; }
  printf '\n'
  if [ -n "$1" ]; then printf '# %s\n\n' "$1"; fi
  if [ -n "${3:-}" ]; then printf '%s\n\n' "$3"; fi
  without_header "$2"
}

global_file() {  # repo home cache — $home/AGENTS.md. Exit 1 if a part is missing
  local repo="$1" home="$2" cache="$3" p incomplete=0
  {
    printf '<!-- %s from MISTRAL.md, the house rules, the memory and the modes. Do not edit. -->\n' "$HEADER"
    tail -n +2 "$repo/MISTRAL.md"
    # The personal layer is missing on a fresh clone of the framework. Then it is not included, with no failure.
    if [ -f "$repo/records/house-rules.md" ]; then
      section "" "$repo/records/house-rules.md"
    fi
    if [ -f "$repo/records/memory/MEMORY.md" ]; then
      section "The agent's memory, the index" "$repo/records/memory/MEMORY.md" \
        "Each line points to a file in \`$repo/records/memory/\`."
    fi
    # A plugin removed from the lockfile, as the README allows, loses its part too.
    if p="$(plugin "$repo" superpowers)"; then
      section "Superpowers" "$cache/$p/skills/using-superpowers/SKILL.md" || incomplete=1
    fi
    if p="$(plugin "$repo" ponytail)"; then
      section "Ponytail mode, level full" "$cache/$p/skills/ponytail/SKILL.md" || incomplete=1
    fi
  } > "$home/AGENTS.md.new"
  mv "$home/AGENTS.md.new" "$home/AGENTS.md"
  return "$incomplete"
}

profile() {  # home name alias [agent definition] [extra text] [tools, comma-separated] — agents/<name>.toml, only if it is missing or the script's
  local f="$1/agents/$2.toml"
  if [ -f "$f" ] && ! grep -qF "# $HEADER" "$f"; then
    echo "vibe: $f belongs to the human. Not writing over it." >&2; return 1
  fi
  python3 - "$f" "$2" "$3" "${4:-}" "${5:-}" "${6:-}" "$HEADER" <<'EOF'
import json, sys
path, name, alias, agent, extra, tools, header = sys.argv[1:8]
lines = [f"# {header}. Do not edit.", f'description = "The house role {name}"',
         f'active_model = "{alias}"']
body = ""
if agent:
    # The body of the definition in agents/, without the YAML header: the same instructions as the
    # Claude Code agent. Vibe adds them to the system prompt of the profile.
    text = open(agent, encoding="utf-8").read()
    body = text.split("---", 2)[2].strip() if text.startswith("---") else text.strip()
    if "skill" in body:
        body += ("\n\nIn Vibe, the skill named above is not preloaded. Load it first, "
                 "with the `skill` tool.")
if extra:
    body = (body + "\n\n" + extra).strip()
if body:
    lines.append(f"instructions = {json.dumps(body, ensure_ascii=False)}")
if tools:
    # Only the named tools, as in the explore profile of Vibe: a read-only profile.
    lines.append(f"enabled_tools = {json.dumps(tools.split(','))}")
with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
EOF
}

house_toml() {  # config <path> | hooks <path> <root> | trust <path> <root> — the keys of the house, the rest stays
  python3 - "$@" <<'EOF'
import datetime, json, os, re, sys, tomllib

# The prices, in dollars per million tokens: input, from cache, output. In euros they are × 0.85.
# Large 4 is at the reduced price, with no end date on the Mistral pricing page, read on
# 9 October 2026. The full price is 1.36, 0.14 and 4.18. When the reduction ends, the sum in the
# Mistral console comes out double the house estimate. Then change the three numbers, at
# `large-4` and at `large-4-low`.
MODELS = [
    {"name": "mistral-large-4", "provider": "mistral", "alias": "large-4",
     "input_price": 0.68, "cached_input_price": 0.07, "output_price": 2.09,
     "thinking": "high", "auto_compact_threshold": 400000},
    {"name": "mistral-large-4", "provider": "mistral", "alias": "large-4-low",
     "input_price": 0.68, "cached_input_price": 0.07, "output_price": 2.09,
     "thinking": "low", "auto_compact_threshold": 400000},
    {"name": "mistral-small-2603", "provider": "mistral", "alias": "small-4",
     "input_price": 0.15, "cached_input_price": 0.015, "output_price": 0.6,
     "thinking": "high", "auto_compact_threshold": 200000},
]

# The house models (the providers that are not Mistral) come from the human's config. A miniature
# house, with another VIBE_HOME, has them too. Each model with thinking off gets one alias for
# each level, `<alias>-<level>`. The profiles of Vibe override the config, so the level is chosen
# through the alias, as with `large-4-low`.
SOURCE = os.environ.get("VIBE_SOURCE") or os.path.expanduser("~/.vibe/config.toml")


def house_ones(source):
    """The (providers, models) of the house from the config of the human, with the aliases for each level."""
    providers = [p for p in source.get("providers", []) if p.get("name") != "mistral"]
    names = {p.get("name") for p in providers}
    base = [m for m in source.get("models", [])
            if m.get("provider") in names and m.get("thinking", "off") == "off" and "alias" in m]
    levels = [{**m, "alias": f"{m['alias']}-{n}", "thinking": n}
              for m in base for n in m.get("thinking_levels", []) if n != "off"]
    return providers, base + levels


def key(k):
    return k if re.fullmatch(r"[A-Za-z0-9_-]+", k) else json.dumps(k, ensure_ascii=False)


def value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, (datetime.date, datetime.time)):
        return v.isoformat()
    if isinstance(v, list):
        return "[" + ", ".join(value(x) for x in v) + "]"
    return "{" + ", ".join(f"{key(k)} = {value(x)}" for k, x in v.items()) + "}"


def toml_text(d):
    """The simple keys on top, then the tables, then the lists of tables. Anything deeper goes inline."""
    def of_tables(v):
        return isinstance(v, list) and v and all(isinstance(x, dict) for x in v)
    top = [f"{key(k)} = {value(v)}" for k, v in d.items()
           if not isinstance(v, dict) and not of_tables(v)]
    bottom = []
    for k, v in d.items():
        if isinstance(v, dict):
            bottom += ["", f"[{key(k)}]"] + [f"{key(a)} = {value(b)}" for a, b in v.items()]
        elif of_tables(v):
            for x in v:
                bottom += ["", f"[[{key(k)}]]"] + [f"{key(a)} = {value(b)}" for a, b in x.items()]
    return "\n".join(top + bottom) + "\n"


def read(path):
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except FileNotFoundError:
        return {}
    except tomllib.TOMLDecodeError as e:
        sys.exit(f"vibe: {path} is not TOML ({e}). Not writing over it.")


def write(path, d, mode=None):
    text = toml_text(d)
    # The safety net of the small writer: what would not read back the same is not written.
    if tomllib.loads(text) != d:
        sys.exit(f"vibe: {path} cannot be rewritten without loss. Not writing over it.")
    new = path + ".new"
    with open(new, "w", encoding="utf-8") as f:
        f.write(text)
    if mode is not None:
        os.chmod(new, mode)
    os.replace(new, path)


kind, path = sys.argv[1], sys.argv[2]
d = read(path)
if kind == "config":
    d["include_commit_signature"] = False
    d["active_model"] = "large-4"
    source = d if os.path.realpath(SOURCE) == os.path.realpath(path) else read(SOURCE)
    providers, house = house_ones(source)
    foreign = {p["name"] for p in providers}
    ours = {m["alias"] for m in MODELS}
    d["models"] = [m for m in d.get("models", [])
                   if m.get("alias") not in ours and m.get("provider") not in foreign] + MODELS + house
    if providers:
        d["providers"] = [p for p in d.get("providers", []) if p.get("name") not in foreign] + providers
    write(path, d)
    # The aliases of the house, for the profiles written by bash: the alias, the base model and the level, one for each line.
    for m in house:
        level = m.get("thinking", "off")
        print(m["alias"], m["alias"] if level == "off" else m["alias"].removesuffix("-" + level), level)
elif kind == "hooks":
    # The reminder of the house after each reply (bin/reminder.py). The hooks of the human stay.
    repo = sys.argv[3]
    d["hooks"] = [h for h in d.get("hooks", []) if h.get("name") != "reminder"] + [
        {"name": "reminder", "type": "post_agent",
         "command": f'python3 "{repo}/bin/reminder.py" --tool vibe || true', "timeout": 30}]
    write(path, d)
else:
    root = sys.argv[3]
    d["trusted"] = [t for t in d.get("trusted", []) if t != root] + [root]
    d["untrusted"] = [t for t in d.get("untrusted", []) if t != root]
    write(path, d, 0o600)
EOF
}

if [ "${VIBE_FUNCTIONS_ONLY:-}" = 1 ]; then
  return 0 2>/dev/null || exit 0
fi

set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
home="${VIBE_HOME:-$HOME/.vibe}"
cache="$HOME/.claude/plugins/cache"
mkdir -p "$home/agents" "$home/skills" "$home/tmp"
incomplete=0

link_skills "$repo" "$home" "$cache" || incomplete=1
echo "skills linked in $home/skills/: $(ls "$home/skills" | wc -l)"

global_file "$repo" "$home" "$cache" || incomplete=1
echo "global rules: $home/AGENTS.md, $(wc -c < "$home/AGENTS.md") bytes"

house=$(house_toml config "$home/config.toml") || incomplete=1
house_toml trust "$home/trusted_folders.toml" "$repo" || incomplete=1
echo "config.toml: large-4 active, large-4-low, small-4${house:+, house models: $(awk '{print $1}' <<<"$house" | xargs)}. Trust root: $repo"
house_toml hooks "$home/hooks.toml" "$repo" || incomplete=1
echo "hooks.toml: the house reminder after each reply, from $repo/bin/reminder.py"

for r in spec plans orchestration; do
  profile "$home" "$r" large-4 || incomplete=1
done
# The agents of the house take their instructions from their definitions, as in Claude Code.
profile "$home" execute large-4 "$repo/agents/executor.md" || incomplete=1
profile "$home" execute-fast large-4-low "$repo/agents/executor.md" || incomplete=1
profile "$home" escalation large-4 "$repo/agents/escalation.md" || incomplete=1
profile "$home" reader small-4 "$repo/agents/reader.md" || incomplete=1
profile "$home" helper large-4 "" "$INSTR_HELPER" grep,read_file || incomplete=1
# The house models: for each alias, the profile of the alias, the profile of the executor and the two
# profiles of the GVS5H method, each with the instructions of the house. The bench asks for them
# with `--agent <model>[-<role>][-<level>]`.
while read -r a base level; do
  [ -n "$a" ] || continue
  s=""; [ "$level" = off ] || s="-$level"
  house_text=${INSTR_HOUSE//@EXECUTOR@/$base-execute$s}
  profile "$home" "$a" "$a" "" "$house_text" || incomplete=1
  profile "$home" "$base-execute$s" "$a" "$repo/agents/executor.md" "$house_text" || incomplete=1
  profile "$home" "$base-gvs5h$s" "$a" "$repo/agents/executor.md" "$house_text

${INSTR_GVS5H//@WORKER@/$base-worker$s}" || incomplete=1
  profile "$home" "$base-worker$s" "$a" "" "$INSTR_WORKER" || incomplete=1
done <<<"$house"
echo "profiles: $(ls "$home/agents" | sed 's/\.toml$//' | tr '\n' ' ')"

[ "$incomplete" -eq 0 ] || { echo "the Vibe link did not complete" >&2; exit 1; }
