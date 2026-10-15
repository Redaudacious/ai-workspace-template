#!/usr/bin/env python3
"""The bench: the same task given to any AI coding tool, in a miniature house (a throwaway
copy of the workspace), with a simulated human who answers its questions. What the tool did
is read from its log and passed through the checks.

  bench.py run --tool agy|claude|vibe --model <id> [--effort <e>] --task <folder|name from bin/bench/tasks> --output <folder> [--reference <run>] [--minutes <n>] [--manners] [--same-model]
  bench.py read --tool agy|claude|vibe --log <log.jsonl> --stage spec|plans|execute|search [--folder <folder>] [--task <folder>]
  bench.py profile --after <YYYY-MM-DD> --output <file>
  bench.py journey --project <folder> --output <folder> [--tool claude|vibe] [--variant <framework>] [--note <file>] [--label <l>] [--model <m>] [--effort <e>] [--sessions <n>] [--minutes <n>] [--budget <$>] [--manners] [--same-model]
  bench.py journey --resume <the journey's folder>
  bench.py blind --a <journey> --b <journey> --output <folder> --key <file>

Exit codes of `run`: 0, the run ended, however the checks came out; 3, the tool's quota
ran out and the run does not count; 4, something changed outside the miniature house; 1,
another error.

Exit codes of `journey`: 0, the journey ended, however the acceptance came out; 3, the
quota ran out; 1, another error. On 3 and on 1, the miniature house stays, and `--resume`
continues.
"""
import argparse
import collections
import datetime
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(1, str(Path(__file__).resolve().parents[1]))
import usage  # noqa: E402
import tools  # noqa: E402
import checks  # noqa: E402

# The workspace root; the test moves it to a fabricated space.
ROOT = Path(os.environ.get("BENCH_ROOT") or Path(__file__).resolve().parents[2])
MAX_ANSWERS = 30
MARK = {True: "✓", False: "✗", None: "–"}

HUMAN_SYSTEM = """You play the human who gave a task to a coding agent. You receive the agent's last message and answer exactly as the human would: short, in English.

- To a question with options, pick the option the agent recommends, unless the brief asks for another, and write its number.
- To a request for approval, write "yes", unless the brief asks for something else.
- To a question of fact, answer from the brief. Where the brief says nothing, answer like a human who wants something simple.
- If the agent stopped without asking anything and did not finish, write "continue".
- If the agent finished, that is, it gave the final report or the prompt of the next session and waits for nothing more from you, write exactly DONE.

Do not write code, do not give new requirements, do not explain. Write only the answer.

Brief:
"""


# ── the simulated human ───────────────────────────────────────────────

def human_answers(brief, message):
    # `--safe-mode` keeps the house's hooks and plugins out, `--system-prompt` replaces
    # Claude Code's large prompt: a call costs little and does not touch the Gemini quota.
    d = tools.run(["claude", "-p", "The agent's message:\n\n" + (message or "(wrote nothing in the chat)"),
                   "--safe-mode", "--system-prompt", HUMAN_SYSTEM + brief, "--no-session-persistence",
                   "--tools", "", "--model", "sonnet", "--output-format", "json"], "/tmp")
    return (d.get("result") or "").strip()


def last_message(steps):
    t = checks.turns(steps)
    texts = [p["text"] for p in (t[-1] if t else []) if p["kind"] == "text"]
    return "\n\n".join(texts[-3:])[-6000:]


# ── the miniature house ───────────────────────────────────────────────

def git(folder, *args):
    subprocess.run(["git", "-C", str(folder), *args], check=True, capture_output=True)


def new_repo(folder):
    # The test identity sits only on the commit command (AGENTS.md, "Commits carry the
    # human's identity"): `git config` would write it into the repository's configuration.
    # `main`, as in the house: a new repository would otherwise get the name git picks, here `master`.
    git(folder, "init", "-q", "-b", "main")
    git(folder, "add", "-A")
    git(folder, "-c", "user.name=bench", "-c", "user.email=bench@local", "commit", "-q", "--allow-empty", "-m", "Start of the trial")


def variant_house(space, variant, note):
    """The `.claude/` of the miniature house: the variant's skills and agents, the human's rules,
    the variant's note and its settings. Claude Code reads them from here, not from ~/.claude:
    the adapter starts the session with `--setting-sources project,local`."""
    c = space / ".claude"
    for d in ("skills", "agents", "rules"):
        (c / d).mkdir(parents=True, exist_ok=True)
    for sk in sorted((variant / "skills").iterdir()):
        if (sk / "SKILL.md").is_file():
            shutil.copytree(sk, c / "skills" / sk.name)
    for ag in sorted((variant / "agents").glob("*.md")):
        shutil.copy(ag, c / "agents" / ag.name)
    home = Path.home() / ".claude"
    for r in sorted((home / "rules").glob("*.md")):
        shutil.copy(r, c / "rules" / r.name)
    if (home / "CLAUDE.md").is_file():
        # An import on its own line, like `@file.md`, is expanded: in the copy, the file would not sit next to it.
        text = re.sub(r"(?m)^@(\S+)[ \t]*$", lambda m: (home / m.group(1)).read_text(encoding="utf-8")
                      if (home / m.group(1)).is_file() else m.group(0), (home / "CLAUDE.md").read_text(encoding="utf-8"))
        (c / "rules/personal.md").write_text(text, encoding="utf-8")
    if note:
        shutil.copy(note, c / "rules/variant-note.md")
    # The variant's own tool writes the settings, in an empty HOME: what the tool changes gets in too.
    lock, tool = variant / "plugins.lock.json", variant / "bin/merge-claude-config.py"
    if lock.is_file() and tool.is_file():
        with tempfile.TemporaryDirectory() as h:
            subprocess.run([sys.executable, str(tool), str(lock), h], check=True, capture_output=True)
            shutil.copy(Path(h) / ".claude/settings.json", c / "settings.json")
    else:
        (c / "settings.json").write_text("{}\n", encoding="utf-8")


def miniature_house(task_dir, task, variant=None, note=None):
    """A copy of the workspace: the framework comes from the given variant (by default the root),
    the personal layer from the root."""
    variant = Path(variant or ROOT)
    # No dots in the path: the key of Claude Code's memory is made from it.
    space = Path(f"/tmp/bench-{uuid.uuid4().hex[:12]}")
    space.mkdir()
    # `bin/vibe.sh` reads `MISTRAL.md`, the lockfile and `agents/`, and writes the house's VIBE_HOME.
    for f in ("AGENTS.md", "CLAUDE.md", "GEMINI.md", "MISTRAL.md", ".gitignore", "plugins.lock.json"):
        if (variant / f).is_file():
            shutil.copy2(variant / f, space / f)
    for d in ("bin", "skills", "agents"):
        (space / d).symlink_to(variant / d)
    shutil.copytree(variant / "template/records", space / "records")
    # The house rules and the memory are copied, so that what a tool writes stays inside.
    # The local workers file exists, with no worker: execution gives the bridge no task, and the
    # tool does not look for the human's own file, which would send it to their machines.
    (space / "records/local-workers.md").write_text(
        "# Local workers\n\n## The workers\n\nNone: in the bench house, tasks run in the session.\n",
        encoding="utf-8")
    if (ROOT / "records/house-rules.md").is_file():
        shutil.copy2(ROOT / "records/house-rules.md", space / "records/house-rules.md")
    if (ROOT / "records/memory").is_dir():
        shutil.copytree(ROOT / "records/memory", space / "records/memory", symlinks=True)
    variant_house(space, variant, note)
    new_repo(space)
    project = space / "projects" / task["project"]
    for layer in task.get("layers", ["template"]):
        shutil.copytree(variant / layer, project, dirs_exist_ok=True, symlinks=True)
    if (task_dir / "project").is_dir():
        shutil.copytree(task_dir / "project", project, dirs_exist_ok=True, symlinks=True)
    project.mkdir(parents=True, exist_ok=True)
    new_repo(project)
    return space, project


# ── the fingerprint of the real repositories ──────────────────────────

def repos():
    found, base = [], str(ROOT).count(os.sep)
    for d, sub, files in os.walk(ROOT):
        if ".git" in sub or ".git" in files:
            found.append(d)
        sub[:] = [] if d.count(os.sep) - base >= 4 else [
            s for s in sub if s not in (".git", "node_modules", ".venv", "__pycache__")]
    return sorted(found)


# Where an installation that escaped the miniature house ends up: the tool runs with the human's home.
# Only the names inside are compared, because other programs rewrite the files there at any time.
HOME_PLACES = ("~/.config/systemd/user", "~/.local/bin", "~/opt", "~/.local/state")


# The panel rewrites the weekly file in `records/` once a minute, while any chat of the human
# works: a long run would find it changed through no fault of the tool.
NOT_IN_FINGERPRINT = ":(exclude)usage/weeks"


def fingerprint():
    """The state of every repository in the workspace, by content, as in bin/tool-bridge.sh,
    plus the human's crontab and the places of an installation in the home."""
    states = {}
    for d in repos():
        h = hashlib.sha256()
        for args in (("status", "--porcelain", "-uall"), ("diff", "HEAD", "--binary", "--no-color", "--no-ext-diff")):
            h.update(subprocess.run(["git", "-C", d, "-c", "core.quotePath=false", *args, "--", ".", NOT_IN_FINGERPRINT],
                                    capture_output=True).stdout)
        states[d] = h.hexdigest()
    if shutil.which("crontab"):
        states["crontab"] = hashlib.sha256(subprocess.run(["crontab", "-l"], capture_output=True).stdout).hexdigest()
    for place in HOME_PLACES:
        d = Path(place).expanduser()
        states[place] = "\n".join(sorted(os.listdir(d))) if d.is_dir() else ""
    return states


def changed(before, after):
    return sorted(d for d in set(before) | set(after) if before.get(d) != after.get(d))


# ── the report ────────────────────────────────────────────────────────

def cell(text):
    # The tool's text is quoted, not followed: a link in it, for instance to the house in
    # /tmp, would break with the house, and check-docs would fail on the report.
    return str(text).replace("\n", " ").replace("|", "\\|").replace("](", "]\\(")


def artifacts(folder, steps):
    """What the tool wrote in the work item's folder, read from the project at the end, plus the commits."""
    out = []
    for c in sorted({p["target"] for p in steps if p["kind"] == "write" and checks.in_work_folder(p["target"])}):
        text = checks.read_file(c, folder)
        if text is not None:
            out += [f"<details><summary><code>{c}</code>, {len(text.splitlines())} lines</summary>", "",
                    "`````markdown", text.rstrip(), "`````", "", "</details>", ""]
    log = subprocess.run(["git", "-C", str(folder), "log", "--all", "--oneline", "--decorate"],
                         capture_output=True, text=True).stdout.strip()
    return (out or ["Nothing in the work item's folder.", ""]) + ["Commits:", "", "```text", log or "(none)", "```"]


def money(x, currency):
    return f"{currency}{x:.2f}"


def cost_label(tool, usd):
    """What is paid, said plainly: with Vibe, estimated euros from the month's Vibe Code amount; with a
    house model, through Vibe, €0; with the others, dollars at the API price, which are not paid but
    reduce the subscription's quota."""
    if usd is None:
        return "cost: —"
    if tool == "vibe" and usd == 0:
        return f"house model: {money(0, '€')}, no Vibe Code amount"
    if tool == "vibe":
        return f"from the Vibe Code amount: {money(usd * usage.EUR_PER_USD, '€')} estimated"
    return f"equivalent at the API price: {money(usd, '$')} — not paid, it reduces the subscription's quota"


def write_report(output, meta, results, steps, reference):
    r = [f"# {meta['tool']} · {meta['model']} · {meta['task']}", "",
         f"{meta['date']} · {meta['duration_s'] // 60} min · {meta['answers']} answers of the simulated human · "
         f"{cost_label(meta['tool'], meta['cost'])} · tokens: {meta['tokens'] or '—'} · ended: {cell(meta['reason'])}", "",
         f"**Threshold:** {'passed' if meta['threshold'] else 'not passed'}.", "",
         f"**Manners:** {'required' if meta.get('manners') else 'informational'}.", "",
         "## The checks", "", "| | check | required | reason |", "|---|---|---|---|"]
    r += [f"| {MARK[v['state']]} | `{v['name']}` | {'yes' if v['required'] else 'no'} | {cell(v['reason'])} |"
          for v in results]
    r += ["", "## What it wrote", ""] + artifacts(output / "project", steps)
    if reference:
        rp = Path(reference)
        reference_steps = [json.loads(x) for x in (rp / "steps.jsonl").read_text(encoding="utf-8").splitlines()]
        r += ["", f"## What the reference wrote, {rp.name}", ""] + artifacts(rp / "project", reference_steps)
    r += ["", "## The steps", "", "| row | turn | kind | target or text |", "|---|---|---|---|"]
    r += [f"| {p['row']} | {p['turn']} | {p['kind']} | {cell((p['target'] or p['text'])[:120])} |" for p in steps]
    (output / "report.md").write_text("\n".join(r) + "\n", encoding="utf-8")


# ── the commands ──────────────────────────────────────────────────────

def task_ctx(s, folder):
    """What the checks read from task.json: the web search, the new request, the plan, the helper, the answer, the probe."""
    return {"folder": folder, **{k: s.get(k) for k in ("web_search", "new_request", "plan", "plan_with_code",
                                                       "helper", "answer", "probe")}}


def run(a):
    task_dir = Path(a.task).resolve()
    # A name without a folder is a bench task, from bin/bench/tasks/: so another repository can call it by name.
    if not task_dir.is_dir() and (Path(__file__).resolve().parent / "tasks" / a.task).is_dir():
        task_dir = Path(__file__).resolve().parent / "tasks" / a.task
    task = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
    brief = (task_dir / "brief.md").read_text(encoding="utf-8")
    tool = tools.TOOLS[a.tool](a.model, a.effort)
    # A single line of the tool can last as long as the whole run: a plans session works
    # for tens of minutes without asking anything.
    tools.LINE_LIMIT = a.minutes * 60
    before = fingerprint()
    space, project = miniature_house(task_dir, task)
    try:
        return the_run(a, task_dir, task, brief, tool, before, space, project)
    finally:  # the miniature house leaves on any exit, even on a failure of the bench
        shutil.rmtree(space, ignore_errors=True)


def the_run(a, task_dir, task, brief, tool, before, space, project):
    start, human, reason, code = time.time(), [], "done", 0
    try:
        tool.prepare(space, project)
        tool.start(project, task["prompt"])
        while True:
            if len(human) >= MAX_ANSWERS:
                reason = "the cap on answers"
                break
            if time.time() - start > a.minutes * 60:
                reason = "the cap on time"
                break
            message = last_message(tool.steps(project))
            answer = human_answers(brief, message)
            human.append({"message": message, "answer": answer})
            if answer == "DONE":
                break
            tool.proceed(project, answer)
    except tools.QuotaExhausted as e:
        reason, code = f"quota: {e}", 3
    except Exception as e:  # the run stops, but the report is written anyway
        reason, code = f"error: {e}", 1
    duration = round(time.time() - start)
    # The fingerprint is taken before any write to the output, which can sit in a repository of the house.
    outside = changed(before, fingerprint())
    if outside:  # the reason for a failure stays next to code 4: otherwise it would be lost without a trace
        reason, code = "changes outside the miniature house: " + ", ".join(outside) + ("" if reason == "done" else f"; {reason}"), 4
    steps = tool.steps(project)
    base = Path(a.output).resolve() / f"{datetime.datetime.now():%Y-%m-%d-%H%M}-{tool.name}-{task_dir.name}"
    output, n = base, 1
    while output.exists():  # two runs in the same minute do not overwrite each other
        n += 1
        output = base.with_name(f"{base.name}-{n}")
    output.mkdir(parents=True)
    tool.clean(output)
    shutil.copytree(project, output / "project", symlinks=True)
    # task.json stays next to the run: re-judging takes it from here, even if the task's folder was temporary.
    shutil.copy(task_dir / "task.json", output / "task.json")
    ctx = task_ctx(task, output / "project")
    results = checks.check(steps, task["stage"], ctx, a.manners)
    meta = {"tool": tool.name, "model": a.model, "effort": a.effort, "task": task_dir.name, "manners": a.manners,
            "stage": task["stage"], "date": datetime.datetime.now().isoformat(timespec="minutes"),
            "duration_s": duration, "answers": sum(o["answer"] != "DONE" for o in human),
            "cost": tool.cost, "tokens": tool.tokens, "reason": reason, "code": code, "threshold": code == 0 and checks.threshold(results),
            "checks": {v["name"]: v["state"] for v in results}}
    if tool.name == "vibe":
        meta["eur_estimated"] = None if tool.cost is None else round(tool.cost * usage.EUR_PER_USD, 4)
    (output / "steps.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in steps), encoding="utf-8")
    (output / "human.jsonl").write_text("".join(json.dumps(o, ensure_ascii=False) + "\n" for o in human), encoding="utf-8")
    (output / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(output, meta, results, steps, a.reference)
    print(f"{output}: {reason}; threshold {'passed' if meta['threshold'] else 'not passed'}")
    return code


def read(a):
    steps = tools.STEPS[a.tool](a.log, a.folder)
    ctx = {"folder": a.folder}
    if a.task:  # re-judging a bench run: the task's folder, or the run's, which holds task.json
        ctx = task_ctx(json.loads((Path(a.task) / "task.json").read_text(encoding="utf-8")), a.folder)
    results = checks.check(steps, a.stage, ctx)
    for v in results:
        print(f"{MARK[v['state']]} {v['name']}{'' if v['required'] else ' (informational)'}: {v['reason']}")
    print(f"threshold: {'passed' if checks.threshold(results) else 'not passed'}")
    return 0


KINDS = (("execute", {"execute", "executing-plans"}), ("plans", {"writing-plans"}), ("spec", {"brainstorming"}))


def bounds(log):
    """The first and the last date of a session, plus its starting folder."""
    dates, folder = [], None
    for line in log.open(encoding="utf-8", errors="replace"):
        try:
            p = json.loads(line)
        except ValueError:
            continue
        if p.get("timestamp"):
            dates.append(p["timestamp"])
            folder = folder or p.get("cwd")
    return (min(dates), max(dates), folder) if dates else (None, None, None)


def minutes_between(start, end):
    t = [datetime.datetime.fromisoformat(x.replace("Z", "+00:00")) for x in (start, end)]
    return round((t[1] - t[0]).total_seconds() / 60)


def profile(a):
    seen, by_kind = set(), {}
    logs = sorted((Path.home() / ".claude/projects").glob("*/*.jsonl"), key=lambda j: j.stat().st_size, reverse=True)
    for j in logs:
        # The same session can sit under the key from before and from after the space was moved;
        # a bench session, left over after a failure, is not the human's.
        if j.name in seen or j.parent.name.startswith("-tmp-bench-"):
            continue
        seen.add(j.name)
        start, end, folder = bounds(j)
        if not start or start[:10] < a.after:
            continue
        steps = tools.steps_claude(j, folder)
        called = {p["target"] for p in steps if p["kind"] == "skill"}
        kind = next((f for f, s in KINDS if called & s), None)
        if kind:
            results = checks.check(steps, kind, {"folder": folder})
            by_kind.setdefault(kind, []).append((j, steps, results, minutes_between(start, end)))
    r = [f"# Profile of Claude Code, from the logs since {a.after}", "",
         "Produced with `bin/bench/bench.py profile`; the kind of session comes from the skills called in it.", ""]
    for kind, sessions in sorted(by_kind.items()):
        r += [f"## {kind}: {len(sessions)} sessions", "",
              "| check | required | passed | applicable | % |", "|---|---|---|---|---|"]
        for v in sessions[0][2]:
            states = [next(x["state"] for x in results if x["name"] == v["name"]) for _, _, results, _ in sessions]
            yes, applicable = states.count(True), sum(s is not None for s in states)
            r.append(f"| `{v['name']}` | {'yes' if v['required'] else 'no'} | {yes} | {applicable} | "
                     f"{round(100 * yes / applicable) if applicable else '—'} |")
        r += ["", "The sessions, with the questions, the searches, the steps up to the first change, the minutes and what they failed:", ""]
        for j, steps, results, m in sessions:
            first = checks.first_change(steps)
            failed = [v["name"] for v in results if v["state"] is False]
            r.append(f"- `{j}`: {sum(checks.asks(t) for t in checks.turns(steps))} "
                     f"questions, {sum(p['kind'] in ('search', 'page') for p in steps)} searches, "
                     f"{first if first is not None else len(steps)} steps up to the first change, {m} minutes; "
                     f"failed: {', '.join(failed) or 'none'}")
        r.append("")
    Path(a.output).write_text("\n".join(r), encoding="utf-8")
    print(f"{a.output}: " + (", ".join(f"{f} {len(s)}" for f, s in sorted(by_kind.items())) or "no session"))
    return 0


# ── the whole journey ─────────────────────────────────────────────────

HANDOFF_SYSTEM = """You read the end of a work session and its state file, STATE.md, and you say what new session the human would open after it, exactly as written there: its role, the tier, the thinking level and the prompt to paste, word for word.

- The role is one of spec, plans, execute, review, orchestration. The execution of a plan is execute.
- The model is opus or sonnet, by the tier written: the large tier is opus, the medium tier is sonnet. An old state file writes Opus or Sonnet: Opus is opus, Sonnet is sonnet.
- The effort is the thinking level written, for example high for "thinking `high`".
- If the end or the state file says that no session follows, or that the work item is finished, next is false.
- The end of the session comes first: the state file can be left over from an older session."""

HANDOFF_SCHEMA = {"type": "object", "required": ["next"], "properties": {
    "next": {"type": "boolean"},
    "role": {"type": "string", "enum": ["spec", "plans", "execute", "review", "orchestration"]},
    "model": {"type": "string", "enum": ["opus", "sonnet"]},
    "effort": {"type": "string", "enum": ["low", "medium", "high", "xhigh", "max"]},
    "prompt": {"type": "string"}}}


def handoff(message, state_md):
    """The next session, read like a human: from the end of the session and from the handoff in STATE.md."""
    i = max(state_md.find("The next session"), 0)
    d = tools.run(["claude", "-p", f"The end of the session:\n\n{message}\n\nSTATE.md:\n\n{state_md[i:][:8000]}",
                   "--safe-mode", "--system-prompt", HANDOFF_SYSTEM, "--no-session-persistence", "--tools", "",
                   "--model", "sonnet", "--output-format", "json", "--json-schema", json.dumps(HANDOFF_SCHEMA)], "/tmp")
    p = d.get("structured_output") or {}
    if p.get("next") and not all(p.get(k) for k in ("role", "model", "prompt")):
        return {"next": False, "reason": "handoff without a role, a model or a prompt: " + json.dumps(p, ensure_ascii=False)}
    return p


def one_session(tool, project, brief, prompt, human, start, minutes, resumed):
    """One session with the simulated human, until DONE or a cap; returns the reason it ended."""
    if resumed:
        tool.proceed(project, "The session was interrupted; continue where you left off.")
    else:
        tool.start(project, prompt)
    while True:
        if len(human) >= MAX_ANSWERS:
            return "the cap on answers"
        if time.time() - start > minutes * 60:
            return "the cap on time"
        message = last_message(tool.steps(project))
        answer = human_answers(brief, message)
        human.append({"message": message, "answer": answer})
        if answer == "DONE":
            return "done"
        tool.proceed(project, answer)


def keep_logs(tool, folder):
    """The session's log and its agents' logs, with the type of each, in the session's folder."""
    folder.mkdir(parents=True, exist_ok=True)
    j = tool.log()
    if j.is_file():
        shutil.copy(j, folder / "log.jsonl")
        if (j.parent / j.stem / "subagents").is_dir():
            shutil.copytree(j.parent / j.stem / "subagents", folder / "agents", dirs_exist_ok=True)


def count_tokens(f):
    """The tokens of a log: input, from the cache and output; an answer is counted once."""
    seen, n = set(), 0
    for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        m = r.get("message") or {}
        if r.get("type") == "assistant" and m.get("usage") and m.get("id") not in seen:
            seen.add(m.get("id"))
            n += sum(m["usage"].get(k, 0) for k in ("input_tokens", "cache_read_input_tokens",
                                                     "cache_creation_input_tokens", "output_tokens"))
    return n


def figures(folder):
    """The equivalent at the API price, in dollars, with the prices from bin/usage.py, the steps and the tokens: of the
    session and of its agents. Copied here, the agents' logs no longer sit under the session's, so
    they are not counted twice."""
    cost, steps, n = 0.0, 0, 0
    for f in [folder / "log.jsonl", *sorted((folder / "agents").glob("agent-*.jsonl"))]:
        if f.is_file():
            c = usage.session(f)[1]
            cost, steps, n = cost + usage.total_of(c), steps + c["steps"], n + count_tokens(f)
    return round(cost, 4), steps, n


def acceptance(pdir, project):
    """The project's acceptance probes, hidden from the agents, on the `main` at the end."""
    arch = subprocess.run(["git", "-C", str(project), "archive", "main"], capture_output=True)
    if arch.returncode:
        return {"code": None, "output": "the project has no main: " + arch.stderr.decode(errors="replace")[-300:]}
    with tempfile.TemporaryDirectory() as t:
        subprocess.run(["tar", "-x", "-C", t], input=arch.stdout, check=True)
        r = subprocess.run([sys.executable, str(pdir / "acceptance/probe.py"), t], cwd=t,
                           capture_output=True, text=True, timeout=900)
    return {"code": r.returncode, "output": (r.stdout + r.stderr)[-4000:]}


def write_state(output, st):
    (output / "journey.json").write_text(json.dumps(st, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def journey_report(output, st):
    a = st["acceptance"]
    vibe = st.get("tool") == "vibe"
    r = [f"# Journey {st['label']} · {Path(st['trial_project']).name}", "",
         f"State: {cell(st['state'])} · {cost_label(st.get('tool', 'claude'), st['cost'])} · "
         f"tokens: {st['tokens']} · escalations: {st['escalations']} · "
         f"returns: {st['returns']} · acceptance: {'passed' if a['code'] == 0 else 'failed'} · "
         f"manners: {'passed' if st.get('manners_passed', True) else 'failed'}{'' if st.get('manners') else ' (informational)'}", "",
         "| nr | role | model | effort | minutes | answers | steps | tokens | agents | cost | manners failed | ended |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    r += [f"| {x['nr']} | {x['role']} | {x['model']} | {x['effort'] or '—'} | {x['duration_s'] // 60} | {x['answers']} | "
          f"{x['steps']} | {x['tokens']} | {cell(', '.join(f'{k} {v}' for k, v in x['agents'].items()) or '—')} | {money(x['cost'] * usage.EUR_PER_USD, '€') + ' estimated' if vibe else money(x['cost'], '$')} | "
          f"{cell(', '.join(k for k, v in x.get('manners', {}).items() if v is False) or '—')} | {cell(x['reason'])} |"
          for x in st["sessions"]]
    r += ["", "## The acceptance", "", "```text", a["output"].rstrip(), "```"]
    (output / "report.md").write_text("\n".join(r) + "\n", encoding="utf-8")


# The Vibe profile of the role in the handoff; a review, which is no longer a session of the house, would
# run as execution.
VIBE_PROFILE = {"spec": "spec", "plans": "plans", "orchestration": "orchestration", "execute": "execute"}


def journey(a):
    if a.resume:
        output = Path(a.resume).resolve()
        st = json.loads((output / "journey.json").read_text(encoding="utf-8"))
    else:
        if not (a.project and a.output):
            raise SystemExit("journey: --project and --output, or --resume")
        pdir, variant = Path(a.project).resolve(), Path(a.variant or ROOT).resolve()
        p = json.loads((pdir / "project.json").read_text(encoding="utf-8"))
        note = Path(a.note).resolve() if a.note else None
        space, project = miniature_house(pdir, {"project": p["name"], "layers": p.get("layers", ["template"])}, variant, note)
        label = a.label or variant.name
        base = Path(a.output).resolve() / f"{datetime.datetime.now():%Y-%m-%d-%H%M}-{label}-{p['name']}"
        output, n = base, 1
        while output.exists():
            n += 1
            output = base.with_name(f"{base.name}-{n}")
        output.mkdir(parents=True)
        st = {"label": label, "tool": a.tool, "variant": str(variant), "note": str(note) if note else None,
              "trial_project": str(pdir), "space": str(space), "project": str(project), "sessions_max": a.sessions,
              "minutes": a.minutes, "budget": a.budget, "manners": a.manners,
              # A house model, with Vibe, takes all the roles; Claude takes its model from the handoff.
              "house_model": a.model if a.tool == "vibe" and a.model not in ("opus", "sonnet") else None,
              "house_effort": a.effort if a.tool == "vibe" and a.model not in ("opus", "sonnet") else None,
              # Claude, on a single model: every session on --model and --effort, whatever the handoff asks.
              "same_model": a.model if a.same_model and a.tool == "claude" else None,
              "same_effort": a.effort if a.same_model and a.tool == "claude" else None,
              "state": "in progress", "sessions": [], "current": None,
              "next": {"role": "spec", "model": a.model, "effort": a.effort, "prompt": p["request"]}}
    pdir, space, project = Path(st["trial_project"]), Path(st["space"]), Path(st["project"])
    brief = (pdir / "brief.md").read_text(encoding="utf-8")
    tools.LINE_LIMIT = st["minutes"] * 60
    st["state"] = "in progress"
    while st["current"] or (st["next"] and len(st["sessions"]) < st["sessions_max"]):
        if sum(x["cost"] for x in st["sessions"]) > st["budget"]:
            st["state"] = f"the budget of {st['budget']} $, exceeded"
            break
        if not st["current"]:
            st["current"] = {**st["next"], "nr": len(st["sessions"]) + 1, "id": str(uuid.uuid4()), "start": time.time()}
        c = st["current"]
        write_state(output, st)
        vibe = st.get("tool") == "vibe"
        model = VIBE_PROFILE.get(c["role"], "execute") if vibe else c["model"]
        effort = None if vibe else c.get("effort")
        if not vibe and st.get("same_model"):
            model, effort = st["same_model"], st.get("same_effort")
        if vibe and st.get("house_model"):
            # The profile of the alias per level, written by bin/vibe.sh; execution, on the executor of the same model.
            model = st["house_model"] + ("-execute" if model == "execute" else "")
            effort = st.get("house_effort")
        tool = tools.TOOLS[st.get("tool", "claude")](model, effort)
        if vibe:
            model = tool.model  # with the level attached, as Vibe asks
        tool.prepare(space, project)
        tool.id = c["id"]
        human, code, before = [], 0, fingerprint()
        try:
            reason = one_session(tool, project, brief, c["prompt"], human, c["start"], st["minutes"], tool.log().is_file())
        except tools.QuotaExhausted as e:
            reason, code = f"quota: {e}", 3
        except Exception as e:  # the journey stops, and the house stays for --resume
            reason, code = f"error: {e}", 1
        folder = output / "sessions" / f"{c['nr']:02d}-{c['role']}"
        keep_logs(tool, folder)
        with (folder / "human.jsonl").open("a", encoding="utf-8") as fo:
            fo.write("".join(json.dumps(o, ensure_ascii=False) + "\n" for o in human))
        if code:
            st["state"] = "quota" if code == 3 else reason
            write_state(output, st)
            print(f"{output}: {reason}; the house stays in {space}, for --resume")
            return code
        if vibe:
            # The journey's sessions share the house's VIBE_HOME, with the agents started from the terminal with
            # everything: the session's cost and tokens are what was added since the one before.
            pv = tool.steps(project)
            cost = round((tool.cost or 0) - sum(x["cost"] for x in st["sessions"]), 4)
            n = tool.tokens - sum(x["tokens"] for x in st["sessions"])
            steps = len({p["row"] for p in pv if p["kind"] != "human"})
            types = [p["target"] for p in pv if p["kind"] == "subagent"]
        else:
            pv = tools.steps_claude(folder / "log.jsonl", project)
            cost, steps, n = figures(folder)
            types = [json.loads(m.read_text(encoding="utf-8")).get("agentType", "agent") for m in sorted((folder / "agents").glob("*.meta.json"))]
        # The session's manners, from its steps; orchestration is judged like execution: it receives the work item's folder, not the handoff.
        stage = c["role"] if c["role"] in checks.ALL else "execute"
        manners = {v["name"]: v["state"] for v in checks.check(pv, stage, {"folder": project})
                   if v["name"] in checks.MANNERS}
        st["sessions"].append({"nr": c["nr"], "role": c["role"], "model": model, "effort": effort,
                               "prompt": c["prompt"], "id": c["id"], "duration_s": round(time.time() - c["start"]),
                               "answers": sum(o["answer"] != "DONE" for o in human), "cost": cost, "steps": steps, "tokens": n,
                               "agents": dict(collections.Counter(types)), "manners": manners, "reason": reason,
                               "outside": changed(before, fingerprint())})
        st["current"] = None
        if reason != "done":
            st["state"] = reason
            break
        state_md = (project / "STATE.md").read_text(encoding="utf-8") if (project / "STATE.md").is_file() else ""
        hand = handoff(human[-1]["message"] if human else "", state_md)
        if hand.get("next") and hand.get("prompt") == c["prompt"]:  # a state file left over from the session before
            hand = {"next": False, "reason": "the handoff repeats the prompt of the session that just ended"}
        st["next"] = {k: hand.get(k) for k in ("role", "model", "effort", "prompt")} if hand.get("next") else None
        st["ending"] = None if hand.get("next") else hand.get("reason", "no session follows")
    else:
        st["state"] = "done" if not st["next"] else f"the cap of {st['sessions_max']} sessions"
    st["acceptance"] = acceptance(pdir, project)
    roles = [x["role"] for x in st["sessions"]]
    first = next((i for i, r in enumerate(roles) if r in ("execute", "orchestration")), len(roles))
    st["escalations"] = sum(x["agents"].get("escalation", 0) for x in st["sessions"])
    st["returns"] = sum(r in ("spec", "plans") for r in roles[first:])
    st["cost"] = round(sum(x["cost"] for x in st["sessions"]), 4)
    st["tokens"] = sum(x["tokens"] for x in st["sessions"])
    st["manners_passed"] = all(v is not False for x in st["sessions"] for v in x.get("manners", {}).values())
    if st.get("tool") == "vibe":
        st["eur_estimated"] = round(st["cost"] * usage.EUR_PER_USD, 4)
    shutil.copytree(project, output / "project", symlinks=True, dirs_exist_ok=True)
    journey_report(output, st)
    key = Path.home() / ".claude/projects" / str(project).replace("/", "-")
    shutil.rmtree(space, ignore_errors=True)
    if key.name.startswith("-tmp-bench-"):  # ⚠ only a key of the miniature house
        shutil.rmtree(key, ignore_errors=True)
    st["space_left"] = space.exists()
    write_state(output, st)
    print(f"{output}: {st['state']}; {st['cost']:.2f} $; acceptance {'passed' if st['acceptance']['code'] == 0 else 'failed'}")
    return 0


def blind(a):
    """The results of two journeys, put side by side without saying which is which."""
    journeys = [Path(a.a).resolve(), Path(a.b).resolve()]
    random.shuffle(journeys)
    for letter, d in zip("AB", journeys):
        dest = Path(a.output).resolve() / letter
        dest.mkdir(parents=True)
        arch = subprocess.run(["git", "-C", str(d / "project"), "archive", "main"], capture_output=True, check=True)
        subprocess.run(["tar", "-x", "-C", str(dest)], input=arch.stdout, check=True)
        # The records say how the work was done, so they also say the variant: the human judges only what came out.
        shutil.rmtree(dest / "records", ignore_errors=True)
    Path(a.key).write_text(json.dumps({"A": str(journeys[0]), "B": str(journeys[1])}, indent=2) + "\n", encoding="utf-8")
    print(f"{a.output}: A and B; the key is in {a.key}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="The bench of AI coding tools.")
    sub = ap.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run", help="one task, on one tool, with the simulated human")
    r.add_argument("--tool", required=True, choices=sorted(tools.TOOLS))
    r.add_argument("--model", required=True)
    r.add_argument("--effort")
    r.add_argument("--task", required=True)
    r.add_argument("--output", required=True)
    r.add_argument("--reference", help="the run put side by side in the report")
    r.add_argument("--minutes", type=int, default=90, help="the run's cap on time; default 90")
    r.add_argument("--manners", action="store_true", help="the manners checks become required on this run")
    c = sub.add_parser("read", help="the checks on a log that already exists")
    c.add_argument("--tool", required=True, choices=sorted(tools.STEPS))
    c.add_argument("--log", required=True)
    c.add_argument("--stage", required=True, choices=checks.ALL)
    c.add_argument("--folder", help="the folder the paths are relative to")
    c.add_argument("--task", help="the task's folder, for a bench run")
    p = sub.add_parser("profile", help="the numbers of Claude Code, from its logs")
    p.add_argument("--after", required=True, help="the first day, YYYY-MM-DD")
    p.add_argument("--output", required=True)
    d = sub.add_parser("journey", help="a trial project, from spec to merge, on a variant of the house")
    d.add_argument("--project", help="the trial project's folder: project.json, brief.md, acceptance/probe.py")
    d.add_argument("--output", help="the folder in which the journey's folder is made")
    d.add_argument("--tool", default="claude", choices=["claude", "vibe"],
                   help="the sessions' tool; with vibe, the profile comes from each session's role")
    d.add_argument("--variant", help="the framework the miniature house is made from; default the root")
    d.add_argument("--note", help="a file put in the variant's house rules, .claude/rules/variant-note.md")
    d.add_argument("--label", help="the variant's name in the journey's folder; default the framework's name")
    d.add_argument("--model", default="opus", help="the first session's model, the spec's; default opus. With vibe, a house alias (qwen-agent) takes all the roles")
    d.add_argument("--effort", help="the first session's effort")
    d.add_argument("--sessions", type=int, default=10, help="the cap on sessions; default 10")
    d.add_argument("--minutes", type=int, default=150, help="the cap on one session; default 150")
    d.add_argument("--budget", type=float, default=80, help="the dollars at the API price after which no session starts")
    d.add_argument("--resume", help="the folder of a journey stopped by quota or by an error")
    d.add_argument("--manners", action="store_true", help="each session's manners become required on this journey")
    d.add_argument("--same-model", action="store_true",
                   help="with claude, each session on --model and --effort, not on the model from the handoff")
    o = sub.add_parser("blind", help="two journeys, put side by side without saying which is which")
    o.add_argument("--a", required=True)
    o.add_argument("--b", required=True)
    o.add_argument("--output", required=True)
    o.add_argument("--key", required=True, help="the file in which the letter of each journey is written")
    a = ap.parse_args()
    return {"run": run, "read": read, "profile": profile, "journey": journey, "blind": blind}[a.command](a)


if __name__ == "__main__":
    sys.exit(main())
