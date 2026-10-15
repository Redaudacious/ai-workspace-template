#!/usr/bin/env python3
"""Test for `bin/reminder.py`: on made-up replies, the reminder comes at the first slip of the last
reply and at most once. Called as a hook, the script answers in the form of each tool, reads the
Vibe journal in its form, and stays silent on a broken input. It is run with
`python3 tests/test-reminder.py`."""
import importlib.util
import json
import os
import pathlib
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


ROOT = project_root()
TOOL = ROOT / "bin" / "reminder.py"
failed = 0


def check(condition, message):
    global failed
    failed += not condition
    print(f"  {'✓' if condition else '✗'} {message}")


def step(kind, target="", text="", row=0, turn=0):
    return {"row": row, "turn": turn, "kind": kind, "tool": "", "target": target, "text": text}


try:
    spec = importlib.util.spec_from_file_location("reminder", TOOL)
    rem = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rem)
except Exception as e:
    print(f"  ✗ bin/reminder.py does not load: {e}")
    sys.exit(1)
import tools  # noqa: E402  put on the path by reminder.py

S, P, RD = rem.SKILL.format("plans"), rem.PERCENT, rem.READER
print("which slip gets the reminder")
check(all(tools.REMINDER.search(x) for x in (S, P, RD)), "the bench parsers recognize each reminder")
human = step("human", text="do this", row=-1)
check(rem.slip([human, step("skill", "plans"), step("text", text="I write the plans.", row=1)], "claude") == S,
      "a skill loaded without an announcement gets the reminder, with its name")
check(rem.slip([human, step("skill", "plans"), step("text", text="Using plans to write the plans.")], "claude") is None,
      "an announced skill gets nothing")
check(rem.slip([human, step("skill", "ponytail")], "vibe") is None, "the modes are not announced")
writes = [human, step("write", "bin/x.py"), step("text", text="I wrote x.", row=1)]
check(rem.slip(writes, "claude") == P, "writes without a percentage get the percentage reminder")
check(rem.slip(writes + [step("text", text="40% done; about 10 minutes left.", row=1)], "claude") is None,
      "with the percentage told, nothing")
check(rem.slip([human, step("command", 'git commit -m "Message"')], "vibe") == P, "a commit without a percentage, the same")
check(rem.slip([human, step("read", "README.md"), step("text", text="Here it is.")], "claude") is None,
      "a discussion without writes gets no reminders")
pages = [human, step("skill", "spec"), step("text", text="Using spec to write the spec."),
         step("search", "restic"), step("page", "https://restic.net"), step("page", "https://borgbackup.org", row=1)]
check(rem.slip(pages, "vibe") == RD, "with Vibe, the third page read directly gets the reader reminder")
check(rem.slip(pages[:-1], "vibe") is None, "two pages pass")
check(rem.slip(pages, "claude") is None, "with Claude, the panel reminds about pages")
check(rem.slip([human, step("search", "a"), step("page", "b"), step("page", "c")], "vibe") is None,
      "the reader, which loads no skills, reads with no reminders")
check("Using plans to" in S and "N%" in P, "the reminders give the form of the sentence asked for, not only ask for the announcement")
many = [human, step("skill", "spec"), step("skill", "brainstorming", row=1), step("write", "records/x.md", row=2),
        step("text", text="I wrote x.", row=2)]
combined = rem.slip(many, "vibe")
check(combined and S.replace("plans", "spec") in combined and "brainstorming" in combined.split("The same for")[-1] and P in combined,
      "all the slips of a reply come in one reminder: each unannounced skill, then the percentages")
check(tools.REMINDER.search(combined or ""), "the bench parsers recognize the combined reminder too")
check(combined and combined.startswith("You have 2 things to fix, all of them, in the next reply:")
      and "(1) " in combined and "(2) " in combined,
      "the combined reminder counts its items, so the model does not fix only the first")
check(not S.startswith("You have"), "a single slip stays a simple reminder")
after = [human, step("skill", "plans"), step("reminder", text=S), step("text", text="Ok.", row=1)]
check(rem.slip(after, "claude") is None, "after a reminder, the next reply gets no other")
check(rem.slip(after + [step("human", text="go on", row=1, turn=1), step("skill", "documentation", row=2, turn=1)], "claude")
      == rem.SKILL.format("documentation"), "a new turn of the human is judged again")

print("the role asked for without its skill")
ROLE = rem.ROLE.format("spec")
request = step("human", text="I want a small tool. Let's write the spec.", row=-1)
check(rem.slip([request, step("write", "summary.py"),
                step("text", text="I wrote summary.py. 100% done; about 0 minutes left.")], "claude") == ROLE,
      "the spec asked for, with code written and no spec skill, gets the role reminder")
check(rem.slip([request, step("skill", "spec"), step("text", text="Using spec to write the spec.")], "claude") is None,
      "with the spec skill loaded, nothing")
for text, role in (("Read the spec x and write the plan of the work and the README.md of the folder.", "plans"),
                   ("The plans are to be written, with the README.md of the work.", "plans"),
                   ("Orchestrate the work records/work/open/x with the orchestration skill.", "orchestration")):
    check(rem.slip([step("human", text=text, row=-1), step("text", text="Done.")], "vibe") == rem.ROLE.format(role),
          f"“{text[:32]}…” asks for the {role} role")
check(rem.slip([step("human", text="Execute the plan x.md with the execute skill.", row=-1), step("text", text="Done.")], "claude") is None,
      "execution is not a role of the rule")
check(rem.slip([request, step("text", text="Which tool?"), step("human", text="yes", turn=1),
                step("text", text="Ok.", row=1, turn=1)], "claude") is None,
      "only the last message of the human is judged")
check(tools.REMINDER.search(ROLE), "the bench parsers recognize the role reminder")

print("called as a hook")
with tempfile.TemporaryDirectory() as d:
    t = pathlib.Path(d)

    def hook(tool, data):
        return subprocess.run([sys.executable, str(TOOL), "--tool", tool], input=data,
                              capture_output=True, text=True)

    log = t / "session.jsonl"
    log.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in [
        {"type": "user", "message": {"content": "write x"}},
        {"type": "assistant", "message": {"id": "a1", "content": [{"type": "tool_use", "name": "Write", "input": {"file_path": "/p/x.py"}}]}},
        {"type": "assistant", "message": {"id": "a2", "content": [{"type": "text", "text": "I wrote x."}]}}]) + "\n")
    p = hook("claude", json.dumps({"transcript_path": str(log), "stop_hook_active": False}))
    check(p.returncode == 0 and json.loads(p.stdout or "{}") == {"decision": "block", "reason": P},
          f"claude: block, with the reminder in reason {p.stderr.strip()[-200:]}")
    p = hook("claude", json.dumps({"transcript_path": str(log), "stop_hook_active": True}))
    check(p.returncode == 0 and p.stdout == "", "claude: with stop_hook_active, silent")
    p = hook("claude", "{ not json")
    check(p.returncode == 0 and p.stdout == "", "claude: a broken input stays silent and does not stop the session")

    # The Vibe journal, in the form tested on 9 October 2026: the entries of the turn in `projection_delta`,
    # the reply under judgment only in the request to the hook.
    def delta(*entries, op="append_entry"):
        return {"type": "projection_delta", "payload": {"delta": [{"op": op, "entry": e} for e in entries]
                                                        + [{"op": "set_envelope", "state": {}}]}}

    def request_to_hook(text, turn="turn-1"):
        return {"type": "action_intent", "payload": {"kind": "hook", "request": {
            "hook": "post_agent_turn", "turn_id": turn, "input": {"candidate": {"message": {"role": "assistant", "content": [
                {"type": "reasoning", "content": [{"type": "text", "text": "thinking 99%"}]}, {"type": "text", "text": text}]}}}}}}

    u = {"id": "u1", "type": "message", "role": "user", "source": "turn_start", "content": [{"type": "text", "text": "write x"}]}
    e_running = {"id": "e1", "type": "effect", "detail": {"toolName": "file_system.write_file", "input": {"path": "/p/x.py"}}}
    e_done = {**e_running, "generationStatus": "completed"}
    notice = {"id": "n1", "type": "notice", "detail": {"kind": "hook_completed", "hookName": "reminder",
                                                       "content": "Requested turn revision"}}

    def session(name, *lines):
        folder = t / name / "journal"
        folder.mkdir(parents=True)
        (folder / "0000000000000001.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in lines) + "\n")
        (folder / "0000000000000099.jsonl").write_text("")
        return json.dumps({"session_id": name, "transcript_path": str(t / name), "cwd": "/p", "hook_event_name": "post_agent"})

    p = hook("vibe", session("s1", delta(u), delta(e_running), delta(e_done, op="replace_entry"), request_to_hook("I wrote x.")))
    check(p.returncode == 0 and json.loads(p.stdout or "{}") == {"decision": "deny", "reason": P},
          f"vibe: deny, with the reminder in reason, from the session journal; the percentage in the reasoning does not count {p.stderr.strip()[-200:]}")
    p = hook("vibe", session("s2", delta(u), delta(e_done), request_to_hook("I wrote x, 40%, 5 minutes left.")))
    check(p.returncode == 0 and p.stdout == "", "vibe: the percentage in the reply found in the request to the hook counts")
    p = hook("vibe", session("s3", delta(u), delta(e_done), request_to_hook("I wrote x."), delta(notice), request_to_hook("I wrote x.")))
    check(p.returncode == 0 and p.stdout == "", "vibe: after the notice of the reminder, the second call in the turn stays silent")
    p = hook("vibe", json.dumps({"session_id": "missing", "transcript_path": str(t / "missing")}))
    check(p.returncode == 0 and p.stdout == "", "vibe: a session with no journal stays silent")

print(f"\n  failed checks: {failed}")
sys.exit(1 if failed else 0)
