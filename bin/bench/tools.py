"""Bench adapters: how to start a tool without an interface, how to answer it and how to read
its steps, in the common form from the spec "tools work like Claude Code", § 5.2-5.3.

A new tool brings a class with the same operations (prepare, start, proceed, steps,
clean) and a function that converts its log to the common form.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import usage  # noqa: E402  cost of the Vibe sessions

LINE_LIMIT = 90 * 60  # seconds for one round of the tool. The bench sets it below the run cap.
# "price limit": Vibe's `--max-price` cap was reached. The run does not count, as with a quota.
QUOTA = re.compile(r"RESOURCE_EXHAUSTED|usage limit|rate limit|price limit", re.I)
# The network or the server failed, not the tool. The round restarts after a pause.
TRANSIENT = re.compile(r"EAI_AGAIN|ECONNRESET|ETIMEDOUT|socket hang up|"
                       r"API Error: (?:Can't reach|Connection|Request timed out|5\d\d|Overloaded)", re.I)
PAUSE = int(os.environ.get("BENCH_PAUSE", "60"))  # seconds between retries. The test sets it to 0.


class QuotaExhausted(Exception):
    """The tool said its quota is used up. The run does not count."""


class Transient(Exception):
    """The network or the server failed in the middle of a round."""


def clean_env():
    # Started from a Claude Code session, a tool would inherit its variables and think it is
    # in the same session. A user starts it from a clean environment.
    return {k: os.environ[k] for k in ("HOME", "PATH", "TERM", "LANG", "USER") if k in os.environ}


def run(cmd, folder, env=None, ndjson=False):
    """Run a tool that writes JSON and return what it wrote. An exhausted quota is a separate exception.

    `env` is added to the clean environment. With `ndjson`, the output is one JSON line per
    entry and comes back as text. A failure shows then only in the exit code."""
    p = subprocess.run(cmd, cwd=folder, env={**clean_env(), **(env or {})}, stdin=subprocess.DEVNULL,
                       capture_output=True, text=True, timeout=LINE_LIMIT + 120)
    try:
        d = {} if ndjson else json.loads(p.stdout)
    except ValueError:
        d = {}
    if p.returncode != 0 or d.get("is_error") or d.get("status", "SUCCESS") != "SUCCESS":
        # Only the end of the output. The skills the model read come before it, and they can quote "price limit".
        everything = p.stdout[-4000:] + p.stderr
        m = QUOTA.search(everything)
        if m:
            raise QuotaExhausted(everything[max(0, m.start() - 80):m.end() + 120].strip())
        if TRANSIENT.search(everything):
            raise Transient(everything.strip()[-300:])
        raise RuntimeError(f"{Path(cmd[0]).name} exited with {p.returncode}: {everything.strip()[-300:]}")
    return p.stdout if ndjson else d


def safe_text(text):
    # A text that starts with "-" would be read as a command-line option.
    return " " + text if text.startswith("-") else text


# The project in the miniature workspace of a run. When a run is judged again, the workspace is
# gone and the given folder is its copy.
BENCH_WORKSPACE = re.compile(r"^/tmp/bench-[0-9a-f]{12}/projects/[^/]+/")


def relative(path, folder):
    folder = str(folder or "")
    if folder and path.startswith(folder.rstrip("/") + "/"):
        return path[len(folder.rstrip("/")) + 1:]
    return BENCH_WORKSPACE.sub("", path)


def step(row, turn, kind, tool="", target="", text=""):
    return {"row": row, "turn": turn, "kind": kind, "tool": tool, "target": target, "text": text}


# ── Antigravity, from the app or from `agy` ───────────────────────────

KIND_AGY = {
    "view_file": ("read", "AbsolutePath"),
    "write_to_file": ("write", "TargetFile"),
    "replace_file_content": ("write", "TargetFile"),
    "multi_replace_file_content": ("write", "TargetFile"),
    "run_command": ("command", "CommandLine"),
    "search_web": ("search", "query"),
    "read_url_content": ("page", "Url"),
    "ask_question": ("question", None),
    "invoke_subagent": ("subagent", None),
}


def steps_agy(log, folder=None):
    """The `transcript_full.jsonl` of an Antigravity conversation, in the common form."""
    steps, r, turn, asked = [], -1, -1, False
    if not Path(log).is_file():
        return steps
    for line in Path(log).read_text(encoding="utf-8").splitlines():
        try:
            p = json.loads(line)
        except ValueError:
            continue
        kind_of_entry = p.get("type")
        # In the app, the user answers ask_question in the window and the answer comes back as a
        # result, `A1: ...`. `agy` in the terminal gets `A1: User Skipped`, which is not the user's.
        # The option label "(Recommended)" belongs to Gemini, not to the user.
        answers = re.findall(r"(?mi)^A\d+: (?:\(recommended\)\s*)?(.*)", p.get("content") or "") if kind_of_entry == "GENERIC" and asked else []
        if answers:
            asked = False
            if answers != ["User Skipped"] * len(answers):
                turn += 1
                steps.append(step(r, turn, "human", text=" | ".join(answers)))
        elif kind_of_entry == "USER_INPUT":
            turn += 1
            text = re.sub(r"(?s)<ADDITIONAL_METADATA>.*|<USER_SETTINGS_CHANGE>.*", "", p.get("content") or "")
            steps.append(step(r, turn, "human", text=re.sub(r"</?USER_REQUEST>", "", text).strip()))
        elif kind_of_entry == "EPHEMERAL_MESSAGE":
            steps.append(step(r, turn, "reminder", text=(p.get("content") or "").strip()))
        elif kind_of_entry == "PLANNER_RESPONSE":
            r += 1
            if (p.get("content") or "").strip():
                steps.append(step(r, turn, "text", text=p["content"].strip()))
            for call in p.get("tool_calls") or []:
                name, args = call.get("name", ""), call.get("args") or {}
                kind, key = KIND_AGY.get(name, ("other", None))
                target, text = str(args.get(key, "")) if key else "", ""
                if name == "ask_question":
                    asked = True
                    text = " | ".join(q.get("question", "") for q in args.get("questions") or [])
                if kind == "read" and target.endswith("/SKILL.md"):
                    kind, target = "skill", target.split("/")[-2]
                steps.append(step(r, turn, kind, name, relative(target, folder), text))
    return steps


class Agy:
    name = "agy"

    def __init__(self, model, effort=None):
        self.model, self.id, self.cost, self.tokens = model, None, None, 0

    def prepare(self, workspace, project):
        # The local files, made by the same function as in the real workspace: the rules of the
        # parent folders, GEMINI.md and the memory index, all from the miniature workspace.
        subprocess.run(["bash", "-c", 'ANTIGRAVITY_FUNCTIONS_ONLY=1 . "$1/bin/antigravity.sh" && local_file "$2" "$1"',
                        "-", str(workspace), str(project)], check=True, capture_output=True)

    def _round(self, project, text):
        cmd = ["agy", "-p", safe_text(text), "--model", self.model, "--dangerously-skip-permissions",
               "--output-format", "json", "--print-timeout", f"{LINE_LIMIT}s"]
        if self.id:
            cmd += ["--conversation", self.id]
        d = run(cmd, project)
        self.id = d.get("conversation_id") or self.id
        self.tokens += (d.get("usage") or {}).get("total_tokens", 0)

    def start(self, project, prompt):
        self._round(project, prompt)

    def proceed(self, project, answer):
        self._round(project, answer)

    def log(self):
        return Path.home() / ".gemini/antigravity-cli/brain" / str(self.id) / ".system_generated/logs/transcript_full.jsonl"

    def steps(self, folder):
        return steps_agy(self.log(), folder) if self.id else []

    def clean(self, output):
        if self.id and self.log().is_file():
            shutil.copy(self.log(), Path(output) / "log.jsonl")


# ── Claude Code ───────────────────────────────────────────────────────

KIND_CLAUDE = {
    "Read": ("read", "file_path"),
    "Write": ("write", "file_path"),
    "Edit": ("write", "file_path"),
    "MultiEdit": ("write", "file_path"),
    "NotebookEdit": ("write", "notebook_path"),
    "Bash": ("command", "command"),
    "WebSearch": ("search", "query"),
    "WebFetch": ("page", "url"),
    "AskUserQuestion": ("question", None),
    "Skill": ("skill", "skill"),
    "Agent": ("subagent", "subagent_type"),
    "Task": ("subagent", "subagent_type"),
}
# User lines that the app wrote, not the user: the output of a local command and the reminders.
NOT_USER = ("<local-command", "<system-reminder", "<task-notification", "<bash-")
# The reminders of the framework, sent by the hook at the end of the response (bin/reminder.py).
# They are not the user's.
REMINDER = re.compile(r"You loaded the \S+ skill without announcing it|Tell the human how much is done, in percent|"
                      r"Framework rule: past two pages, the reader agent does the research|The human asked for the \S+ role")
# The name of the `post_agent` hook written by bin/vibe.sh. Vibe puts it in the `hook_completed` notice.
REMINDER_HOOK = "reminder"
# The answer from the question window comes back as the result of the tool, but it is the user's:
# `... have been answered: "the question"="the answer"`.
WINDOW_ANSWER = re.compile(r'"(?:[^"\\]|\\.)*"="((?:[^"\\]|\\.)*)"')


def steps_claude(log, folder=None):
    """The log of a Claude Code session in the common form. The lines of subagents, of loaded
    skills (`isMeta`) and of summaries are not the user's. The function skips them."""
    steps, responses, turn = [], {}, -1
    if not Path(log).is_file():
        return steps
    for line in Path(log).read_text(encoding="utf-8").splitlines():
        try:
            p = json.loads(line)
        except ValueError:
            continue
        if p.get("isSidechain") or p.get("isCompactSummary"):
            continue
        message = p.get("message") or {}
        content = message.get("content")
        if p.get("isMeta"):
            # The reminder of the framework, from the Stop hook, is a meta line:
            # `Stop hook feedback:\n<the reminder>`. The other meta lines, such as loaded skills,
            # are not the user's.
            m = (REMINDER.search(content) if p.get("type") == "user" and isinstance(content, str)
                 and content.startswith("Stop hook feedback:") else None)
            if m:
                steps.append(step(len(responses) - 1, turn, "reminder", text=m.group(0)))
            continue
        if p.get("type") == "user":
            texts = [content] if isinstance(content, str) else [
                b.get("text", "") for b in content or [] if b.get("type") == "text"]
            for b in content if isinstance(content, list) else []:
                result = b.get("content") if b.get("type") == "tool_result" else None
                if isinstance(result, str) and "have been answered" in result[:80]:
                    texts.append(" | ".join(WINDOW_ANSWER.findall(result)))
            for text in texts:
                if text.strip() and not text.lstrip().startswith(NOT_USER):
                    turn += 1
                    steps.append(step(len(responses) - 1, turn, "human", text=text.strip()))
        elif p.get("type") == "assistant":
            r = responses.setdefault(message.get("id") or p.get("uuid"), len(responses))
            for b in content or []:
                if b.get("type") == "text" and b.get("text", "").strip():
                    steps.append(step(r, turn, "text", text=b["text"].strip()))
                elif b.get("type") == "tool_use":
                    name, args = b.get("name", ""), b.get("input") or {}
                    kind, key = KIND_CLAUDE.get(name, ("other", None))
                    target, text = str(args.get(key, "")) if key else "", ""
                    if name == "AskUserQuestion":
                        text = " | ".join(q.get("question", "") for q in args.get("questions") or [])
                    if kind == "skill":
                        target = target.split(":")[-1]
                    if kind == "subagent":
                        # Without `run_in_background: false`, the app starts the agent in the background.
                        text = "foreground" if args.get("run_in_background") is False else "background"
                    steps.append(step(r, turn, kind, name, relative(target, folder), text))
    return steps


class Claude:
    name = "claude"

    def __init__(self, model, effort=None):
        self.model, self.effort, self.id, self.cost, self.tokens = model, effort, None, None, 0
        self.key = self.workspace = None

    def prepare(self, workspace, project):
        # Memory belongs to the start folder (bin/restore-env.sh). The key of the project in the
        # miniature workspace gets a link to the copy of the memory, as it does in the real one.
        self.key = Path.home() / ".claude/projects" / str(project).replace("/", "-")
        self.key.mkdir(parents=True, exist_ok=True)
        memory = Path(workspace) / "records/memory"
        if memory.is_dir() and not (self.key / "memory").exists():
            (self.key / "memory").symlink_to(memory)
        self.workspace = Path(workspace)

    def _round(self, project, text, session):
        # `auto` does not apply without an interface. Claude falls back to the normal mode and
        # refuses writes (tested 2 October 2026). The open permissions belong to the miniature
        # workspace. `--permission-prompts none` removes the tools that need a person.
        for attempt in range(4):
            cmd = ["claude", "-p", safe_text(text), *session, "--model", self.model,
                   "--permission-mode", "bypassPermissions", "--permission-prompts", "none",
                   "--output-format", "json"]
            if self.effort:
                cmd += ["--effort", self.effort]
            settings = self.workspace / ".claude/settings.json" if self.workspace else None
            if settings and settings.is_file():
                # The workspace of the variant: skills, agents, rules and settings come from the
                # miniature workspace, not from ~/.claude, which belongs to the real workspace.
                cmd += ["--setting-sources", "project,local", "--settings", str(settings), "--add-dir", str(self.workspace)]
            try:
                d = run(cmd, project)
                break
            except Transient:
                if attempt == 3:
                    raise
                time.sleep(PAUSE)
                if self.log().is_file():  # the round had started, so it restarts with what happened
                    text, session = "The connection dropped in the middle of the round. Continue from where you left off.", ["--resume", self.id]
        self.cost = d.get("total_cost_usd", self.cost)

    def start(self, project, prompt):
        self.id = self.id or str(uuid.uuid4())  # the path is chosen beforehand, so it can be read again
        self._round(project, prompt, ["--session-id", self.id])

    def proceed(self, project, answer):
        self._round(project, answer, ["--resume", self.id])

    def log(self):
        path = self.key / f"{self.id}.jsonl" if self.key else Path("/does-not-exist")
        if path.is_file():
            return path
        found = list((Path.home() / ".claude/projects").glob(f"*/{self.id}.jsonl"))
        return found[0] if found else path

    def steps(self, folder):
        return steps_claude(self.log(), folder) if self.id else []

    def clean(self, output):
        j = self.log() if self.id else None
        if j and j.is_file():
            shutil.copy(j, Path(output) / "log.jsonl")
        # The sessions of the bench are not the user's. Their key is removed, so the profile
        # does not count them. ⚠ Only a key of the miniature workspace, never a real one.
        for key in {self.key, j.parent if j else None}:
            if key and key.name.startswith("-tmp-bench-") and key.is_dir():
                shutil.rmtree(key)


# ── Mistral Vibe ──────────────────────────────────────────────────────

# The short name of the tool is the part after the last dot: `file_system.read_file` is `read_file`.
KIND_VIBE = {
    "read_file": ("read", "filePath"),
    "write_file": ("write", "filePath"),
    "search_replace": ("write", "filePath"),
    "edit": ("write", "filePath"),
    "bash": ("command", "command"),
    "start": ("command", "command"),  # `process.start`: where a run longer than 300 s goes
    "web_search": ("search", "query"),
    "open_url": ("page", "url"),
    "web_fetch": ("page", "url"),
    "ask_user_question": ("question", None),
    "task": ("subagent", None),
    "skill": ("skill", "name"),
}
# In the session log, the tools have raw names and arguments (`skill.read`, `path`,
# `file_path`). The `--output streaming` output gives them in normal form (`skill`, `filePath`).
NAME_VIBE = {"skill.read": "skill"}
# With Vibe, the agents of the framework are `vibe --agent <profile>` runs started from the terminal (MISTRAL.md).
AGENT_VIBE = re.compile(r"(?:^|[;&|(]\s*|\s)vibe\s[^;&|]*?--agent[ =]([\w-]+)")
# The agent of the framework, by the name of the Vibe profile: `qwen-agent-execute-medium`, the
# executor on a local model, is still the executor. The thinking level at the end does not change the agent.
ROLE_VIBE = (("execute-fast", "executor"), ("execute", "executor"), ("escalation", "escalation"),
             ("reader", "reader"), ("helper", "helper"), ("worker", "worker"))


def framework_agent(profile):
    base = re.sub(r"-(?:low|medium|high)$", "", profile)
    return next((a for s, a in ROLE_VIBE if base == s or base.endswith("-" + s)), profile)


# A single `&`, not `&&`, `2>&1` or `&>`: the command goes to the background.
BACKGROUND = re.compile(r"(?<![&>|])&(?![&>])|\bnohup\b|\bsetsid\b")


def text_vibe(e):
    return "".join(c.get("text", "") for c in e.get("content") or [] if c.get("type") == "text").strip()


def steps_vibe(log, folder=None):
    """The `--output streaming` output of Vibe, collected from all calls of a run, in the
    common form. A model response (`row`) starts at thinking or at text, after the user or after
    a tool. The tools after it belong to it. An entry with the same `id` is kept once,
    in its last form."""
    if not Path(log).is_file():
        return []
    entries = {}
    for line in Path(log).read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if isinstance(e, dict) and e.get("id"):
            entries[e["id"]] = e
    return steps_from_entries(entries.values(), folder)


def steps_from_entries(entries, folder=None):
    """The entries of a Vibe session, in order, in the common form. They come from the
    `--output streaming` output or from the session log (`bin/reminder.py`), which have the same form."""
    steps, r, turn, last = [], -1, -1, "human"
    for e in entries:
        kind_of_entry = e.get("type")
        d = e.get("detail") or {}
        if kind_of_entry == "notice" and d.get("kind") == "hook_completed" and d.get("hookName") == REMINDER_HOOK:
            # The reminder asked for another response. It is not a user turn, and what follows is a new response.
            steps.append(step(r, turn, "reminder", text=d.get("content") or ""))
            last = "human"
        elif kind_of_entry == "message" and e.get("role") == "user":
            turn += 1
            steps.append(step(r, turn, "human", text=text_vibe(e)))
            last = "human"
        elif kind_of_entry in ("reasoning", "message"):
            if last in ("human", "effect"):
                r += 1
            if kind_of_entry == "message" and text_vibe(e):
                steps.append(step(r, turn, "text", text=text_vibe(e)))
            last = "model"
        elif kind_of_entry == "effect":
            if last == "human":  # a tool with no thinking and no text before it is also a new response
                r += 1
            name, args = d.get("toolName", ""), d.get("input") or {}
            name = NAME_VIBE.get(name, name)
            kind, key = KIND_VIBE.get(name.rsplit(".", 1)[-1], ("other", None))
            target = str(args.get(key) or args.get("path") or args.get("file_path") or "") if key else ""
            text = ""
            if kind == "question":
                text = " | ".join(q.get("question", "") for q in args.get("questions") or [])
            m = AGENT_VIBE.search(target) if kind == "command" else None
            if m:
                kind, text = "subagent", "background" if BACKGROUND.search(target) else "foreground"
                target = framework_agent(m.group(1))
            steps.append(step(r, turn, kind, name, relative(target, folder), text))
            last = "effect"
    return steps


class Vibe:
    name = "vibe"

    def __init__(self, model, effort=None):
        # `model` is the profile in $VIBE_HOME/agents/, which fixes the model and the thinking. With
        # an effort, the profile is `<model>-<effort>`: the alias by level of a local model, written by bin/vibe.sh.
        self.level = effort not in (None, "", "off", "none")
        if self.level:
            model = f"{model}-{effort}"
        self.model, self.id, self.cost, self.tokens, self.home = model, None, None, 0, None

    def prepare(self, workspace, project):
        # A VIBE_HOME of the miniature workspace, written by its bin/vibe.sh: the rules, the profiles
        # and the skills of the workspace, with its trust root. The login is in the key wallet of
        # the system, so a new VIBE_HOME finds it. The clones of the plugins may be missing. Then
        # the script exits with 1, but the global file is written.
        self.home = Path(workspace) / ".vibe"
        subprocess.run(["bash", str(Path(workspace) / "bin/vibe.sh")], env={**os.environ, "VIBE_HOME": str(self.home)},
                       capture_output=True)
        if not (self.home / "AGENTS.md").is_file():
            raise RuntimeError("bin/vibe.sh did not write AGENTS.md in the miniature workspace")
        if self.level and not (self.home / "agents" / f"{self.model}.toml").is_file():
            raise RuntimeError(f"the profile {self.model} is missing from the miniature workspace. The model is "
                               "not in the user's ~/.vibe/config.toml, or it has no such level.")
        exclude = Path(workspace) / ".git/info/exclude"
        if exclude.parent.is_dir() and "/.vibe/" not in (exclude.read_text() if exclude.is_file() else ""):
            with exclude.open("a", encoding="utf-8") as f:
                f.write("/.vibe/\n")

    def log(self):
        """The output of all calls of the run, in lines. `id` is the key of the bench, not of Vibe."""
        return self.home / f"bench-{self.id}.jsonl" if self.home and self.id else Path("/does-not-exist")

    def session(self):
        """The Vibe session id, from the first line of the log that has it."""
        if not self.log().is_file():
            return None
        for line in self.log().read_text(encoding="utf-8").splitlines():
            try:
                sid = json.loads(line).get("sessionId")
            except (ValueError, AttributeError):
                continue
            if sid:
                return sid
        return None

    def _round(self, project, text):
        cmd = ["vibe", "--agent", self.model, "-p", safe_text(text), "--output", "streaming",
               "--auto-approve", "--trust", "--max-price", os.environ.get("BENCH_VIBE_CAP", "3")]
        sid = self.session()
        if sid:
            cmd += ["--resume", sid]
        # The key wallet, with the login of Vibe, opens through the session bus.
        # VIBE_CLI=python: the Rust TUI of vibe 2.26 refuses `-p` with `--resume`, and the second round needs both.
        env = {"VIBE_HOME": str(self.home), "VIBE_CLI": "python",
               **{k: os.environ[k] for k in ("DBUS_SESSION_BUS_ADDRESS", "XDG_RUNTIME_DIR") if k in os.environ}}
        output = run(cmd, project, env=env, ndjson=True)
        with self.log().open("a", encoding="utf-8") as f:
            f.write(output if not output or output.endswith("\n") else output + "\n")
        # All sessions in the VIBE_HOME of the workspace. A run has only one. On the way, the
        # bench subtracts what the earlier sessions cost.
        sessions = usage.vibe_sessions(self.home)
        self.cost = round(sum(s["usd"] or 0 for s in sessions), 4)
        self.tokens = sum(s["input"] + s["cache"] + s["output"] for s in sessions)

    def start(self, project, prompt):
        self.id = self.id or uuid.uuid4().hex
        self._round(project, prompt)

    def proceed(self, project, answer):
        self._round(project, answer)

    def steps(self, folder):
        return steps_vibe(self.log(), folder) if self.id else []

    def clean(self, output):
        # The VIBE_HOME of the run is in the miniature workspace and leaves with it.
        if self.log().is_file():
            shutil.copy(self.log(), Path(output) / "log.jsonl")


TOOLS = {"agy": Agy, "claude": Claude, "vibe": Vibe}
STEPS = {"agy": steps_agy, "claude": steps_claude, "vibe": steps_vibe}
