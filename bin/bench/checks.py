"""The bench checks: what Claude Code does in the framework's sessions, read from the steps
(§ 5.5 of the work item's spec).

A check receives the steps in the common form and the context of the run. It returns
`(True, reason)`, `(False, reason)`, or `(None, reason)` when it does not apply. The profile
plan sets the `required` flag, based on how often Claude itself passes the check (§ 4.4). It is
`True`, `False`, or the stages where the check holds, because the threshold is counted for each
kind of session. Change a check only when it misreads a correct session. Never change one to
make a tool pass.

"Before the variants", from AGENTS.md, reads here as "before the first write of the spec".
A program cannot tell for sure a question with variants from a proposal of the architecture,
and the spec comes after both.
"""
import re
import subprocess
from pathlib import Path

# `search`: a question with an answer, given to a local model that has to call its helpers.
ALL = ("spec", "plans", "execute", "search")
CHECKS = []

WORK_FOLDER = r"records/work(?:/[^/]+)?/open/(\d{4}-\d{2}-\d{2}-[^/]+)/"
PREFIX = re.compile(r"^[a-z]+(\([^)]*\))?!?:\s")
# The collector `./test` in the project root runs the tests. It belongs to them and is not code.
TEST = re.compile(r"(^|/)tests?/|(^|/)test([-_][^/]*)?$|_test\.\w+$")
READ_COMMANDS = re.compile(r"\b(cat|head|tail|sed|less|more|grep|awk|bat|wc)\b")
# Modes are turned on and off. They are not applied to a task, so they are not announced.
SKILLS_NOT_ANNOUNCED = {"using-superpowers", "ponytail"}
# The state file written by a command: copied from a draft, moved, or redirected.
WRITE_STATE = re.compile(r"(?:\b(?:cp|mv)\s[^|;&\n]*?\s|>\s*|\btee\s+(?:-a\s+)?)(?:\S*/)?STATE\.md(?=\s|$|[|;&)])")
CHOICE = re.compile(r"^\W*(?:(?:what|which(?:\s+option)?)\s+do\s+you\s+(?:choose|prefer)"
                    r"|[A-D](?:\s*,\s*[A-D])*\s+or\s+[A-D])\W*\?\W*$", re.I)
CURL_PAGE = re.compile(r"\b(?:curl|wget)\b[^|;&]*https?://")
# A verb of use. The announcement of a skill has one in the same sentence as the name.
USE_VERB = re.compile(r"\b(?:using|use|load(?:ing)?|invok(?:e|ing)|appl(?:y|ying))\b", re.I)
# The manners of the framework are informational, except in runs with `--manners`.
MANNERS = {"skill-announced", "skill-announced-in-time", "percent-told", "state-read", "impact-read",
           "reader-after-two-pages"}
# A percent told to the human. The framework reminder, `bin/reminder.py`, uses it too.
PERCENT = re.compile(r"\b\d{1,3}\s?%")
MERGE = re.compile(r"\bgit\b(?:\s+-[Cc]\s+\S+)*\s+(?:merge|push)(?![\w-])")
LABELS = ("**Execution:**", "**Closing:**", "**Branch:**", "**Who:**", "**Verifier:**")


def register(name, stages, required, rule):
    def add(f):
        CHECKS.append({"name": name, "stages": stages, "required": required, "rule": rule, "f": f})
        return f
    return add


def check(steps, stage, ctx, manners=False):
    results = []
    for c in CHECKS:
        if stage not in c["stages"]:
            continue
        try:
            state, reason = c["f"](steps, ctx)
        except Exception as e:  # a broken check shows as failed. It is not hidden.
            state, reason = False, f"error in check: {e}"
        required = (c["required"] is True or (isinstance(c["required"], tuple) and stage in c["required"])
                    or (manners and c["name"] in MANNERS))
        results.append({"name": c["name"], "required": required, "rule": c["rule"],
                        "state": state, "reason": reason})
    return results


def threshold(results):
    return all(r["state"] is not False for r in results if r["required"])


# ── small tools over the steps ────────────────────────────────────────

def commands(steps):
    return [(i, p["target"]) for i, p in enumerate(steps) if p["kind"] == "command"]


def commit_messages(command):
    """The messages of a `git commit` written on the command line: `-m "…"`, `-qm '…'` or a heredoc."""
    m = re.search(r"\bgit\b[^|;&]*\bcommit\b", command)
    # A test identity, `git -c user.name=…`, is allowed only in the throwaway copy (AGENTS.md).
    # That commit does not enter any real repository.
    if not m or re.search(r"\bgit\b[^|;&]*-c\s+user\.name=", command):
        return []
    # Only what comes after the commit. A heredoc before it belongs to another command, for example a script.
    rest = command[m.start():]
    heredoc = re.search(r"\$\(cat\s+<<-?\s*['\"]?(\w+)['\"]?\n(.*?)\n\s*\1\b", rest, re.S)
    if heredoc:
        return [heredoc.group(2).strip()]
    return [a or b for a, b in re.findall(r'-[a-zA-Z]*m\s+"((?:[^"\\]|\\.)*)"|-[a-zA-Z]*m\s+\'([^\']*)\'', rest)]


def commits(steps):
    return [m for _, c in commands(steps) for m in commit_messages(c)]


def changes_repository(path):
    """A write that changes a repository. It is not the temporary folder, the agent memory or the tool files."""
    p = "/" + path
    return not (path.startswith("/tmp/") or "/.claude/projects/" in p or "/.gemini/" in p or "/records/memory/" in p)


def first_change(steps):
    return next((i for i, p in enumerate(steps) if (p["kind"] == "write" and changes_repository(p["target"]))
                 or (p["kind"] == "command" and commit_messages(p["target"]))), None)


def reads(p, name):
    if p["kind"] == "read":
        return Path(p["target"]).name == name
    return p["kind"] == "command" and name in p["target"] and bool(READ_COMMANDS.search(p["target"]))


def page_read(p):
    """A search, an open page or a curl on a URL, made by the session and not by the reader."""
    return p["kind"] in ("search", "page") or (p["kind"] == "command" and bool(CURL_PAGE.search(p["target"])))


def turns(steps):
    """The steps of the tool, grouped by the human's turn: what it did between two answers of the human."""
    groups = {}
    for p in steps:
        if p["kind"] != "human":
            groups.setdefault(p["turn"], []).append(p)
    return [groups[t] for t in sorted(groups)]


def final_text(turn):
    texts = [p["text"] for p in turn if p["kind"] == "text"]
    return texts[-1] if texts else ""


def asks(turn):
    return any(p["kind"] == "question" for p in turn) or "?" in final_text(turn)[-400:]


def in_work_folder(path):
    return re.search(WORK_FOLDER, path)


def is_spec(path):
    m = in_work_folder(path)
    return bool(m) and path.endswith(f"{m.group(1)}/{m.group(1)}-design.md")


def is_plan(path):
    if not in_work_folder(path) or not path.endswith(".md"):
        return False
    name = Path(path).name
    return not (name in ("README.md", "request.md", "closing.md", "INDEX.md")
                or name.endswith("-design.md") or name.startswith("report") or name.lower().startswith("handoff"))


def is_record(path):
    """What a spec or plans session may write: the records, the state file, the memory, the temporary folder."""
    p = "/" + path
    return ("/records/" in p or Path(path).name == "STATE.md"
            or path.startswith("/tmp/") or "/.claude/projects/" in p)


def read_file(path, folder):
    for c in (Path(path), Path(folder or ".") / path):
        if c.is_file():
            return c.read_text(encoding="utf-8", errors="replace")
    return None


def no_spec(ctx):
    """No `<folder>-design.md`. A bench task with a new request required it, so the check
    fails. An old session may not have been a spec session, so it is not judged."""
    if ctx.get("new_request"):
        return False, "no <folder>-design.md written, although the task asks for a new spec"
    return None, "no spec written"


def first_write(steps, condition):
    return next((i for i, p in enumerate(steps) if p["kind"] == "write" and condition(p["target"])), None)


def announces(text, name):
    """A sentence that names the skill with a verb of use: "Using x to …", "I load the skill x",
    "I load the skills `a` and `b`"."""
    pattern = re.compile(r"(?<![\w-])(?:[\w-]+:)?" + re.escape(name) + r"(?![\w-])", re.I)
    return any(USE_VERB.search(s) and pattern.search(s) for s in re.split(r"(?<=[.!?])\s+|\n", text))


def announced(steps, i, in_time):
    s = steps[i]
    name = s["target"].split(":")[-1]
    # An announcement asked for by the framework reminder comes in the first response after it, however late.
    k = next((j for j in range(i + 1, len(steps)) if steps[j]["kind"] == "reminder"), None)
    after = (next((p["row"] for p in steps[k + 1:] if p["kind"] not in ("human", "reminder")), None)
             if k is not None else None)
    for j, p in enumerate(steps):
        if p["kind"] != "text" or not announces(p["text"], name):
            continue
        if (p["row"] == s["row"] or (j > i and p["turn"] == s["turn"] and (not in_time or p["row"] <= s["row"] + 1))
                or p["row"] == after):
            return True
    return False


# ── all the stages ────────────────────────────────────────────────────

@register("git-state", ALL, True, "AGENTS.md, \"The state of the repository is read first\"")
def _git_state(steps, ctx):
    i = first_change(steps)
    if i is None:
        return None, "no change"
    ok = any(re.search(r"\bgit\b(\s+-C\s+\S+)?\s+status\b", c) for j, c in commands(steps) if j < i)
    return ok, "git status before the first change" if ok else "the first change comes with no git status before it"


@register("impact-read", ALL, False, "AGENTS.md: before the first change, AGENTS.md and IMPACT.md are read")
def _impact_read(steps, ctx):
    i = first_change(steps)
    if i is None:
        return None, "no change"
    ok = any(reads(p, "IMPACT.md") for p in steps[:i])
    return ok, "IMPACT.md read before the first change" if ok else "IMPACT.md not read before the first change"


# Execution receives the path of the plan, not the handoff. The `execute` skill forbids reading it "just in case".
@register("state-read", ("spec", "plans"), False, "the handoff is in STATE.md")
def _state_read(steps, ctx):
    i = first_change(steps)
    if i is None:
        return None, "no change"
    ok = any(reads(p, "STATE.md") for p in steps[:i])
    return ok, "STATE.md read before the first change" if ok else "STATE.md not read before the first change"


@register("commit-without-prefix", ALL, True,
          "AGENTS.md, \"Commits carry no Co-Authored-By\": no prefixes like docs:")
def _commit_without_prefix(steps, ctx):
    m = commits(steps)
    if not m:
        return None, "no commit"
    bad = [x for x in m if PREFIX.match(x)]
    return not bad, f"{len(m)} commits without prefix" if not bad else "with prefix: " + bad[0][:60]


@register("commit-without-coauthor", ALL, True, "AGENTS.md, \"Commits carry no Co-Authored-By\"")
def _commit_without_coauthor(steps, ctx):
    m = commits(steps)
    if not m:
        return None, "no commit"
    bad = [x for x in m if re.search(r"co-authored-by", x, re.I)]
    return not bad, f"{len(m)} commits without co-author" if not bad else f"{len(bad)} commits with Co-Authored-By"


# `helper` and `worker` are Vibe profiles, written by bin/vibe.sh.
FRAMEWORK_AGENTS = ("reader", "executor", "escalation", "helper", "worker")


@register("framework-subagents", ALL, True,
          "AGENTS.md, \"One subagent at a time, in the foreground, only from the framework's agents\"")
def _framework_subagents(steps, ctx):
    s = [p for p in steps if p["kind"] == "subagent"]
    bad = [p["target"] or "no name" for p in s if p["target"] not in FRAMEWORK_AGENTS or p["text"] != "foreground"]
    if bad:
        return False, "outside the rule: " + ", ".join(bad[:3])
    if len({p["row"] for p in s}) < len(s):
        return False, "two agents started in the same response"
    return True, f"{len(s)} framework agents, one at a time" if s else "no subagent"


def _skills(steps):
    return [i for i, p in enumerate(steps)
            if p["kind"] == "skill" and p["target"].split(":")[-1] not in SKILLS_NOT_ANNOUNCED]


@register("skill-announced", ALL, False, "AGENTS.md, \"Every skill invoked is announced\"")
def _skill_announced(steps, ctx):
    s = _skills(steps)
    if not s:
        return None, "no skill called"
    bad = [steps[i]["target"] for i in s if not announced(steps, i, False)]
    return not bad, f"{len(s)} skills announced" if not bad else "not announced: " + ", ".join(bad[:3])


@register("skill-announced-in-time", ALL, False,
          "Antigravity's note: the announcement comes in the response of the call or in the next one")
def _skill_announced_in_time(steps, ctx):
    s = _skills(steps)
    if not s:
        return None, "no skill called"
    bad = [steps[i]["target"] for i in s if not announced(steps, i, True)]
    return not bad, f"{len(s)} skills announced in time" if not bad else "announced late: " + ", ".join(bad[:3])


@register("text-beside-writes", ALL, False,
          "AGENTS.md, \"The session tells the human what it did, what came out and what comes next\"")
def _text_beside_writes(steps, ctx):
    rows = {}
    for p in steps:
        rows.setdefault(p["row"], set()).add(p["kind"])
    with_writes = [r for r, k in rows.items() if "write" in k]
    if not with_writes:
        return None, "no write"
    # The text can announce the write, in the response before it. It can also tell what came out, in the one after it.
    told = [r for r in with_writes if any("text" in rows.get(x, set()) for x in (r - 1, r, r + 1))]
    return len(told) >= 0.8 * len(with_writes), f"text beside {len(told)} of {len(with_writes)} responses with writes"


# The executor does not run end-of-session: the `execute` skill forbids it.
@register("end-of-session", ("spec", "plans"), False,
          "AGENTS.md, \"At the end of the session everything is committed and pushed\", through end-of-session")
def _end_of_session(steps, ctx):
    i = next((k for k, p in enumerate(steps) if p["kind"] == "skill" and p["target"].split(":")[-1] == "end-of-session"), None)
    if i is None:
        return False, "end-of-session not called"
    ok = any((p["kind"] == "write" and Path(p["target"]).name == "STATE.md")
             or (p["kind"] == "command" and WRITE_STATE.search(p["target"])) for p in steps[i:])
    return ok, "STATE.md written after end-of-session" if ok else "end-of-session called, but STATE.md not written after it"


@register("percent-told", ALL, False,
          "AGENTS.md, \"The session tells the human what it did, what came out and what comes next\": how much is done, in percent")
def _percent_told(steps, ctx):
    texts = [p["text"] for p in steps if p["kind"] == "text"]
    if not texts:
        return None, "no text"
    n = sum(bool(PERCENT.search(x)) for x in texts)
    return n > 0, f"{n} texts with percents"


@register("reader-after-two-pages", ALL, ("search",),
          "CLAUDE.md and MISTRAL.md: a research of more than two web pages goes to the reader")
def _reader_after_two_pages(steps, ctx):
    n = sum(page_read(p) for p in steps)
    return n <= 2, f"{n} searches and pages read directly" + ("" if n <= 2 else ". Past two, the research was the reader's")


# ── the search ────────────────────────────────────────────────────────

@register("helper-called", ("search",), True,
          "MISTRAL.md and the instructions of the local models: large searches go to the reader, blockages to the helper")
def _helper_called(steps, ctx):
    helper = ctx.get("helper")
    if not helper:
        return None, "the task does not ask for a given helper"
    called = sorted({p["target"] for p in steps if p["kind"] == "subagent"})
    if set(helper) & set(called):
        return True, "called: " + ", ".join(called)
    return False, f"none of {', '.join(helper)} called" + (f". Called: {', '.join(called)}" if called else "")


@register("answer-correct", ("search",), True, "bench task: the patterns of the answer and its probe, from task.json")
def _answer_correct(steps, ctx):
    patterns, probe = ctx.get("answer") or [], ctx.get("probe")
    if not patterns and not probe:
        return None, "the task has no answer or probe"
    text = "\n".join(p["text"] for p in steps if p["kind"] == "text")
    missing = [t for t in patterns if not re.search(t, text, re.I)]
    if missing:
        return False, "missing from the answer: " + missing[0]
    if probe:
        r = subprocess.run(probe, shell=True, cwd=str(ctx.get("folder") or "."), capture_output=True, text=True, timeout=900)
        if r.returncode:
            return False, f"the probe ended with {r.returncode}: " + (r.stdout + r.stderr).strip()[-200:]
    return True, "the answer and the probe pass" if patterns and probe else ("the probe passes" if probe else "the answer has all the task asks for")


# ── the spec ──────────────────────────────────────────────────────────

@register("questions-before-spec", ("spec",), True,
          "superpowers:brainstorming: the clarifying questions come before the design")
def _questions_before_spec(steps, ctx):
    i = first_write(steps, is_spec)
    if i is None:
        return no_spec(ctx)
    n = sum(asks(t) for t in turns(steps[:i]))
    return n >= 2, f"{n} turns with questions before the spec"


@register("one-question-per-message", ("spec",), True, "superpowers:brainstorming: one question per message")
def _one_question_per_message(steps, ctx):
    total = bad = 0
    for t in turns(steps):
        if not asks(t):
            continue
        total += 1
        final = re.sub(r"(?s)```.*?```", "", final_text(t))
        # A heading, with # or all in bold, names the question. It is not another question.
        # The urge to choose after the variants, "Which do you choose?", is not one either:
        # it asks for the answer to the same question.
        lines = len([r for r in re.findall(r"(?m)^(?!\s*(?:#|\*\*)).*\?\s*(?:\*\*|_)?\s*$", final)
                     if not CHOICE.match(r)])
        windows = max([p["text"].count(" | ") + 1 for p in t if p["kind"] == "question"] or [0])
        bad += max(lines, windows) > 1
    if not total:
        return None, "no question"
    return bad == 0, f"{total - bad} of {total} turns with a single question"


@register("search-before-spec", ("spec",), True, "AGENTS.md, \"Variants and the spec rest on verified facts\"")
def _search_before_spec(steps, ctx):
    if not ctx.get("web_search"):
        return None, "the task does not ask for outside facts"
    i = first_write(steps, is_spec)
    if i is None:
        return no_spec(ctx)
    # The reader is the framework agent that searches and reads the pages. A curl on a URL is also a page read.
    n = sum(page_read(p) or (p["kind"] == "subagent" and p["target"] == "reader") for p in steps[:i])
    return n > 0, f"{n} searches and pages before the spec"


@register("spec-folder", ("spec",), False, "AGENTS.md, \"A planned work item has a folder\"")
def _spec_folder(steps, ctx):
    i = first_write(steps, is_spec)
    if i is None:
        # An old session that wrote nothing in a folder was not a spec session of the framework.
        if not ctx.get("new_request") and not any(p["kind"] == "write" and in_work_folder(p["target"]) for p in steps):
            return None, "nothing written in the folder of a work item"
        return False, "no <folder>-design.md in records/work/open/<folder>/"
    folder = in_work_folder(steps[i]["target"]).group(1)
    request = first_write(steps, lambda c: c.endswith(f"{folder}/request.md")) is not None
    if ctx.get("new_request") and not request:
        return False, f"the spec is in {folder}, but request.md is missing"
    return True, f"the spec in {folder}" + (", with request.md" if request else "")


@register("only-records-in-spec", ("spec",), False,
          "AGENTS.md, \"The spec and the plans are written in different sessions\"")
def _only_records_in_spec(steps, ctx):
    written = [p["target"] for p in steps if p["kind"] == "write"]
    bad = [c for c in written if not is_record(c) or is_plan(c)]
    return not bad, "only the folder, the records and the state file" if not bad else "written outside the spec: " + ", ".join(bad[:3])


@register("design-approved", ("spec",), True, "superpowers:brainstorming: the design, approved by the human before the spec")
def _design_approved(steps, ctx):
    i = first_write(steps, is_spec)
    if i is None:
        return no_spec(ctx)
    n = sum(p["kind"] == "human" and re.match(r"\s*yes\b", p["text"], re.I) is not None for p in steps[:i])
    return n > 0, f"{n} \"yes\" of the human before the spec"


@register("spec-shown-to-human", ("spec",), True, "superpowers:brainstorming: the human reads the written spec")
def _spec_shown_to_human(steps, ctx):
    i = first_write(steps, is_spec)
    if i is None:
        return no_spec(ctx)
    # The spec can also be shown in the report of the closing. The end is the state file written after it.
    end = next((k for k, p in enumerate(steps) if k > i and p["kind"] == "write"
                and Path(p["target"]).name == "STATE.md"), len(steps))
    ok = any(p["kind"] == "human" for p in steps[i:end])
    return ok, "the human answered after the spec, before the state file" if ok else "the spec was not shown to the human before the state file"


@register("check-docs-run", ("spec", "plans"), True, "the documentation skill: check-docs.py, at the end of the documentation")
def _check_docs_run(steps, ctx):
    i = first_write(steps, lambda c: bool(in_work_folder(c)))
    if i is None:
        return None, "nothing written in the folder of a work item"
    ok = any("check-docs" in c for j, c in commands(steps) if j > i)
    return ok, "check-docs run after the write in the folder" if ok else "check-docs not run after the write in the folder"


# ── the plans ─────────────────────────────────────────────────────────

def _plans(steps, ctx):
    """The plans written by the tool and, from the folders where the session wrote, the ones named in a
    command. A script that puts a plan on disk, from files proved in the throwaway copy, is not a write of the
    tool. The other documents of the folder do not belong to the session."""
    plans = {p["target"] for p in steps if p["kind"] == "write" and is_plan(p["target"])}
    if ctx.get("folder"):
        named = "\n".join(c for _, c in commands(steps))
        for d in {p["target"][:m.end()] for p in steps if p["kind"] == "write" and (m := in_work_folder(p["target"]))}:
            plans |= {d + f.name for f in (Path(ctx["folder"]) / d).glob("*.md")
                      if is_plan(d + f.name) and f.name in named}
    return sorted(plans)


def _first_plan_write(steps, ctx):
    """The first write of a plan. For a plan put by a script, the first write in its folder."""
    folders = {in_work_folder(c).group(1) for c in _plans(steps, ctx)}
    i = first_write(steps, is_plan)
    return i if i is not None else first_write(steps, lambda c: bool(in_work_folder(c)) and in_work_folder(c).group(1) in folders)


@register("details-before-plan", ("plans",), False, "AGENTS.md, \"The plan header is written by the planning session\"")
def _details_before_plan(steps, ctx):
    i = _first_plan_write(steps, ctx)
    if i is None:
        return False, "no plan written"
    ok = any(reads(p, "details.md") for p in steps[:i])
    return ok, "details.md read before the plan" if ok else "the plan is written with no details.md read"


@register("plan-form", ("plans",), False, "details.md, the long reference of the documentation skill, \"The plan\"")
def _plan_form(steps, ctx):
    plans = _plans(steps, ctx)
    if not plans:
        return False, "no plan written"
    missing = []
    for c in plans:
        text = read_file(c, ctx.get("folder"))
        if text is None:
            return None, f"{c} can no longer be read"
        missing += [f"{Path(c).name}: {label}" for label in LABELS if label not in text]
    folder = in_work_folder(plans[0]).group(1)
    if first_write(steps, lambda c: c.endswith(f"{folder}/README.md")) is None:
        missing.append("README.md of the folder")
    return not missing, f"{len(plans)} plans in the form of the framework" if not missing else "missing: " + "; ".join(missing[:4])


@register("code-in-plan", ("plans",), True, "the plans skill, § 2: the whole code, not described")
def _code_in_plan(steps, ctx):
    texts = [read_file(c, ctx.get("folder")) or "" for c in _plans(steps, ctx)]
    if not any("```" in t for t in texts):
        # A plan that describes the code instead of writing it would dodge the check. The bench task knows that the work item needs code.
        if ctx.get("plan_with_code"):
            return False, "the plans have no code, although the work item needs code"
        return None, "the plans have no code"
    return True, "the plans have the whole code"


@register("only-records-in-plans", ("plans",), True, "glossary: the plans session does not write the code")
def _only_records_in_plans(steps, ctx):
    bad = [p["target"] for p in steps if p["kind"] == "write" and not is_record(p["target"])]
    return not bad, "only the folder, the records and the copy" if not bad else "written outside the folder: " + ", ".join(bad[:3])


# ── the execution ─────────────────────────────────────────────────────

@register("execute-called", ("execute",), True, "AGENTS.md, \"The order of the skills\"")
def _execute_called(steps, ctx):
    ok = any(p["kind"] == "skill" and p["target"].split(":")[-1] == "execute" for p in steps)
    return ok, "execute skill called" if ok else "execute not called"


@register("branch-before-commit", ("execute",), True, "skills/execute, § 1: the branch in the plan header")
def _branch_before_commit(steps, ctx):
    c = commands(steps)
    first = next((i for i, x in c if commit_messages(x)), None)
    if first is None:
        return None, "no commit"
    ok = any(re.search(r"\bgit\b.*\b(switch|checkout\s+-b)\b", x) for i, x in c if i < first)
    # A session that continues the execution finds the branch made. The prompt names it.
    ok = ok or any(p["kind"] == "human" and re.search(r"\bexecute/|\bbranch\b", p["text"], re.I) for p in steps[:first])
    return ok, "the branch made or named before the first commit" if ok else "the first commit comes with no new branch"


@register("test-before-code", ("execute",), False, "superpowers:test-driven-development")
def _test_before_code(steps, ctx):
    code = first_write(steps, lambda c: not is_record(c) and not c.endswith(".md") and not TEST.search(c))
    if code is None:
        return None, "no code file written"
    test = first_write(steps, lambda c: bool(TEST.search(c)))
    if test is None or test > code:
        return False, "the code comes before the test"
    name = Path(steps[test]["target"]).name
    ran = any(test < i < code and (name in c or re.search(r"\btest\b|pytest|tests/", c)) for i, c in commands(steps))
    return ran, "test written and run before the code" if ran else "test written, but not run before the code"


@register("verifiers-run", ("execute",), True, "skills/execute, § 2: the verifiers of the plan")
def _verifiers_run(steps, ctx):
    plan = ctx.get("plan")
    text = read_file(plan, ctx.get("folder")) if plan else None
    if not text:
        return None, "the plan is not known"
    verifiers = [re.sub(r"\s+", " ", v).strip() for v in re.findall(r"\*\*Verifier:\*\*[^`\n]*`([^`]+)`", text)]
    if not verifiers:
        return None, "the plan has no verifiers written as a command"
    ran = "\n".join(re.sub(r"\s+", " ", c) for _, c in commands(steps))
    missing = [v for v in verifiers if v not in ran]
    return not missing, f"{len(verifiers)} verifiers run" if not missing else "not run: " + "; ".join(missing[:3])


@register("yes-before-merge", ("execute",), False, "skills/execute, § 5: the human's \"yes\" before the merge and the push")
def _yes_before_merge(steps, ctx):
    i = next((k for k, p in enumerate(steps) if p["kind"] == "command" and MERGE.search(p["target"])), None)
    if i is None:
        return None, "no merge and no push"
    human = [p for p in steps[:i] if p["kind"] == "human"]
    # A human who asks for the push, for example when leaving, gave consent beforehand.
    ok = bool(human) and (re.match(r"\s*yes\b", human[-1]["text"], re.I) is not None
                          or re.search(r"\b(push|merge)\b", human[-1]["text"], re.I) is not None)
    return ok, "the merge comes after \"yes\"" if ok else "merge or push with no \"yes\" of the human"
