#!/usr/bin/env python3
"""Test of bin/bench/bench.py, bin/bench/tools.py and bin/bench/checks.py.

No test framework and no quota. `agy`, `claude` and `vibe` are replaced by fake tools:
small scripts that write logs in the form of the real ones, in a fabricated HOME. The
workspace is fabricated too, so the fingerprint of the bench does not look at the real
repositories.
"""
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile


def project_root():
    """The folder that holds the `test` collector. It is not asked from git."""
    d = pathlib.Path(os.environ.get("TESTS_ROOT") or __file__).resolve()
    if d.is_file():
        d = d.parent
    while d != d.parent:
        if os.access(d / "test", os.X_OK):
            return d
        d = d.parent
    raise SystemExit("cannot find the project root")


R = project_root()
BENCH = R / "bin" / "bench" / "bench.py"
failed = 0


def check(condition, message):
    global failed
    if condition:
        print(f"  ✓ {message}")
    else:
        failed += 1
        print(f"  ✗ {message}")


if not BENCH.exists():
    print(f"  ✗ cannot find {BENCH}")
    sys.exit(1)

sys.path.insert(0, str(BENCH.parent))
import tools  # noqa: E402
import checks  # noqa: E402

# The control commands of the fake tools sit in HOME: the bench gives the tools a clean environment.
FAKE_AGY = r'''#!/usr/bin/env python3
import json, os, pathlib, sys, uuid
a = sys.argv[1:]
text = a[a.index("-p") + 1].strip()
home = pathlib.Path.home()
if (home / "fake-quota").exists():
    print("RESOURCE_EXHAUSTED (code 429): the quota refills in 4h", file=sys.stderr)
    sys.exit(1)
cid = a[a.index("--conversation") + 1] if "--conversation" in a else str(uuid.uuid4())
j = home / ".gemini/antigravity-cli/brain" / cid / ".system_generated/logs/transcript_full.jsonl"
j.parent.mkdir(parents=True, exist_ok=True)
rows = j.read_text().splitlines() if j.exists() else []
def write(**r):
    r["step_index"] = len(rows)
    rows.append(json.dumps(r, ensure_ascii=False))
write(type="USER_INPUT", content=f"<USER_REQUEST>\n{text}\n</USER_REQUEST>\n<ADDITIONAL_METADATA>\ntime\n</ADDITIONAL_METADATA>")
if "--conversation" not in a:
    answer = "What color do you like?"
    write(type="PLANNER_RESPONSE", content="", tool_calls=[{"name": "view_file", "args": {"AbsolutePath": "/s/skills/brainstorming/SKILL.md"}}])
    write(type="PLANNER_RESPONSE", content="Using brainstorming to ask. " + answer,
          tool_calls=[{"name": "ask_question", "args": {"questions": [{"question": answer}]}}])
    write(type="GENERIC", content="A1: User Skipped")
else:
    target = os.path.join(os.getcwd(), "color.txt")
    open(target, "w").write(text + "\n")
    if (home / "fake-escape").exists():
        open((home / "fake-escape").read_text().strip(), "a").write("escaped\n")
    write(type="PLANNER_RESPONSE", content="", tool_calls=[{"name": "write_to_file", "args": {"TargetFile": target}}])
    write(type="EPHEMERAL_MESSAGE", content="You just changed `color.txt`.")
    answer = "I wrote the color in color.txt. Done."
    write(type="PLANNER_RESPONSE", content=answer)
j.write_text("\n".join(rows) + "\n")
print(json.dumps({"conversation_id": cid, "status": "SUCCESS", "response": answer, "usage": {"total_tokens": 100}}))
'''

FAKE_CLAUDE = r'''#!/usr/bin/env python3
import json, os, pathlib, sys
a = sys.argv[1:]
text = a[a.index("-p") + 1].strip()
if "--system-prompt" in a:  # the simulated human: answers the question, then ends
    print(json.dumps({"result": "blue" if "?" in text else "DONE", "is_error": False}))
    sys.exit(0)
cwd = os.getcwd()
key = pathlib.Path.home() / ".claude/projects" / cwd.replace("/", "-")
key.mkdir(parents=True, exist_ok=True)
new = "--session-id" in a
sid = a[a.index("--session-id" if new else "--resume") + 1]
j = key / f"{sid}.jsonl"
rows = j.read_text().splitlines() if j.exists() else []
def write(**r):
    rows.append(json.dumps(r, ensure_ascii=False))
write(type="user", message={"role": "user", "content": text})
if new:
    open("memory.txt", "w").write("linked\n" if (key / "memory").is_symlink() else "unlinked\n")
    write(type="assistant", message={"id": "m1", "content": [{"type": "tool_use", "name": "Skill", "input": {"skill": "superpowers:brainstorming"}}]})
    write(type="user", isMeta=True, message={"content": [{"type": "text", "text": "Base directory for this skill"}]})
    result = "What color do you like?"
    write(type="assistant", message={"id": "m2", "content": [{"type": "text", "text": "Using superpowers:brainstorming to ask. " + result}]})
else:
    open("color.txt", "w").write(text + "\n")
    write(type="assistant", message={"id": "m3", "content": [{"type": "text", "text": "I write the color."},
          {"type": "tool_use", "name": "Write", "input": {"file_path": os.path.join(cwd, "color.txt")}}]})
    write(type="assistant", isSidechain=True, message={"id": "s1", "content": [{"type": "tool_use", "name": "Write", "input": {"file_path": "/other"}}]})
    result = "Done."
    write(type="assistant", message={"id": "m4", "content": [{"type": "text", "text": result}]})
j.write_text("\n".join(rows) + "\n")
print(json.dumps({"session_id": sid, "result": result, "is_error": False, "total_cost_usd": 0.01}))
'''


# Fake Vibe: writes the `streaming` output and the session log in VIBE_HOME, as Vibe 2.26 does.
# The tokens add up per session, so the second call holds those of the first.
FAKE_VIBE = r'''#!/usr/bin/env python3
import json, os, pathlib, sys, uuid
a = sys.argv[1:]
if "--resume" in a and os.environ.get("VIBE_CLI") != "python":  # the Rust TUI of 2.26 refuses -p with --resume
    print("error: the argument '--prompt [<PROMPT>]' cannot be used with '--resume [<RESUME>]'", file=sys.stderr)
    sys.exit(2)
text = a[a.index("-p") + 1].strip()
home = pathlib.Path(os.environ["VIBE_HOME"])
if (pathlib.Path.home() / "fake-quota").exists():
    print("Price limit exceeded: $3.10 > $3.00", file=sys.stderr)
    sys.exit(1)
new = "--resume" not in a
sid = str(uuid.uuid4()) if new else a[a.index("--resume") + 1]
d = home / "logs/session/unified" / sid
g = d / "generations/0000000000000001"
g.mkdir(parents=True, exist_ok=True)
(d / "CURRENT").write_text(json.dumps({"generation": "0000000000000001"}))
(d / "meta.json").write_text(json.dumps({"session_id": sid, "start_time": "2026-10-08T10:00:00+00:00"}))
ag = a[a.index("--agent") + 1]
profile = home / "agents" / f"{ag}.toml"
import tomllib
active = tomllib.loads(profile.read_text()).get("active_model", "large-4") if profile.is_file() else "large-4"
(g / "runtime-state.json").write_text(json.dumps({"session_metadata": {"active_model": active}}))
(g / "projection-state.json").write_text(json.dumps({"snapshot": {"session": {"tokenUsage": {
    "inputTokens": 1_000_000 if new else 2_000_000, "cachedInputTokens": 0, "outputTokens": 0}}}}))
def emit(kind, **r):
    print(json.dumps({"id": str(uuid.uuid4()), "sessionId": sid, "type": kind, **r}, ensure_ascii=False))
emit("message", role="user", content=[{"type": "text", "text": text}])
emit("reasoning", text="I am thinking")
if new:
    open("home-vibe.txt", "w").write(f"{(home / 'AGENTS.md').is_file()}\n")
    open("agent-vibe.txt", "w").write(ag + "\n")
    emit("effect", detail={"toolName": "skill", "input": {"name": "brainstorming"}})
    emit("message", role="assistant", content=[{"type": "text", "text": "Using brainstorming to ask. What color do you like?"}])
else:
    target = os.path.join(os.getcwd(), "color.txt")
    open(target, "w").write(text + "\n")
    emit("effect", detail={"toolName": "file_system.write_file", "input": {"filePath": target, "content": text}})
    emit("message", role="assistant", content=[{"type": "text", "text": "Done."}])
'''


def step(kind, target="", text="", row=0, turn=0):
    return {"row": row, "turn": turn, "kind": kind, "tool": "", "target": target, "text": text}


def state(name, steps, **ctx):
    return next(v["f"] for v in checks.CHECKS if v["name"] == name)(steps, ctx)[0]


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")


print("the common form")
with tempfile.TemporaryDirectory() as tmp:
    t = pathlib.Path(tmp)
    write_jsonl(t / "agy.jsonl", [
        {"type": "USER_INPUT", "content": "<USER_REQUEST>\ndo something\n</USER_REQUEST>\n<ADDITIONAL_METADATA>\ntime\n</ADDITIONAL_METADATA>"},
        {"type": "PLANNER_RESPONSE", "content": "", "tool_calls": [{"name": "view_file", "args": {"AbsolutePath": "/s/skills/brainstorming/SKILL.md"}}]},
        {"type": "EPHEMERAL_MESSAGE", "content": "You just read the skill"},
        {"type": "PLANNER_RESPONSE", "content": "Using brainstorming to ask.", "tool_calls": [
            {"name": "write_to_file", "args": {"TargetFile": "/p/records/x.md"}},
            {"name": "ask_question", "args": {"questions": [{"question": "What do you want?"}]}}]},
        {"type": "GENERIC", "content": "A1: User Skipped"},
        {"type": "USER_INPUT", "content": "<USER_REQUEST>\n1\n</USER_REQUEST>"}])
    p = tools.steps_agy(t / "agy.jsonl", "/p")
    check([x["kind"] for x in p] == ["human", "skill", "reminder", "text", "write", "question", "human"],
          "agy: the kinds of the steps, in order")
    check(p[1]["target"] == "brainstorming" and p[4]["target"] == "records/x.md" and p[5]["text"] == "What do you want?",
          "agy: the skill by its folder, the relative path, the text of the question")
    check(p[0]["text"] == "do something" and p[-1]["turn"] == 1,
          "agy: the request without the wrappers, and the turn grows with each human answer")
    write_jsonl(t / "app.jsonl", [
        {"type": "USER_INPUT", "content": "<USER_REQUEST>\ndo something\n</USER_REQUEST>"},
        {"type": "PLANNER_RESPONSE", "content": "", "tool_calls": [
            {"name": "ask_question", "args": {"questions": [{"question": "Is the design good?"}]}}]},
        {"type": "GENERIC", "content": "Created At: x\nCompleted At: y\nA1: (Recommended) Yes, the design is good."},
        {"type": "PLANNER_RESPONSE", "content": "", "tool_calls": [{"name": "write_to_file", "args": {"TargetFile": "/p/a.md"}}]},
        {"type": "GENERIC", "content": "Created At: x\nCreated file file:///p/a.md"}])
    p = tools.steps_agy(t / "app.jsonl", "/p")
    check([x["kind"] for x in p] == ["human", "question", "human", "write"] and p[2]["text"] == "Yes, the design is good."
          and p[3]["turn"] == 1, "agy: the answer given in the app, to ask_question, is the human's, without the label of the option")
    write_jsonl(t / "claude.jsonl", [
        {"type": "user", "message": {"content": "hello"}},
        {"type": "assistant", "message": {"id": "a1", "content": [{"type": "tool_use", "name": "Skill", "input": {"skill": "superpowers:brainstorming"}}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}},
        {"type": "user", "isMeta": True, "message": {"content": [{"type": "text", "text": "Base directory"}]}},
        {"type": "assistant", "message": {"id": "a2", "content": [{"type": "text", "text": "Using superpowers:brainstorming to x"}]}},
        {"type": "assistant", "message": {"id": "a2", "content": [{"type": "tool_use", "name": "Bash", "input": {"command": "git status"}}]}},
        {"type": "assistant", "isSidechain": True, "message": {"id": "s", "content": [{"type": "tool_use", "name": "Write", "input": {"file_path": "/x"}}]}},
        {"type": "user", "message": {"content": "<local-command-stdout>output</local-command-stdout>"}},
        {"type": "user", "message": {"content": "yes"}}])
    p = tools.steps_claude(t / "claude.jsonl", "/p")
    check([x["kind"] for x in p] == ["human", "skill", "text", "command", "human"],
          "claude: without the meta lines, the subagents' lines and the local commands")
    check(p[1]["target"] == "brainstorming" and p[2]["row"] == p[3]["row"] == 1 and p[-1]["turn"] == 1,
          "claude: the skill without the plugin, the response by its id, the turn")
    write_jsonl(t / "window.jsonl", [
        {"type": "user", "message": {"content": "close"}},
        {"type": "assistant", "message": {"id": "a1", "content": [{"type": "tool_use", "id": "q1", "name": "AskUserQuestion",
                                                                   "input": {"questions": [{"question": "Write everything?"}]}}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "q1", "content":
            'Your questions have been answered: "Write everything?"="Yes, write everything (Recommended)". You can now continue with these answers in mind.'}]}},
        {"type": "assistant", "message": {"id": "a2", "content": [{"type": "tool_use", "name": "Bash", "input": {"command": "git push"}}]}}])
    p = tools.steps_claude(t / "window.jsonl", "/p")
    check([x["kind"] for x in p] == ["human", "question", "human", "command"] and p[2]["text"] == "Yes, write everything (Recommended)"
          and p[3]["turn"] == 1, "claude: the answer from the question window is the human's")
    write_jsonl(t / "agents.jsonl", [
        {"type": "user", "message": {"content": "read"}},
        {"type": "assistant", "message": {"id": "a1", "content": [
            {"type": "tool_use", "name": "Agent", "input": {"subagent_type": "reader", "description": "x", "run_in_background": False}},
            {"type": "tool_use", "name": "Agent", "input": {"subagent_type": "general-purpose", "description": "y"}}]}}])
    p = tools.steps_claude(t / "agents.jsonl", "/p")
    check([(x["target"], x["text"]) for x in p[1:]] == [("reader", "foreground"), ("general-purpose", "background")],
          "claude: the agent by its type, and without run_in_background: false it starts in the background")
    # Vibe: an entry shows up once, but the bench collects the output of several calls. The agents of
    # the framework are `vibe --agent` runs from the terminal, so they are read from the command.
    write_jsonl(t / "vibe.jsonl", [
        {"id": "u1", "sessionId": "s", "type": "message", "role": "user", "content": [{"type": "text", "text": "do something"}]},
        {"id": "g1", "sessionId": "s", "type": "reasoning", "text": "I am thinking"},
        {"id": "e1", "sessionId": "s", "type": "effect", "detail": {"toolName": "skill", "input": {"name": "brainstorming"}}},
        {"id": "a1", "sessionId": "s", "type": "message", "role": "assistant", "content": [{"type": "text", "text": "Using brainstorming to ask."}]},
        {"id": "e2", "sessionId": "s", "type": "effect", "detail": {"toolName": "file_system.write_file", "input": {"filePath": "/p/records/x.md", "content": "x"}}},
        {"id": "e3", "sessionId": "s", "type": "effect", "detail": {"toolName": "ask_user_question", "input": {"questions": [{"question": "What do you want?"}]}}},
        {"id": "e3", "sessionId": "s", "type": "effect", "state": {"status": "completed"},
         "detail": {"toolName": "ask_user_question", "input": {"questions": [{"question": "What do you want?"}]}}},
        {"id": "e4", "sessionId": "s", "type": "effect", "detail": {"toolName": "file_system.bash", "input": {"command": "vibe --agent reader -p 'search' --trust --max-price 0.20 </dev/null"}}},
        {"id": "e5", "sessionId": "s", "type": "effect", "detail": {"toolName": "file_system.bash", "input": {"command": "vibe --agent execute -p 'x' --auto-approve > log 2>&1 &"}}},
        {"id": "e6", "sessionId": "s", "type": "effect", "detail": {"toolName": "file_system.bash", "input": {"command": "git status && echo done 2>&1"}}},
        {"id": "u2", "sessionId": "s", "type": "message", "role": "user", "content": [{"type": "text", "text": "1"}]},
        "not an entry"])
    p = tools.steps_vibe(t / "vibe.jsonl", "/p")
    check([x["kind"] for x in p] == ["human", "skill", "text", "write", "question", "subagent", "subagent", "command", "human"],
          "vibe: the kinds of the steps, in order")
    check(p[1]["target"] == "brainstorming" and p[3]["target"] == "records/x.md" and p[4]["text"] == "What do you want?",
          "vibe: the skill by its name, the relative path, the text of the question")
    check(p[1]["row"] == 0 and p[2]["row"] == p[3]["row"] == 1 and p[-1]["turn"] == 1,
          "vibe: a new response at the text after tools, and the turn grows with each message of the human")
    check([(x["target"], x["text"]) for x in p[5:7]] == [("reader", "foreground"), ("executor", "background")],
          "vibe: `vibe --agent` from the terminal is a framework agent, and with `&` at the end it starts in the background")
    # A long run, started with `tools.process.start` (bash cuts at 300 s), is also a framework agent.
    write_jsonl(t / "vibe2.jsonl", [
        {"id": "u1", "sessionId": "s", "type": "message", "role": "user", "content": [{"type": "text", "text": "do something"}]},
        {"id": "e1", "sessionId": "s", "type": "effect", "detail": {"toolName": "process.start", "kind": "process",
         "input": {"command": "vibe --agent execute -p 'x' --auto-approve --max-price 2 </dev/null", "cwd": "/p"}}}])
    p = tools.steps_vibe(t / "vibe2.jsonl", "/p")
    check([(x["kind"], x["target"], x["text"]) for x in p[1:]] == [("subagent", "executor", "foreground")],
          "vibe: `process.start` with `vibe --agent` is a framework agent, in the foreground")

    # The reminder of the framework, sent by the hook, is a step of its own, with no new human turn. The
    # `attachment` line with the same text and a file read that contains it are not reminders.
    write_jsonl(t / "reminder.jsonl", [
        {"type": "user", "message": {"content": "write"}},
        {"type": "assistant", "message": {"id": "a1", "content": [{"type": "tool_use", "name": "Read", "input": {"file_path": "/p/bin/reminder.py"}}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "content": 'PERCENT = "Tell the human how much is done, in percent"'}]}},
        {"type": "user", "isMeta": True, "message": {"content": "Stop hook feedback:\nTell the human how much is done, in percent, and how long it takes."}},
        {"type": "attachment", "attachment": {"type": "hook_blocking_error", "hookEvent": "Stop", "blockingError": {
            "blockingError": "Tell the human how much is done, in percent, and how long it takes."}}},
        {"type": "assistant", "message": {"id": "a2", "content": [{"type": "text", "text": "40% done."}]}}])
    p = tools.steps_claude(t / "reminder.jsonl", "/p")
    check([x["kind"] for x in p] == ["human", "read", "reminder", "text"] and p[-1]["turn"] == 0,
          "claude: the hook's reminder is a step of its own, once, with no new turn. The result of a tool is not a reminder")
    write_jsonl(t / "vibe3.jsonl", [
        {"id": "u1", "sessionId": "s", "type": "message", "role": "user", "content": [{"type": "text", "text": "write"}]},
        {"id": "a1", "sessionId": "s", "type": "message", "role": "assistant", "content": [{"type": "text", "text": "I wrote it."}]},
        {"id": "n1", "sessionId": "s", "type": "notice", "detail": {"kind": "hook_run_started", "hookName": None}},
        {"id": "n2", "sessionId": "s", "type": "notice", "detail": {
            "kind": "hook_completed", "hookName": "reminder", "content": "Requested turn revision"}},
        {"id": "a2", "sessionId": "s", "type": "message", "role": "assistant", "content": [{"type": "text", "text": "I use plans."}]}])
    p = tools.steps_vibe(t / "vibe3.jsonl", "/p")
    check([(x["kind"], x["row"], x["turn"]) for x in p] == [("human", -1, 0), ("text", 0, 0), ("reminder", 0, 0), ("text", 1, 0)],
          "vibe: the notice of the framework hook is the reminder, with no new turn, and the response after it is a new one")
    from_entries = getattr(tools, "steps_from_entries", lambda *a: [])
    p = from_entries([
        {"id": "e1", "type": "effect", "detail": {"toolName": "skill.read", "input": {"name": "plans"}}},
        {"id": "e2", "type": "effect", "detail": {"toolName": "file_system.read_file", "input": {"path": "/p/README.md"}}},
        {"id": "e3", "type": "effect", "detail": {"toolName": "edit", "input": {"file_path": "/p/x.py"}}}], "/p")
    check([(x["kind"], x["target"]) for x in p] == [("skill", "plans"), ("read", "README.md"), ("write", "x.py")],
          "vibe: the tools with the raw names and arguments of the session log")

print("the checks")
check(checks.commit_messages('git commit -m "feat: x"') == ["feat: x"]
      and checks.commit_messages("git -C d commit -qm 'This message'") == ["This message"]
      and checks.commit_messages("git commit -m \"$(cat <<'EOF'\nLong message\nEOF\n)\"") == ["Long message"]
      and checks.commit_messages("git status") == [],
      "commit messages: -m, -qm, heredoc, and nothing without a commit")
long_message = "The server works, because the key closed the administration panel"
check(state("commit-without-prefix", [step("command", 'git commit -m "feat: add x"')]) is False
      and state("commit-without-prefix", [step("command", f'git commit -qm "{long_message}"')]) is True,
      "commit-without-prefix: feat: fails, a sentence passes")
check(state("git-state", [step("command", "git status -sb"), step("write", "x")]) is True
      and state("git-state", [step("write", "x"), step("command", "git status")]) is False,
      "git-state: git status before the first write")
check(state("impact-read", [step("command", "cat IMPACT.md"), step("write", "x")]) is True
      and state("impact-read", [step("write", "x")]) is False, "impact-read: with cat or with Read, before the write")
announcement = [step("skill", "brainstorming", row=0), step("text", text="Using superpowers:brainstorming to x", row=3)]
check(state("skill-announced", announcement) is True and state("skill-announced-in-time", announcement) is False,
      "skill-announced: the announcement in the same turn, and in time only in the next response")
spec = "records/work/open/2026-10-02-x/2026-10-02-x-design.md"
check(state("spec-folder", [step("write", "records/work/open/2026-10-02-x/request.md"), step("write", spec)], new_request=True) is True
      and state("spec-folder", [step("write", "records/work/open/2026-10-02-x/spec.md")]) is False,
      "spec-folder: <folder>-design.md with request.md, and another name fails")
check(state("only-records-in-spec", [step("write", spec), step("write", "src/x.sh")]) is False,
      "only-records-in-spec: a code file fails")
questions = [step("text", text="What do you want?", turn=0), step("human", text="x", turn=1), step("text", text="And how much?", turn=1),
             step("human", text="y", turn=2), step("write", spec, turn=2)]
check(state("questions-before-spec", questions) is True, "questions-before-spec: two turns with questions")
check(state("one-question-per-message", [step("text", text="What do you want?\nAnd when?")]) is False
      and state("one-question-per-message", [step("text", text="## The first question?\nWhat do you want?")]) is True,
      "one-question-per-message: two questions fail, and the heading is not counted")
check(state("test-before-code", [step("write", "tests/test-x.sh"), step("command", "bash tests/test-x.sh"), step("write", "x.sh")]) is True
      and state("test-before-code", [step("write", "x.sh"), step("write", "tests/test-x.sh")]) is False,
      "test-before-code: the test written and run first")
check(state("yes-before-merge", [step("human", text="yes"), step("command", "git merge --ff-only x")]) is True
      and state("yes-before-merge", [step("human", text="1"), step("command", "git push")]) is False,
      "yes-before-merge: the merge only after \"yes\"")
check(state("branch-before-commit", [step("command", "git switch -c execute/x"), step("command", f'git commit -m "{long_message}"')]) is True,
      "branch-before-commit: the branch first")

print("the checks repaired after the second Vibe test")
stages = {e: {v["name"] for v in checks.check([], e, {})} for e in checks.ALL}
check({"state-read", "end-of-session"} <= stages["spec"] & stages["plans"]
      and not {"state-read", "end-of-session"} & stages["execute"],
      "state-read and end-of-session are not judged at execution: the executor receives the path of the plan and does not close the session")
check("impact-read" in stages["execute"], "impact-read is also judged at execution")
check(state("skill-announced-in-time", [step("skill", "execute", row=0), step("text", text="I load the `execute` skill and read the plan.", row=1)]) is True
      and state("skill-announced", [step("skill", "plans"), step("skill", "end-of-session"),
                                    step("text", text="I load the skills `plans` and `end-of-session`.")]) is True,
      "skill-announced: \"I load the skill x\", and a list of skills in a single sentence")
check(state("skill-announced", [step("skill", "plans"), step("text", text="I write the plans of the work item.")]) is False
      and state("skill-announced", [step("skill", "plans"), step("text", text="I use the Read tool. Then plans.")]) is False,
      "skill-announced: with no verb of use, or with the verb in another sentence than the name, it is no announcement")
curl_page = "curl -sL https://restic.net | head"
check(state("reader-after-two-pages", [step("search", "restic"), step("page", "https://restic.net")]) is True
      and state("reader-after-two-pages", [step("subagent", "reader"), step("search", "a"), step("page", "b")]) is True,
      "reader-after-two-pages: two pages read directly pass, and the reader is not counted")
check(state("reader-after-two-pages", [step("search", "restic"), step("page", "https://restic.net"), step("command", curl_page)]) is False,
      "reader-after-two-pages: the third page read directly fails, and so does one taken with curl")
try:
    required = {m: {v["name"] for v in checks.check([], "spec", {}, manners=m) if v["required"]} for m in (True, False)}
except TypeError:
    required = {True: set(), False: set()}
manners = getattr(checks, "MANNERS", {"MANNERS missing"})
check(manners <= required[True] and not manners & required[False],
      "--manners makes the checks of manners required, and without it they stay informational")

after_reminder = [step("skill", "plans", row=0), step("text", text="I write.", row=1), step("text", text="Done.", row=4),
                  step("reminder", text="You loaded the plans skill without announcing it", row=4),
                  step("text", text="I use plans to write the plans of the work item.", row=5)]
check(state("skill-announced-in-time", after_reminder) is True,
      "skill-announced-in-time: the announcement in the response after the reminder is good")
check(state("skill-announced-in-time", after_reminder[:3] + [step("text", text="I use plans now.", row=5)]) is False,
      "with no reminder, an announcement that comes four responses later stays late")
check(getattr(checks, "PERCENT", None) is not None and checks.PERCENT.search("done 40 %")
      and not checks.PERCENT.search("step 4"), "PERCENT: a number followed by %, with or without a space")

print("the search stage")
check("search" in checks.ALL and {"helper-called", "answer-correct", "reader-after-two-pages", "framework-subagents"}
      <= {v["name"] for v in checks.check([], "search", {}) if v["required"]},
      "search stage: the helper, the answer, the reader and the framework agents are required")
check(not any(v["name"] == "reader-after-two-pages" and v["required"] for v in checks.check([], "spec", {})),
      "reader-after-two-pages stays informational outside the search, without --manners")
check(state("helper-called", [step("subagent", "reader", "foreground")], helper=["reader"]) is True
      and state("helper-called", [step("subagent", "executor", "foreground")], helper=["reader"]) is False
      and state("helper-called", []) is None,
      "helper-called: the agent the task asks for, called. Another does not take its place. Without a request it is not judged")
check(state("answer-correct", [step("text", text="Ana: 80 hours.")], answer=[r"Ana\D{0,40}\b80\b"]) is True
      and state("answer-correct", [step("text", text="Ana: 79 hours.")], answer=[r"Ana\D{0,40}\b80\b"]) is False
      and state("answer-correct", []) is None,
      "answer-correct: the patterns of the task, searched in the texts of the model")
with tempfile.TemporaryDirectory() as tmp:
    check(state("answer-correct", [], probe="test -f done.txt", folder=tmp) is False
          and (pathlib.Path(tmp) / "done.txt").write_text("") == 0
          and state("answer-correct", [], probe="test -f done.txt", folder=tmp) is True,
          "answer-correct: the probe of the task, run in the project at the end")
check([tools.framework_agent(x) for x in ("reader", "execute", "execute-fast", "qwen-agent-execute-medium",
                                          "qwen-rapid-worker-low", "helper", "qwen-agent-gvs5h-high", "spec")]
      == ["reader", "executor", "executor", "executor", "worker", "helper", "qwen-agent-gvs5h-high", "spec"],
      "framework_agent: the agent from the name of the Vibe profile, on a house model too, at any level")
p = tools.steps_from_entries([{"type": "effect", "detail": {"toolName": "bash", "input": {
    "command": 'vibe --agent helper -p "it does not work for me" --max-price 0.50 </dev/null'}}}])
check(p and p[0]["kind"] == "subagent" and p[0]["target"] == "helper" and p[0]["text"] == "foreground",
      "vibe --agent helper, started from the terminal, is a framework subagent")
check(state("framework-subagents", [step("subagent", "helper", "foreground", row=1), step("subagent", "worker", "foreground", row=2)]) is True,
      "framework-subagents: the helper and the worker of the GVS5H method are the framework's")

print("the checks, on the real sessions of Claude")
check(checks.commit_messages("python3 - <<'EOF'\nimport sys\nEOF\ngit commit -qm 'This message'") == ["This message"],
      "commit messages: the heredoc of another command is not the message")
check(checks.commit_messages('cd "$P" && git -c user.name=trial -c user.email=p@l commit -qm "trial: STATE"') == [],
      "commit messages: a commit with a test identity sits in the throwaway copy and is not judged")
check(state("impact-read", [step("write", "/tmp/claude-1/s/scratchpad/note.md"), step("write", "/h/.claude/projects/-h/memory/x.md"),
                            step("command", "cat IMPACT.md"), step("write", "x")]) is True,
      "first change: the temporary folder and the memory do not change a repository")
check(state("framework-subagents", [step("subagent", "reader", "foreground", row=1), step("subagent", "executor", "foreground", row=2)]) is True
      and state("framework-subagents", []) is True,
      "framework-subagents: the framework agents, one at a time, in the foreground")
check(state("framework-subagents", [step("subagent", "general-purpose", "foreground")]) is False
      and state("framework-subagents", [step("subagent", "reader", "background")]) is False
      and state("framework-subagents", [step("subagent", "reader", "foreground"), step("subagent", "executor", "foreground")]) is False,
      "framework-subagents: another agent, one in the background, or two in the same response fail")
check(state("skill-announced", [step("skill", "ponytail")]) is None
      and state("skill-announced", [step("skill", "end-of-session", row=1), step("text", text="I use `end-of-session` to close", row=1)]) is True
      and state("skill-announced", [step("skill", "writing-plans", row=1), step("text", text="I'm using the writing-plans skill to create the plan.", row=2)]) is True,
      "skill-announced: the modes are not announced, and the announcement in the form of writing-plans counts")
check(state("text-beside-writes", [step("text", text="I write round.md.", row=1), step("command", "mkdir x", row=1),
                                   step("write", "round.md", row=2), step("command", "ls", row=3)]) is True,
      "text-beside-writes: the announcement in the response before counts")
check(state("end-of-session", [step("skill", "end-of-session"), step("write", "/tmp/s/STATE.new.md"),
                               step("command", "cp /tmp/s/STATE.new.md STATE.md && git add STATE.md")]) is True,
      "end-of-session: the state file copied from a draft counts")
check(state("one-question-per-message", [step("text", text="**The first question: how do you tell it works?**\n\nI recommend 1. What do you choose?")]) is True,
      "one-question-per-message: the bold heading is not counted")
check(state("one-question-per-message", [step("text", text="I wait for your answer. How do you want to store the files?\n\nWhat do you choose?")]) is True,
      "one-question-per-message: the urge to choose after the question is not counted")
check(state("one-question-per-message", [step("text", text="The next question: the laptop sleeps. **What happens with the lost hour?**\n\n- A. It stays empty.\n- B. It is noted at wake-up.\n\nA or B?")]) is True
      and state("one-question-per-message", [step("text", text="Choose the architecture. **What do we use?**\n\nA, B or C?")]) is True
      and state("one-question-per-message", [step("text", text="What do you want?\nA or B?\nAnd when?")]) is False,
      "one-question-per-message: \"A or B?\" after the variants asks the answer to the same question, it is not another one")
SPEC = "/p/records/work/open/2026-10-08-x/2026-10-08-x-design.md"
check(state("search-before-spec", [step("subagent", "reader"), step("write", SPEC)], web_search=True) is True
      and state("search-before-spec", [step("command", "curl -sL https://www.freedesktop.org/man.html | sed 's/<[^>]*>//g'"), step("write", SPEC)], web_search=True) is True
      and state("search-before-spec", [step("subagent", "escalation"), step("command", "ls https://x"), step("write", SPEC)], web_search=True) is False
      and state("search-before-spec", [step("write", SPEC)], web_search=True) is False,
      "search-before-spec: the reader and a page taken with curl are a search, another agent or another command is not")
check(state("spec-folder", [step("write", "/tmp/x.md")]) is None
      and state("spec-folder", [step("write", "/tmp/x.md")], new_request=True) is False,
      "spec-folder: a session with nothing in the folder is not judged, except a new request")
with tempfile.TemporaryDirectory() as tmp:
    d = pathlib.Path(tmp) / "records/work/open/2026-10-02-x"
    d.mkdir(parents=True)
    (d / "2026-10-02-x-1.md").write_text("**Execution:** x\n**Closing:** x\n**Branch:** x\n**Who:** x\n**Verifier:** x\n")
    (d / "HANDOFF-x.md").write_text("the handoff\n")
    (d / "request.md").write_text("the request\n")
    plan = [step("write", f"records/work/open/2026-10-02-x/{f}") for f in ("2026-10-02-x-1.md", "HANDOFF-x.md", "request.md", "README.md")]
    check(state("plan-form", plan, folder=tmp) is True,
          "plan-form: the five labels of the plan are there, and the handoff and the request are not plans")
    check(state("code-in-plan", plan, folder=tmp) is None
          and state("code-in-plan", plan, folder=tmp, plan_with_code=True) is False,
          "code-in-plan: a plan with no code is not judged, except a task that asks for code")
    y = pathlib.Path(tmp) / "records/work/open/2026-10-03-y"
    y.mkdir(parents=True)
    (y / "2026-10-03-y.md").write_text("**Execution:** x\n**Closing:** x\n**Branch:** x\n**Who:** x\n**Verifier:** x\n```bash\n./test\n```\n")
    script = [step("read", "skills/documentation/references/details.md"), step("command", "git worktree add --detach /tmp/c"),
              step("write", "records/work/open/2026-10-03-y/README.md"), step("command", 'python3 fill.py template.md "$D/2026-10-03-y.md"')]
    check(state("code-in-plan", script[2:], folder=tmp, plan_with_code=True) is True,
          "code-in-plan: the plan leaves unproved, so no throwaway copy is asked for")
    check(all(state(v, script, folder=tmp, plan_with_code=True) is True
              for v in ("code-in-plan", "plan-form", "details-before-plan")),
          "plans: a plan put on disk by a script is read from the folder where the session wrote")
check(state("test-before-code", [step("write", "bot/queue_test.go"), step("command", "go test ./..."), step("write", "bot/queue.go")]) is True,
      "test-before-code: the Go test, x_test.go")
check(state("test-before-code", [step("write", "test"), step("write", "tests/test-x.sh"), step("command", "./test"),
                                 step("write", "x.sh")]) is True,
      "test-before-code: the collector ./test of the project is not code")
check(state("branch-before-commit", [step("human", text="Continue the plan on the branch execute/x, from task 7."), step("command", f'git commit -m "{long_message}"')]) is True
      and state("branch-before-commit", [step("command", "git switch execute/x"), step("command", f'git commit -m "{long_message}"')]) is True
      and state("branch-before-commit", [step("human", text="Execute the plan."), step("command", f'git commit -m "{long_message}"')]) is False,
      "branch-before-commit: a continuation on the branch named in the prompt, or the move to it")
check(state("yes-before-merge", [step("human", text="1"), step("command", "B=$(git merge-base main x)")]) is None
      and state("yes-before-merge", [step("human", text="stop, commit and push, I am leaving"), step("command", "git push")]) is True,
      "yes-before-merge: merge-base is not a merge, and a request of the human to push takes the place of \"yes\"")

wrong = [step("human", text="yes", turn=1), step("write", "records/work/open/2026-10-03-x/x-design.md", turn=1)]
check(all(state(v, wrong, new_request=True) is False for v in ("questions-before-spec", "design-approved", "spec-shown-to-human"))
      and all(state(v, wrong) is None for v in ("questions-before-spec", "design-approved", "spec-shown-to-human")),
      "a task with a new request and no <folder>-design.md fails the spec checks, and an old session is not judged")

print("the checks nobody had written, found by reading the sessions of Claude")
check(state("percent-told", [step("text", text="Progress: about 20%. About 30 minutes left.")]) is True
      and state("percent-told", [step("text", text="Done.")]) is False,
      "percent-told: how much is done, in percent")
check(state("design-approved", [step("text", text="The design, piece 1. Is it good?"), step("human", text="yes", turn=1), step("write", spec, turn=1)]) is True
      and state("design-approved", [step("human", text="1", turn=1), step("write", spec, turn=1)]) is False,
      "design-approved: a \"yes\" of the human before the spec")
check(state("spec-shown-to-human", [step("write", spec), step("human", text="yes", turn=1), step("skill", "end-of-session", turn=1)]) is True
      and state("spec-shown-to-human", [step("write", spec), step("skill", "end-of-session")]) is False,
      "spec-shown-to-human: the human answers after the spec, before the closing")
check(state("spec-shown-to-human", [step("write", spec), step("skill", "end-of-session"), step("human", text="yes", turn=1),
                                    step("write", "STATE.md", turn=1)]) is True
      and state("spec-shown-to-human", [step("write", spec), step("skill", "end-of-session"), step("write", "STATE.md")]) is False,
      "spec-shown-to-human: the spec shown in the report of the closing, before the state file, counts")
check(state("check-docs-run", [step("write", spec), step("command", "python3 bin/check-docs.py . | tail -1")]) is True
      and state("check-docs-run", [step("write", spec), step("command", "git add -A")]) is False,
      "check-docs-run: the check of the documentation after the write in the folder")

checks.register("check-per-stage", checks.ALL, ("spec",), "trial")(lambda steps, ctx: (True, ""))
per_stage = {e: next(v["required"] for v in checks.check([], e, {}) if v["name"] == "check-per-stage") for e in ("spec", "execute")}
checks.CHECKS.pop()
check(per_stage == {"spec": True, "execute": False}, "the required flag can name the stages where it holds")

check(checks.threshold([{"required": True, "state": False}]) is False
      and checks.threshold([{"required": True, "state": None}, {"required": False, "state": False}]) is True,
      "the threshold: only a failed required check fails")

import bench  # noqa: E402
check("](" not in bench.cell("I wrote in [color.txt](file:///tmp/x/color.txt)."),
      "the report quotes the text of the tool without making it a link")
with tempfile.TemporaryDirectory() as tmp:
    (pathlib.Path(tmp) / "project").mkdir()
    (pathlib.Path(tmp) / "project/README.md").write_text("# trial\n")
    house, _ = bench.miniature_house(pathlib.Path(tmp), {"project": "trial", "layers": []})
    workers = house / "records/local-workers.md"
    has_file = workers.is_file() and not any(c.isdigit() for c in workers.read_text())
    shutil.rmtree(house)
    check(has_file, "the miniature house has the workers file, with no worker: execution does not look for the human's own")

print("the quota is searched at the end of the output")
quote = "x" * 10 + "`Price limit exceeded` in the output" + "y" * 5000
try:
    tools.run([sys.executable, "-c", f"print({quote!r}); raise SystemExit(1)"], ".", ndjson=True)
    check(False, "a failed round raises an error")
except tools.QuotaExhausted:
    check(False, "a quote from the skills, at the start of the output, is not a quota")
except RuntimeError:
    check(True, "a quote from the skills, at the start of the output, is not a quota")

print("the cost label")
cost_label = getattr(bench, "cost_label", lambda *a: "")
check(cost_label("vibe", 2.2) == "from the Vibe Code amount: €1.87 estimated",
      "vibe: euros from the Vibe Code amount, estimated")
check(cost_label("claude", 6.12) == "equivalent at the API price: $6.12 — not paid, it reduces the subscription's quota",
      "claude: the equivalent at the API price, which is not paid")
check(cost_label("vibe", None) == "cost: —", "with no cost, a dash")
check(cost_label("vibe", 0) == "house model: €0.00, no Vibe Code amount",
      "vibe, cost 0: a house model, not a Vibe Code amount")

print("the run, with fake tools")
houses_before = set(pathlib.Path("/tmp").glob("bench-*"))
with tempfile.TemporaryDirectory() as tmp:
    t = pathlib.Path(tmp)
    home, fake, space, output, task = t / "home", t / "fake", t / "space", t / "output", t / "task"
    for d in (home, fake, output, task, space / "records/memory"):
        d.mkdir(parents=True)
    for name, code in (("agy", FAKE_AGY), ("claude", FAKE_CLAUDE), ("vibe", FAKE_VIBE)):
        (fake / name).write_text(code)
        (fake / name).chmod(0o755)
    for f in ("AGENTS.md", "CLAUDE.md", "GEMINI.md", "MISTRAL.md", ".gitignore", "plugins.lock.json"):
        if (R / f).is_file():
            shutil.copy2(R / f, space / f)
    for d in ("template", "example"):
        shutil.copytree(R / d, space / d)
    for d in ("bin", "skills", "agents"):
        (space / d).symlink_to(R / d)
    (space / "records/house-rules.md").write_text("# House rules\n")
    (space / "records/memory/MEMORY.md").write_text("- [x](x.md): a memory\n")
    for args in (("init", "-q"), ("add", "-A"), ("-c", "user.name=trial", "-c", "user.email=trial@local", "commit", "-qm", "fabricated space")):
        subprocess.run(["git", "-C", str(space), *args], check=True, capture_output=True)
    (task / "task.json").write_text(json.dumps({"stage": "spec", "project": "trial", "web_search": False,
                                                "prompt": "Ask me what color I like."}))
    (task / "brief.md").write_text("Your color is blue.\n")
    env = dict(os.environ, HOME=str(home), PATH=f"{fake}:{os.environ['PATH']}", BENCH_ROOT=str(space))

    def run_bench(tool, *extra):
        return subprocess.run([sys.executable, str(BENCH), "run", "--tool", tool, "--model", "m",
                               "--task", str(task), "--output", str(output / tool), "--minutes", "5", *extra],
                              env=env, capture_output=True, text=True)

    for tool_name in ("agy", "claude", "vibe"):
        p = run_bench(tool_name)
        runs = sorted((output / tool_name).iterdir()) if (output / tool_name).is_dir() else []
        check(p.returncode == 0 and len(runs) == 1, f"{tool_name}: the run ends with 0 {p.stderr.strip()[-300:]}")
        if runs:
            run_dir = runs[0]
            meta = json.loads((run_dir / "meta.json").read_text())
            check(meta["answers"] == 1 and meta["reason"] == "done", f"{tool_name}: one answer of the simulated human, then DONE")
            check((run_dir / "project/color.txt").read_text().strip() == "blue", f"{tool_name}: the tool received the answer of the human")
            check(all((run_dir / f).is_file() for f in ("report.md", "steps.jsonl", "human.jsonl", "log.jsonl")),
                  f"{tool_name}: the report, the steps, the simulated human and the raw log")
            if tool_name == "vibe":
                check((run_dir / "project/home-vibe.txt").read_text().strip() == "True",
                      "vibe: the VIBE_HOME of the run has the rules written by bin/vibe.sh")
                check(abs((meta["cost"] or 0) - 1.36) < 0.001 and meta["tokens"] == 2_000_000,
                      f"vibe: the cost and the tokens, from the session log and from config.toml (cost {meta['cost']})")
                check(meta.get("eur_estimated") == 1.156
                      and "from the Vibe Code amount: €1.16 estimated" in (run_dir / "report.md").read_text(),
                      "vibe: the cost in euros, estimated, in meta.json and in the report")
            if tool_name == "claude":
                report = (run_dir / "report.md").read_text()
                check("equivalent at the API price:" in report and "cost at the API price" not in report
                      and "eur_estimated" not in meta,
                      "claude: the label says the equivalent at the API price, not a cost. No euros")
    check(any((output / "agy").glob("*/project/.agents/rules/framework-01.md")), "agy: the local files of the project")
    check(any(x.read_text().strip() == "linked" for x in (output / "claude").glob("*/project/memory.txt")),
          "claude: the memory of the key, linked to the copy in the miniature house")
    check(not list((home / ".claude/projects").glob("-tmp-bench-*")), "claude: the key of the bench session is gone")

    # Mandatory manners: with Vibe and `--manners`. Without the option, the report says they are informational.
    p = run_bench("vibe", "--manners")
    run_dir = max((output / "vibe").iterdir())
    meta, report = json.loads((run_dir / "meta.json").read_text()), (run_dir / "report.md").read_text()
    check(p.returncode == 0 and meta.get("manners") is True and "**Manners:** required" in report
          and "| ✗ | `percent-told` | yes |" in report and meta["threshold"] is False,
          f"vibe --manners: the manners are required, and a percent not told fails the threshold {p.stderr.strip()[-300:]}")
    check("**Manners:** informational" in next((output / "claude").glob("*/report.md")).read_text(),
          "without --manners, the report says the manners are informational")

    # Qwen, through the human's house provider: the profile by level, cost €0, the tokens counted.
    (home / ".vibe").mkdir(exist_ok=True)
    (home / ".vibe/config.toml").write_text(
        '[[models]]\nname = "qwen-agent"\nprovider = "casa"\nalias = "qwen-agent"\nthinking = "off"\n'
        'thinking_levels = ["off", "low", "medium", "high"]\n\n'
        '[[providers]]\nname = "casa"\napi_base = "http://127.0.0.1:8091/v1"\napi_style = "openai"\n')
    p = run_bench("vibe", "--model", "qwen-agent", "--effort", "low")
    run_dir = max((output / "vibe").iterdir())
    meta, report = json.loads((run_dir / "meta.json").read_text()), (run_dir / "report.md").read_text()
    check(p.returncode == 0 and (run_dir / "project/agent-vibe.txt").read_text().strip() == "qwen-agent-low",
          f"vibe --model qwen-agent --effort low: runs on the profile qwen-agent-low {p.stderr.strip()[-300:]}")
    check(meta["cost"] == 0 and meta["tokens"] == 2_000_000 and meta["effort"] == "low"
          and "house model: €0.00" in report,
          f"vibe on Qwen: cost €0, the tokens counted (cost {meta['cost']}, tokens {meta['tokens']})")
    p = run_bench("vibe", "--model", "qwen-agent", "--effort", "ultra")
    run_dir = max((output / "vibe").iterdir())
    check("the profile qwen-agent-ultra" in json.loads((run_dir / "meta.json").read_text())["reason"],
          "a level with no profile stops the run, with the name of the profile")
    (home / ".vibe/config.toml").unlink()
    # A search task: task.json stays in the run, and `read` judges it again from there, with the probe.
    search = t / "search"
    search.mkdir()
    (search / "task.json").write_text(json.dumps({"stage": "search", "project": "trial", "prompt": "What color?",
                                                  "helper": ["reader"], "answer": ["Done"], "probe": "test -f color.txt"}))
    (search / "brief.md").write_text("Your color is blue.\n")
    p = subprocess.run([sys.executable, str(BENCH), "run", "--tool", "vibe", "--model", "m", "--task", str(search),
                        "--output", str(output / "search"), "--minutes", "5"], env=env, capture_output=True, text=True)
    run_dir = max((output / "search").iterdir())
    meta = json.loads((run_dir / "meta.json").read_text())
    check(p.returncode == 0 and (run_dir / "task.json").is_file() and meta["checks"].get("answer-correct") is True
          and meta["checks"].get("helper-called") is False and meta["threshold"] is False,
          f"search: task.json in the run. The answer and the probe pass, and the helper not called fails the threshold {p.stderr.strip()[-300:]}")
    c = subprocess.run([sys.executable, str(BENCH), "read", "--tool", "vibe", "--log", str(run_dir / "log.jsonl"),
                        "--stage", "search", "--folder", str(run_dir / "project"), "--task", str(run_dir)],
                       env=env, capture_output=True, text=True)
    check(c.returncode == 0 and "✓ answer-correct" in c.stdout and "✗ helper-called" in c.stdout,
          "read --task <run>: the new judgment takes the helper, the answer and the probe from the copied task.json")
    (home / "fake-quota").write_text("")
    p = run_bench("agy")
    check(p.returncode == 3 and "quota" in p.stdout, "quota used up: code 3")
    p = run_bench("vibe")
    check(p.returncode == 3 and "Price limit exceeded" in p.stdout, "vibe: the price cap reached is also code 3, with its message")
    (home / "fake-quota").unlink()
    (home / "fake-escape").write_text(str(space / "escaped.txt"))
    p = run_bench("agy")
    check(p.returncode == 4 and "outside the miniature house" in p.stdout, "a write outside the miniature house: code 4")
    (home / ".local/bin").mkdir(parents=True)
    (home / "fake-escape").write_text(str(home / ".local/bin/escaped"))
    p = run_bench("agy")
    (home / "fake-escape").unlink()
    check(p.returncode == 4 and "~/.local/bin" in p.stdout, "an installation in the home, outside the repositories: code 4")
    # The panel rewrites the weekly file in `records/` once a minute, so a long run would see it changed.
    reg = space / "records-p"
    (reg / "usage/weeks").mkdir(parents=True)
    (reg / "usage/weeks/z.json").write_text("{}\n")
    for args in (("init", "-q"), ("add", "-A"), ("-c", "user.name=trial", "-c", "user.email=trial@local", "commit", "-qm", "p")):
        subprocess.run(["git", "-C", str(reg), *args], check=True, capture_output=True)
    (home / "fake-escape").write_text(str(reg / "usage/weeks/z.json"))
    p = run_bench("agy")
    check(p.returncode == 0, f"the weekly file of the panel, rewritten during the run, does not make it code 4 {p.stdout.strip()[-200:]}")
    (home / "fake-escape").write_text(str(reg / "other.txt"))
    p = run_bench("agy")
    (home / "fake-escape").unlink()
    check(p.returncode == 4 and "records-p" in p.stdout, "another file in the same repository stays seen: code 4")

    j = next((output / "agy").glob("*/log.jsonl"))
    p = subprocess.run([sys.executable, str(BENCH), "read", "--tool", "agy", "--log", str(j), "--stage", "spec"],
                       env=env, capture_output=True, text=True)
    check(p.returncode == 0 and "spec-folder" in p.stdout and "threshold:" in p.stdout,
          "read: the checks on a log that already exists")
    run_dir = j.parent
    p = subprocess.run([sys.executable, str(BENCH), "read", "--tool", "agy", "--log", str(j), "--stage", "spec",
                        "--folder", str(run_dir / "project"), "--task", str(task)], env=env, capture_output=True, text=True)
    check(p.returncode == 0 and "– search-before-spec: the task does not ask for outside facts" in p.stdout,
          "read --task: judges a run again with the flags of its task")
    check(tools.relative("/tmp/bench-0123456789ab/projects/greeting/records/work/open/x/plan.md", "/r/2026-x/project")
          == "records/work/open/x/plan.md",
          "read: the paths in the deleted house of the run are read from its copy")

    write_jsonl(home / ".claude/projects/-k/session1.jsonl", [
        {"type": "user", "timestamp": "2026-09-25T10:00:00Z", "cwd": "/k", "message": {"content": "let us write the spec"}},
        {"type": "assistant", "timestamp": "2026-09-25T10:30:00Z", "message": {"id": "a", "content": [
            {"type": "tool_use", "name": "Skill", "input": {"skill": "superpowers:brainstorming"}},
            {"type": "tool_use", "name": "Write", "input": {"file_path": "/k/records/work/open/2026-09-25-x/spec.md"}}]}}])
    p = subprocess.run([sys.executable, str(BENCH), "profile", "--after", "2026-09-20", "--output", str(t / "profile.md")],
                       env=env, capture_output=True, text=True)
    text = (t / "profile.md").read_text() if (t / "profile.md").exists() else ""
    check(p.returncode == 0 and "## spec: 1 sessions" in text and "30 minutes" in text
          and "session1.jsonl`" in text and "spec-folder" in text.split("failed:")[-1],
          "profile: the spec session counted, with its log, the minutes and the failed checks")

# ── the whole journey: the sessions in turn, the handoff read by the bench, the acceptance ──
# The fake tool plays three sessions: the spec hands off the plans, the plans hand off the orchestration,
# and the orchestration makes a commit in `main` and starts an `escalation` agent. The call with
# `--json-schema` reads the handoff from STATE.md, where the fake session writes "HANDOFF: <role>".
FAKE_CLAUDE_JOURNEY = r"""#!/usr/bin/env python3
import json, os, pathlib, subprocess, sys
a = sys.argv[1:]
home = pathlib.Path.home()
with open(home / "argv.log", "a") as f:
    f.write(json.dumps(a) + "\n")
text = a[a.index("-p") + 1].strip()
if "--json-schema" in a:
    for role, effort in (("plans", "high"), ("orchestration", "medium")):
        if "HANDOFF: " + role in text:
            print(json.dumps({"is_error": False, "structured_output": {"next": True, "role": role,
                  "model": "opus", "effort": effort, "prompt": "Prompt for " + role}}))
            sys.exit(0)
    print(json.dumps({"is_error": False, "structured_output": {"next": False}}))
    sys.exit(0)
if "--system-prompt" in a:
    print(json.dumps({"is_error": False, "result": "DONE" if "done" in text.lower() else "yes"}))
    sys.exit(0)
if (home / "fake-network").exists():
    (home / "fake-network").unlink()
    print(json.dumps({"is_error": True, "result": "API Error: Can't reach the API server (EAI_AGAIN)"}))
    sys.exit(1)
if (home / "fake-quota").exists() and "orchestration" in text:
    print("Claude usage limit reached", file=sys.stderr)
    sys.exit(1)
cwd = pathlib.Path.cwd()
key = home / ".claude/projects" / str(cwd).replace("/", "-")
key.mkdir(parents=True, exist_ok=True)
new = "--session-id" in a
sid = a[a.index("--session-id" if new else "--resume") + 1]
j = key / (sid + ".jsonl")
rows = j.read_text().splitlines() if j.exists() else []
def entry(model, effort):
    return json.dumps({"type": "assistant", "perTurnEffort": effort, "message": {"id": sid + str(len(rows)),
        "model": model, "usage": {"input_tokens": 0, "output_tokens": 1000, "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 0}, "content": [{"type": "text", "text": "working"}]}})
rows.append(json.dumps({"type": "user", "message": {"role": "user", "content": text}}))
rows.append(entry("claude-opus-5-5", "high"))
if not new:
    result = "I finished. Done."
elif "orchestration" in text:
    (cwd / "result.txt").write_text("ok\n")
    subprocess.run(["git", "add", "result.txt"], check=True)
    subprocess.run(["git", "-c", "user.name=p", "-c", "user.email=p@l", "commit", "-qm", "result"], check=True)
    (cwd / "STATE.md").write_text("## The next session\n\nNo session follows.\n")
    agents = key / sid / "subagents"
    agents.mkdir(parents=True, exist_ok=True)
    (agents / "agent-u1.jsonl").write_text(entry("claude-opus-5-5", "medium") + "\n")
    (agents / "agent-u1.meta.json").write_text(json.dumps({"agentType": "escalation"}))
    result = "The work item is merged into main. Shall I close?"
else:
    following = "orchestration" if "plans" in text else "plans"
    (cwd / "STATE.md").write_text("## The next session\n\nHANDOFF: " + following + "\n")
    result = "I wrote it. Shall I hand off?"
rows.append(json.dumps({"type": "assistant", "message": {"id": sid + "t" + str(len(rows)),
               "content": [{"type": "text", "text": result}]}}))
j.write_text("\n".join(rows) + "\n")
print(json.dumps({"session_id": sid, "result": result, "is_error": False, "total_cost_usd": 0.02}))
"""


# Fake Vibe for the journey: the same three sessions as FAKE_CLAUDE_JOURNEY, with the `streaming` output.
# The orchestration starts the escalation from the terminal. Each call adds 1,000,000 tokens to the
# output, that is $2.09 on Large 4.
FAKE_VIBE_JOURNEY = r"""#!/usr/bin/env python3
import json, os, pathlib, subprocess, sys, uuid
a = sys.argv[1:]
if "--resume" in a and os.environ.get("VIBE_CLI") != "python":  # the Rust TUI of 2.26 refuses -p with --resume
    print("error: the argument '--prompt [<PROMPT>]' cannot be used with '--resume [<RESUME>]'", file=sys.stderr)
    sys.exit(2)
home = pathlib.Path(os.environ["VIBE_HOME"])
with open(pathlib.Path.home() / "argv-vibe.log", "a") as f:
    f.write(json.dumps(a) + "\n")
text = a[a.index("-p") + 1].strip()
sid = a[a.index("--resume") + 1] if "--resume" in a else str(uuid.uuid4())
d = home / "logs/session/unified" / sid
g = d / "generations/0000000000000001"
g.mkdir(parents=True, exist_ok=True)
(d / "CURRENT").write_text(json.dumps({"generation": "0000000000000001"}))
(d / "meta.json").write_text(json.dumps({"session_id": sid, "start_time": "2026-10-08T10:00:00+00:00"}))
(g / "runtime-state.json").write_text(json.dumps({"session_metadata": {"active_model": "large-4"}}))
u = g / "projection-state.json"
n = json.loads(u.read_text())["snapshot"]["session"]["tokenUsage"]["outputTokens"] if u.exists() else 0
u.write_text(json.dumps({"snapshot": {"session": {"tokenUsage": {
    "inputTokens": 0, "cachedInputTokens": 0, "outputTokens": n + 1_000_000}}}}))
def emit(kind, **r):
    print(json.dumps({"id": str(uuid.uuid4()), "sessionId": sid, "type": kind, **r}, ensure_ascii=False))
emit("message", role="user", content=[{"type": "text", "text": text}])
cwd = pathlib.Path.cwd()
if "--resume" in a:
    result = "I finished. Done."
elif "orchestration" in text:
    (cwd / "result.txt").write_text("ok\n")
    subprocess.run(["git", "add", "result.txt"], check=True)
    subprocess.run(["git", "-c", "user.name=p", "-c", "user.email=p@l", "commit", "-qm", "result"], check=True)
    (cwd / "STATE.md").write_text("## The next session\n\nNo session follows.\n")
    emit("reasoning", text="I start the escalation")
    emit("effect", detail={"toolName": "file_system.bash", "input": {
        "command": "vibe --agent escalation -p 'Resume plan p.md from task 2.' --auto-approve --trust --max-price 3 </dev/null"}})
    result = "The work item is merged into main. Shall I close?"
else:
    following = "orchestration" if "plans" in text else "plans"
    (cwd / "STATE.md").write_text("## The next session\n\nHANDOFF: " + following + "\n")
    result = "I wrote it. Shall I hand off?"
emit("message", role="assistant", content=[{"type": "text", "text": result}])
"""

print("the whole journey, with a fake tool")
with tempfile.TemporaryDirectory() as tmp:
    t = pathlib.Path(tmp)
    home, fake, space, output, trial = t / "home", t / "fake", t / "space", t / "output", t / "trial-project"
    for d in (home / ".claude/rules", fake, output, trial / "acceptance", space / "records/memory", space / "agents"):
        d.mkdir(parents=True)
    (fake / "claude").write_text(FAKE_CLAUDE_JOURNEY)
    (fake / "claude").chmod(0o755)
    for f in ("AGENTS.md", "CLAUDE.md", "MISTRAL.md", ".gitignore", "plugins.lock.json"):
        shutil.copy2(R / f, space / f)
    shutil.copytree(R / "template", space / "template")
    for d in ("bin", "skills"):
        (space / d).symlink_to(R / d)
    (space / "agents/executor.md").write_text("---\nname: executor\n---\n")
    (space / "records/house-rules.md").write_text("# House rules\n")
    (home / ".claude/rules/rule.md").write_text("# A rule of the human\n")
    (home / ".claude/RTK.md").write_text("# RTK\n")
    (home / ".claude/CLAUDE.md").write_text("@RTK.md\n")
    for args in (("init", "-q"), ("add", "-A"), ("-c", "user.name=trial", "-c", "user.email=trial@local", "commit", "-qm", "fabricated space")):
        subprocess.run(["git", "-C", str(space), *args], check=True, capture_output=True)
    note = t / "note.md"
    note.write_text("# The variant's note\n")
    (trial / "project.json").write_text(json.dumps({"name": "dp", "request": "The request of the human: a result.", "layers": []}))
    (trial / "brief.md").write_text("You say yes to everything.\n")
    (trial / "acceptance/probe.py").write_text(
        "import pathlib, sys\nok = (pathlib.Path(sys.argv[1]) / 'result.txt').is_file()\n"
        "print('1 of 1 passed' if ok else '0 of 1 passed')\nsys.exit(0 if ok else 1)\n")
    env = dict(os.environ, HOME=str(home), PATH=f"{fake}:{os.environ['PATH']}", BENCH_ROOT=str(space), BENCH_PAUSE="0")
    old_home, os.environ["HOME"] = os.environ["HOME"], str(home)  # the rules of the human are read from HOME
    house, project = bench.miniature_house(trial, {"project": "dp", "layers": []}, space, note)
    os.environ["HOME"] = old_home
    settings = json.loads((house / ".claude/settings.json").read_text())
    check((house / ".claude/skills/execute/SKILL.md").is_file() and (house / ".claude/agents/executor.md").is_file(),
          "the miniature house has the skills and the agents of the variant in .claude/")
    check((house / ".claude/rules/variant-note.md").read_text() == "# The variant's note\n"
          and (house / ".claude/rules/rule.md").is_file() and "# RTK" in (house / ".claude/rules/personal.md").read_text(),
          "the variant's note, the rules of the human and his CLAUDE.md, with the imports expanded, sit in .claude/rules/")
    check(settings.get("enabledPlugins") and "agents-md@builtin" in settings.get("pluginConfigs", {}),
          "the settings of the variant come from its own merge-claude-config.py: the plugins and AGENTS.md")
    check(subprocess.run(["git", "-C", str(project), "symbolic-ref", "--short", "HEAD"], capture_output=True,
                         text=True).stdout.strip() == "main", "the project of the miniature house starts on main")
    shutil.rmtree(house)

    def journey(*extra):
        return subprocess.run([sys.executable, str(BENCH), "journey", "--project", str(trial), "--variant", str(space),
                               "--note", str(note), "--label", "new", "--output", str(output), "--model", "opus",
                               "--effort", "high", "--minutes", "5", *extra], env=env, capture_output=True, text=True)

    p = journey()
    runs = sorted(output.iterdir())
    check(p.returncode == 0 and len(runs) == 1, f"the journey ends with 0 {p.stdout.strip()[-200:]} {p.stderr.strip()[-300:]}")
    d = json.loads((runs[0] / "journey.json").read_text()) if runs else {"sessions": []}
    check([(s["role"], s["model"], s["effort"]) for s in d["sessions"]]
          == [("spec", "opus", "high"), ("plans", "opus", "high"), ("orchestration", "opus", "medium")],
          "three sessions, each with the role, the model and the effort from the handoff of the one before")
    check(d.get("acceptance", {}).get("code") == 0, "the acceptance runs on the main at the end and passes")
    check(d.get("escalations") == 1 and d.get("returns") == 0,
          "one escalation, counted from the agents of the orchestration, and no return")
    check(d["sessions"] and abs(d["sessions"][-1]["cost"] - 0.06) < 0.001 and d["sessions"][-1].get("tokens") == 3000,
          "the cost and the tokens of the orchestration, from the logs: two of its steps and one of the agent, $0.02 and 1,000 tokens each")
    check((runs[0] / "report.md").is_file() and (runs[0] / "sessions/03-orchestration/agents/agent-u1.jsonl").is_file(),
          "the report and the logs of each session, with its agents")
    argv = [json.loads(r) for r in (home / "argv.log").read_text().splitlines()]
    sessions = [x for x in argv if "--system-prompt" not in x]
    check(all("--setting-sources" in x and x[x.index("--setting-sources") + 1] == "project,local"
              and x[x.index("--settings") + 1].endswith(".claude/settings.json") and "--add-dir" in x for x in sessions),
          "each session starts with the house of the variant: --setting-sources project,local, --settings, --add-dir")
    check(not list((home / ".claude/projects").glob("-tmp-bench-*")) and not d.get("space_left"),
          "at the end the miniature house leaves, and its key too")

    (home / "fake-quota").write_text("")
    (home / "fake-network").write_text("")
    p = journey()
    second = sorted(set(output.iterdir()) - set(runs))
    d = json.loads((second[0] / "journey.json").read_text()) if second else {}
    check(p.returncode == 3 and d.get("state") == "quota" and pathlib.Path(d.get("space", "/no")).is_dir(),
          "the quota used up stops the journey with 3 and keeps the house, to resume")
    (home / "fake-quota").unlink()
    p = subprocess.run([sys.executable, str(BENCH), "journey", "--resume", str(second[0]) if second else "/no"],
                       env=env, capture_output=True, text=True)
    d = json.loads((second[0] / "journey.json").read_text()) if second else {}
    check(p.returncode == 0 and len(d.get("sessions", [])) == 3 and d.get("acceptance", {}).get("code") == 0,
          f"--resume takes the journey to the end, after a network failure that was retried {p.stderr.strip()[-300:]}")

    p = subprocess.run([sys.executable, str(BENCH), "blind", "--a", str(runs[0]), "--b", str(second[0]) if second else "/no",
                        "--output", str(t / "blind"), "--key", str(t / "key.json")], env=env, capture_output=True, text=True)
    key = json.loads((t / "key.json").read_text()) if (t / "key.json").is_file() else {}
    check(p.returncode == 0 and (t / "blind/A/result.txt").is_file() and (t / "blind/B/result.txt").is_file()
          and not (t / "blind/A/records").exists() and sorted(key.values()) == sorted([str(runs[0]), str(second[0])]),
          "blind: A and B, without the records, and the key apart")

    # The journey on a single model: each Claude session stays on --model and --effort, whatever the handoff asks.
    old_runs, old_argv = set(output.iterdir()), len((home / "argv.log").read_text().splitlines())
    p = journey("--model", "haiku", "--effort", "medium", "--same-model")
    new = sorted(set(output.iterdir()) - old_runs)
    dh = json.loads((new[0] / "journey.json").read_text()) if new else {"sessions": []}
    argv = [json.loads(r) for r in (home / "argv.log").read_text().splitlines()[old_argv:]]
    sessions = [x for x in argv if "--system-prompt" not in x and "--json-schema" not in x]
    check(p.returncode == 0 and [(s["role"], s["model"], s["effort"]) for s in dh["sessions"]]
          == [("spec", "haiku", "medium"), ("plans", "haiku", "medium"), ("orchestration", "haiku", "medium")]
          and sessions and all(x[x.index("--model") + 1] == "haiku" for x in sessions),
          f"journey --same-model: each session on haiku, medium, not on the model of the handoff {p.stderr.strip()[-300:]}")

    # The journey on Vibe: the profile comes from the role of each session. The simulated human and the
    # handoff stay with Claude. The sessions share the VIBE_HOME of the house, so the cost of one is a difference.
    (fake / "vibe").write_text(FAKE_VIBE_JOURNEY)
    (fake / "vibe").chmod(0o755)
    before = set(output.iterdir())
    p = journey("--tool", "vibe")
    new = sorted(set(output.iterdir()) - before)
    d = json.loads((new[0] / "journey.json").read_text()) if new else {"sessions": []}
    check(p.returncode == 0 and [s["model"] for s in d["sessions"]] == ["spec", "plans", "orchestration"],
          f"vibe: three sessions, each on the profile of its role {p.stderr.strip()[-300:]}")
    check(d.get("acceptance", {}).get("code") == 0 and d.get("escalations") == 1,
          "vibe: the acceptance passes, and the escalation started from the terminal is counted")
    check([round(s["cost"], 2) for s in d["sessions"]] == [4.18, 4.18, 4.18],
          "vibe: the cost of each session, as a difference in the VIBE_HOME shared by the journey")
    argv = [json.loads(r) for r in (home / "argv-vibe.log").read_text().splitlines()] if (home / "argv-vibe.log").is_file() else []
    check(argv and all("--max-price" in x and "--output" in x for x in argv)
          and sum("--resume" in x for x in argv) == 3,
          "vibe: each call has a cap and the streaming output, and the continuation resumes the session")

    # The manners of the journey are judged on each session, from its steps. The fake sessions tell no percent.
    before = set(output.iterdir())
    p = journey("--tool", "vibe", "--manners")
    new = sorted(set(output.iterdir()) - before)
    d = json.loads((new[0] / "journey.json").read_text()) if new else {"sessions": []}
    top = (new[0] / "report.md").read_text().splitlines()[2] if new else ""
    check(p.returncode == 0 and d.get("manners") is True and d.get("manners_passed") is False
          and d["sessions"] and all(s.get("manners", {}).get("percent-told") is False for s in d["sessions"])
          and "manners: failed" in top and "(informational)" not in top,
          f"journey --manners: the manners of each session, from its steps. A percent not told fails them {p.stderr.strip()[-300:]}")
    check("manners: failed (informational)" in (runs[0] / "report.md").read_text(),
          "the journey without --manners says the manners are informational")

    # A house model takes all the roles of the journey: the profile of the alias by level, execution on its executor.
    (home / ".vibe").mkdir(exist_ok=True)
    (home / ".vibe/config.toml").write_text(
        '[[models]]\nname = "qwen-agent"\nprovider = "casa"\nalias = "qwen-agent"\nthinking = "off"\n'
        'thinking_levels = ["off", "low", "medium", "high"]\n\n'
        '[[providers]]\nname = "casa"\napi_base = "http://127.0.0.1:8091/v1"\napi_style = "openai"\n')
    (home / "argv-vibe.log").unlink(missing_ok=True)
    before = set(output.iterdir())
    p = journey("--tool", "vibe", "--model", "qwen-agent", "--effort", "low")
    new = sorted(set(output.iterdir()) - before)
    dq = json.loads((new[0] / "journey.json").read_text()) if new else {"sessions": []}
    argv = [json.loads(r) for r in (home / "argv-vibe.log").read_text().splitlines()] if (home / "argv-vibe.log").is_file() else []
    check(p.returncode == 0 and [(s["model"], s["effort"]) for s in dq["sessions"]] == [("qwen-agent-low", "low")] * 3
          and argv and all(x[x.index("--agent") + 1] == "qwen-agent-low" for x in argv),
          f"journey --model qwen-agent --effort low: each session on the profile qwen-agent-low {p.stderr.strip()[-300:]}")
    (home / ".vibe/config.toml").unlink()

    check("from the Vibe Code amount: €10.66 estimated" in top and d.get("eur_estimated") == 10.659
          and not re.search(r"€\s?\d[\d.,]* estimated", (runs[0] / "report.md").read_text())
          and "equivalent at the API price: " in (runs[0] / "report.md").read_text(),
          "the journey: with Vibe, euros from the Vibe Code amount. With Claude, the equivalent at the API price")

check(not set(pathlib.Path("/tmp").glob("bench-*")) - houses_before,
      "the miniature houses are gone, even after the quota used up or a write outside")

print()
print("  ✓ all tests pass" if failed == 0 else f"  ✗ {failed} tests failed")
sys.exit(1 if failed else 0)
