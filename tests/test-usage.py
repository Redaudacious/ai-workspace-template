#!/usr/bin/env python3
"""Test for `bin/usage.py`.

No testing framework. The logs are fabricated in a temporary folder, the tool runs as a
separate process, and the output is read as text.
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import datetime


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


TOOL = project_root() / "bin" / "usage.py"
failed = 0


def check(condition, message):
    global failed
    if condition:
        print(f"  ✓ {message}")
    else:
        failed += 1
        print(f"  ✗ {message}")


def answer(sid, model, usage):
    return {"type": "assistant", "timestamp": "2026-09-17T01:00:00Z",
            "message": {"id": sid, "model": model, "usage": usage}}


def write(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(r if isinstance(r, str) else json.dumps(r) for r in lines) + "\n")


if not TOOL.exists():
    print(f"  ✗ cannot find {TOOL}")
    sys.exit(1)

with tempfile.TemporaryDirectory() as tmp:
    j = pathlib.Path(tmp)
    written = answer("m1", "claude-opus-5", {
        "input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 0,
        "cache_creation_input_tokens": 1_000_000,
        "cache_creation": {"ephemeral_5m_input_tokens": 0, "ephemeral_1h_input_tokens": 1_000_000}})
    read = answer("m2", "claude-opus-5", {
        "input_tokens": 0, "cache_read_input_tokens": 1_000_000, "output_tokens": 100_000,
        "cache_creation_input_tokens": 0})
    # ⚠ An answer with several blocks is written on several lines, with the same
    #   `usage`. The doubled line is exactly the trap: counted twice, opus would come out
    #   at 23 $, not 13 $.
    write(j / "project-a" / "aaaaaaaa-opus.jsonl",
          [{"type": "user", "message": {"content": "hello"}}, written, written, read, "{ broken line"])
    write(j / "project-b" / "bbbbbbbb-sonnet.jsonl", [answer("s1", "claude-sonnet-5", {
        "input_tokens": 1_000_000, "cache_read_input_tokens": 0, "output_tokens": 1_000_000,
        "cache_creation_input_tokens": 0})])
    write(j / "project-b" / "cccccccc-unknown.jsonl",
          [answer("x1", "<synthetic>", {"input_tokens": 5, "output_tokens": 5})])

    p = subprocess.run([sys.executable, str(TOOL), "--logs", str(j)],
                       capture_output=True, text=True)
    out = p.stdout
    lines = out.splitlines()

    check(p.returncode == 0, f"it exits with 0 (it exited with {p.returncode}: {p.stderr.strip()[:200]})")
    check("sessions: 2 " in out, "it counts only the sessions with known models")
    check("API-equivalent total: $25.00" in out, "the total: 13 $ opus plus 12 $ sonnet")
    check("output: 50%" in out and "cache read: 2%" in out
          and "cache written: 40%" in out and "input: 8%" in out,
          "the shares of the total: output 50%, read 2%, written 40%, input 8%")
    opus = [r for r in lines if "aaaaaaaa" in r]
    check(len(opus) == 1 and " 13.00 " in opus[0], "opus: 13 $, the doubled answer counted once")
    check(len(opus) == 1 and "opus-5:2" in opus[0], "opus: two steps, not three")
    sonnet = [r for r in lines if "bbbbbbbb" in r]
    check(len(sonnet) == 1 and " 12.00 " in sonnet[0] and "sonnet-5:1" in sonnet[0],
          "sonnet: 12 $, at its own price, not opus's")
    check(bool(opus and sonnet) and lines.index(opus[0]) < lines.index(sonnet[0]),
          "the sessions come from the most expensive")

    p = subprocess.run([sys.executable, str(TOOL), "--logs", str(j / "does-not-exist")],
                       capture_output=True, text=True)
    check(p.returncode == 2, f"without logs it exits with 2, not with an empty table (it exited with {p.returncode})")

# ⚠ The price is the exact model's, not the family's: Opus 5.5 costs 4/20 and reads the
#   cache at 5%, not at 10% like Opus 5. At the family's price, a session on 5.5 comes
#   out a quarter more expensive than it was.
with tempfile.TemporaryDirectory() as tmp:
    k = pathlib.Path(tmp)
    write(k / "p" / "dddddddd-opus55.jsonl", [answer("o55", "claude-opus-5-5", {
        "input_tokens": 1_000_000, "cache_read_input_tokens": 1_000_000, "output_tokens": 0,
        "cache_creation_input_tokens": 0})])
    write(k / "p" / "eeeeeeee-fable.jsonl", [answer("f51", "claude-fable-5-1", {
        "input_tokens": 0, "cache_read_input_tokens": 1_000_000, "output_tokens": 0,
        "cache_creation_input_tokens": 0})])
    write(k / "p" / "ffffffff-sonnet46.jsonl", [answer("s46", "claude-sonnet-4-6", {
        "input_tokens": 1_000_000, "cache_read_input_tokens": 0, "output_tokens": 0,
        "cache_creation_input_tokens": 0})])
    # ⚠ Haiku 5.5 has two rates. Up to 100,000 tokens in a request it costs 0.10/0.50.
    #   Above that, it costs five times more. At the price of Haiku 4.5, it would come out
    #   ten times more expensive.
    write(k / "p" / "99999999-haiku55-small.jsonl", [answer("h1", "claude-haiku-5-5", {
        "input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 1_000_000,
        "cache_creation_input_tokens": 0})])
    write(k / "p" / "88888888-haiku55-large.jsonl", [answer("h2", "claude-haiku-5-5", {
        "input_tokens": 0, "cache_read_input_tokens": 1_000_000, "output_tokens": 1_000_000,
        "cache_creation_input_tokens": 0})])
    p = subprocess.run([sys.executable, str(TOOL), "--logs", str(k)],
                       capture_output=True, text=True)
    lines = p.stdout.splitlines()
    o55 = [r for r in lines if "dddddddd" in r]
    check(len(o55) == 1 and " 4.20 " in o55[0] and "opus-5-5:1" in o55[0],
          "opus 5.5: 4 $ for the input plus 0.20 $ for the cache read, not 5.50 $")
    f51 = [r for r in lines if "eeeeeeee" in r]
    check(len(f51) == 1 and " 0.25 " in f51[0], "fable 5.1: the cache read at 0.25 $ per million")
    s46 = [r for r in lines if "ffffffff" in r]
    check(len(s46) == 1 and " 3.00 " in s46[0], "sonnet 4.6: 3 $, not sonnet 5's price")
    h1 = [r for r in lines if "99999999" in r]
    check(len(h1) == 1 and " 0.50 " in h1[0], "haiku 5.5 under 100,000: the output at 0.50 $ per million")
    h2 = [r for r in lines if "88888888" in r]
    check(len(h2) == 1 and " 2.55 " in h2[0], "haiku 5.5 over 100,000: 0.05 $ for the cache read plus 2.50 $ for the output")
    check("API-equivalent total: $10.50" in p.stdout, "the total of the five: 10.50 $")


# The report by role, model and effort. The role comes from the framework skills called in
# the session. The effort comes from `perTurnEffort`. The agents of a session sit in
# `<session>/subagents/`. They count in its cost, with their own model and effort.
def step(sid, model, effort, usage, *blocks):
    r = answer(sid, model, usage)
    r["perTurnEffort"] = effort
    r["message"]["content"] = list(blocks)
    return r


def skill(name):
    return {"type": "tool_use", "name": "Skill", "input": {"skill": name}}


MILLION_OUTPUT = {"input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 1_000_000,
                  "cache_creation_input_tokens": 0}

with tempfile.TemporaryDirectory() as tmp:
    j = pathlib.Path(tmp)
    write(j / "p" / "11111111-plans.jsonl", [
        {"type": "user", "timestamp": "2026-10-01T10:00:00Z", "message": {"content": "Plans of work x"}},
        step("p1", "claude-opus-5-5", "max", MILLION_OUTPUT, skill("plans"))])
    write(j / "p" / "11111111-plans" / "subagents" / "agent-a1.jsonl", [
        step("a1", "claude-sonnet-5-5", "high", MILLION_OUTPUT)])
    (j / "p" / "11111111-plans" / "subagents" / "agent-a1.meta.json").write_text(
        json.dumps({"agentType": "executor", "requestShape": "foreground"}))
    write(j / "p" / "22222222-orchestration.jsonl", [
        {"type": "user", "timestamp": "2026-10-02T10:00:00Z", "message": {"content": "Orchestrate work x"}},
        step("o1", "claude-opus-5-5", "medium", MILLION_OUTPUT, skill("orchestration"), skill("execute"))])
    write(j / "p" / "33333333-review.jsonl", [
        {"type": "user", "timestamp": "2026-10-03T10:00:00Z", "message": {"content": "<local-command-stdout>x</local-command-stdout>"}},
        {"type": "user", "message": {"content": '<pasted_content id="1">\nReview of the execution of plan x\n</pasted_content id="1">'}},
        step("r1", "claude-opus-5-5", "high", MILLION_OUTPUT)])
    write(j / "p" / "44444444-old.jsonl", [
        {"type": "user", "timestamp": "2026-09-01T10:00:00Z", "message": {"content": "something else"}},
        step("v1", "claude-opus-5-5", "high", MILLION_OUTPUT)])

    p = subprocess.run([sys.executable, str(TOOL), "--logs", str(j)], capture_output=True, text=True)
    plan = [r for r in p.stdout.splitlines() if "11111111" in r]
    check(len(plan) == 1 and " 30.00 " in plan[0] and "sonnet-5-5:1" in plan[0],
          "the session counts its agents: 20 $ for itself, 10 $ for the executor")

    p = subprocess.run([sys.executable, str(TOOL), "--logs", str(j), "--by-role", "--after", "2026-09-22"],
                       capture_output=True, text=True)
    out = p.stdout
    check(p.returncode == 0, f"--by-role exits with 0 (it exited with {p.returncode}: {p.stderr.strip()[:200]})")
    check("sessions: 3 " in out and "$70.00" in out, "--after leaves out the September session: 3 sessions, 70 $")
    lines = out.splitlines()
    check(any(r.split()[:3] == ["plans", "1", "30.00"] for r in lines), "plans: one session, 30 $ with the agent")
    check(any(r.split()[:3] == ["orchestration", "1", "20.00"] for r in lines),
          "orchestration comes before execution: the skill of the orchestrator gives the role")
    check(any(r.split()[:3] == ["review", "1", "20.00"] for r in lines),
          "review: without a framework skill, the first message mentions it")
    check(any(r.split()[:4] == ["plans", "executor", "sonnet-5-5", "high"] for r in lines),
          "the agent appears under the role of the session, with its type, model and effort")
    check(any(r.split()[:4] == ["plans", "session", "opus-5-5", "max"] for r in lines),
          "the steps of the session, with their model and effort")

# --state gives the panel in the app the state of all the chats. A chat is working, warm or
# cold. The state has the minutes of cache left, the name and address from the files of the
# app, the work, the role, the agents and the share of the 7-day limit. The moments in the
# logs are counted from the clock of now.
def ago(seconds_ago):
    t = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=seconds_ago)
    return t.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def tokens(output=0, hour=0, five=0):
    return {"input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": output,
            "cache_creation_input_tokens": hour + five,
            "cache_creation": {"ephemeral_5m_input_tokens": five, "ephemeral_1h_input_tokens": hour}}


def human(text, seconds_ago, cwd):
    return {"type": "user", "timestamp": ago(seconds_ago), "cwd": cwd,
            "message": {"role": "user", "content": text}}


def model_step(mid, seconds_ago, usage, *blocks, model="claude-opus-5-5"):
    return {"type": "assistant", "timestamp": ago(seconds_ago), "perTurnEffort": "high",
            "message": {"id": mid, "model": model, "usage": usage, "content": list(blocks)}}


def tool_use(uid, name="Bash", **inputs):
    return {"type": "tool_use", "id": uid, "name": name, "input": inputs}


def tool_result(uid, seconds_ago):
    return {"type": "user", "timestamp": ago(seconds_ago),
            "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": uid, "content": "ok"}]}}


def run(j, *arguments):
    return subprocess.run([sys.executable, str(TOOL), "--logs", str(j / "logs"), *arguments],
                          capture_output=True, text=True)


def read_state(j, reset):
    p = run(j, "--state", "--app", str(j / "app"), "--cache", str(j / "cache.json"),
            "--week", "30", "--reset", reset, "--weeks", str(j / "weeks"), "--vibe", str(j / "no-vibe"))
    try:
        return p, json.loads(p.stdout)
    except ValueError:
        return p, {}


with tempfile.TemporaryDirectory() as tmp:
    j = pathlib.Path(tmp)
    cwd = str(j / "workdir")
    J = j / "logs" / "-workdir"
    HOUR_MILLION = tokens(output=1_000_000, hour=1_000_000)   # 20 $ for the output plus 8 $ for the cache write, on Opus 5.5
    write(J / "11111111-working.jsonl", [human("hello", 40, cwd), model_step("l1", 30, HOUR_MILLION)])
    write(J / "22222222-warm.jsonl", [
        human("Write the plans of the work records/work/open/2026-10-08-x/ with the plans skill", 600, cwd),
        model_step("w1", 590, HOUR_MILLION, tool_use("s1", "Skill", skill="plans")),
        tool_result("s1", 585),
        model_step("w2", 580, tokens())])
    write(J / "22222222-warm" / "subagents" / "agent-ab12.jsonl", [
        model_step("a1", 180, tokens(output=1_000_000), model="claude-haiku-5-5")])
    (J / "22222222-warm" / "subagents" / "agent-ab12.meta.json").write_text(
        json.dumps({"agentType": "executor", "description": "Execute plan x"}))
    W = j / "logs" / "-workdir" / "55555555-team" / "subagents" / "workflows" / "wf_t1"
    write(W / "agent-w1.jsonl", [
        model_step("w1a", 170, {**tokens(output=10), "cache_read_input_tokens": 90_000}, model="claude-haiku-5-5"),
        model_step("w1b", 160, {**tokens(output=10), "cache_read_input_tokens": 120_000}, model="claude-haiku-5-5")])
    (W / "agent-w1.meta.json").write_text(json.dumps({"agentType": "workflow-subagent", "description": "rewrite:AGENTS.md"}))
    write(J / "33333333-cold.jsonl", [model_step("r0", 5 * 86400, tokens(output=1_000_000)),
                                      human("something else", 7200, cwd), model_step("r1", 7190, HOUR_MILLION)])
    write(J / "44444444-waiting.jsonl", [human("run", 610, cwd),
                                         model_step("t1", 600, tokens(output=1_000_000), tool_use("b1"))])
    write(j / "app" / "account" / "org" / "local_aaaa.json", [json.dumps({
        "sessionId": "local_aaaa", "cliSessionId": "22222222-warm", "title": "Name from the app",
        "model": "claude-opus-5-5", "effort": "max"})])
    reset = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")

    p, s = read_state(j, reset)
    check(p.returncode == 0, f"--state exits with 0 (it exited with {p.returncode}: {p.stderr.strip()[:200]})")
    ch = {c["code"]: c for c in s.get("chats", [])}
    check({k: c["state"] for k, c in ch.items()} == {"11111111": "working", "22222222": "warm",
                                                     "33333333": "cold", "44444444": "working"},
          "--state: working after the step 30 s ago and after the tool without a result, warm, cold")
    w = ch.get("22222222", {})
    check(w.get("warm_min") in (49, 50), f"--state: still warm for 50 min, from the request 585 s ago (it gave {w.get('warm_min')})")
    check(w.get("title") == "Name from the app" and w.get("local") == "local_aaaa" and w.get("effort") == "max"
          and s.get("app") is True, "--state: the name, address and effort come from the file of the app")
    check(w.get("work") == cwd + "/records/work/open/2026-10-08-x" and w.get("role") == "plans",
          "--state: the work from the first message of the human, the role from the skill called")
    ag = w.get("agents") or [{}]
    check(ag[0].get("type") == "executor" and ag[0].get("description") == "Execute plan x"
          and ag[0].get("usd") == 0.5 and ag[0].get("usd_sonnet") == 10.0 and ag[0].get("working") is False,
          "--state: the agent with its type, description, cost on Haiku and the same cost on Sonnet")
    r = ch.get("33333333", {})
    check(r.get("usd") == 48.0 and r.get("usd_window") == 28.0 and r.get("rewrite_usd") == 8.0,
          "--state: the step 5 days ago is outside the window, and writing 1M of context again costs 8 $")
    check(abs(sum(c["weekly"] for c in ch.values()) - 30) < 0.05 and w.get("usd") == 28.5,
          "--state: the shares of the chats add up to the percent of the limit")
    weeks = sorted((j / "weeks").glob("*.json"))
    window = json.loads(weeks[0].read_text()) if len(weeks) == 1 else {}
    check(len(window.get("chats", [])) == 4 and {"opus-5-5", "haiku-5-5"} <= set(window.get("totals", {}).get("by_model", {})),
          "--weeks: the file of the window, with the chats and the totals by model")

    # Reading in chunks: the second run counts nothing twice. A row that is half written
    # counts once, after it is finished.
    _, s = read_state(j, reset)
    check({c["code"]: c["usd"] for c in s.get("chats", [])}.get("22222222") == 28.5,
          "second run: the same cost, with no step counted twice")
    row = json.dumps(model_step("l2", 5, tokens(output=1_000_000)))
    with open(J / "11111111-working.jsonl", "a") as f:
        f.write(row[:40])
    _, s = read_state(j, reset)
    check({c["code"]: c["usd"] for c in s.get("chats", [])}.get("11111111") == 28.0,
          "a row that is half written does not count yet")
    with open(J / "11111111-working.jsonl", "a") as f:
        f.write(row[40:] + "\n")
    _, s = read_state(j, reset)
    check({c["code"]: c["usd"] for c in s.get("chats", [])}.get("11111111") == 48.0,
          "the finished row counts once: 28 $ plus 20 $")

    # The evidence, the sum of the work, the windows and the cost of an agent.
    p = run(j, "--evidence", "22222222", "--weeks", str(j / "weeks"))
    folder = pathlib.Path(cwd) / "records" / "work" / "open" / "2026-10-08-x"
    files = sorted((folder / "usage").glob("*-plans-22222222.json"))
    check(p.returncode == 0 and len(files) == 1 and json.loads(files[0].read_text()).get("usd") == 28.5,
          f"--evidence: the file of the chat in the folder of its work (it exited with {p.returncode}: {p.stderr.strip()[:200]})")
    p = run(j, "--work", str(folder))
    check("the work cost $28.50" in p.stdout, "--work: the sum of the evidence in the folder")
    p = run(j, "--windows", str(j / "weeks"))
    check(p.returncode == 0 and "0.50" in p.stdout and "10.00" in p.stdout,
          "--windows: the executor on Haiku, next to the price on Sonnet")
    p = run(j, "--agent", "ab12")
    check(p.stdout.strip() == "executor haiku-5-5: $0.50. Same tokens on Sonnet: $10.00. Context peak: 0",
          f"--agent: the cost of the agent, of the same tokens on Sonnet, and the peak (it printed {p.stdout.strip()[:140]!r})")
    p = run(j, "--agent", "w1")
    check(p.returncode == 0 and p.stdout.strip().endswith("Context peak: 120000"),
          f"--agent also finds an agent of a team, with its peak (it printed {p.stdout.strip()[:140]!r})")
    p = run(j, "--workflow", "wf_t1")
    check(p.returncode == 0 and p.stdout == "rewrite:AGENTS.md\thaiku-5-5\t120000\n",
          f"--workflow: the label, model and peak of each agent, separated by tabs (it printed {p.stdout[:140]!r})")
    p = run(j, "--workflow", "wf_none")
    check(p.returncode == 2, "--workflow: an unknown team exits with 2")
    p = run(j, "--evidence", "99999999", "--weeks", str(j / "weeks"))
    check(p.returncode == 2, "--evidence: an unknown chat exits with 2, with no file")

# ── Vibe: the sessions in logs/session/unified/, at the prices in config.toml ──
with tempfile.TemporaryDirectory() as tmp:
    v = pathlib.Path(tmp) / "vibe"
    v.mkdir()
    (v / "config.toml").write_text(
        '[[models]]\nname = "mistral-large-4"\nprovider = "mistral"\nalias = "large-4"\n'
        'input_price = 0.68\ncached_input_price = 0.07\noutput_price = 2.09\n\n'
        '[[models]]\nname = "no-cache"\nprovider = "mistral"\nalias = "no-cache"\n'
        'input_price = 1.0\noutput_price = 2.0\n')

    def vibe_session(sid, model, start, input_, cache, output):
        d = v / "logs/session/unified" / sid
        g = d / "generations/0000000000000002"
        g.mkdir(parents=True)
        (d / "CURRENT").write_text(json.dumps({"generation": "0000000000000002", "session_id": sid}))
        (d / "meta.json").write_text(json.dumps({"session_id": sid, "start_time": start, "end_time": None,
                                                 "environment": {"working_directory": "/p"}}))
        (g / "projection-state.json").write_text(json.dumps({"snapshot": {"session": {
            "preview": f"title {sid}",
            "tokenUsage": {"inputTokens": input_, "cachedInputTokens": cache, "outputTokens": output}}}}))
        (g / "runtime-state.json").write_text(json.dumps({"session_metadata": {"active_model": model, "cwd": "/p"}}))

    month = datetime.date.today().strftime("%Y-%m")
    vibe_session("aaaa", "large-4", f"{month}-02T10:00:00+00:00", 2_000_000, 1_000_000, 1_000_000)  # 0.68 + 0.07 + 2.09
    vibe_session("bbbb", "no-cache", f"{month}-03T10:00:00+00:00", 1_000_000, 1_000_000, 0)         # the cache as input: 1.00
    vibe_session("dddd", "unknown", f"{month}-04T10:00:00+00:00", 1_000_000, 0, 0)                  # no price
    vibe_session("cccc", "large-4", "2020-01-05T10:00:00+00:00", 1_000_000, 0, 0)                   # another month: 0.68
    (v / "logs/session/unified/half-written").mkdir()                                               # no CURRENT: skipped

    def vibe(*arguments):
        return subprocess.run([sys.executable, str(TOOL), "--vibe-sessions", "--vibe", str(v), *arguments],
                              capture_output=True, text=True)

    p = vibe()
    check(p.returncode == 0 and f"Vibe, {month}: €3.26 estimated, from $3.84 at the prices in config.toml, sessions: 3, no price: 1" in p.stdout,
          f"--vibe-sessions: the sum of the month (it printed {p.stdout.strip()[-160:]!r} {p.stderr.strip()[-200:]!r})")
    check("2.84" in p.stdout and "title aaaa" in p.stdout and "title cccc" not in p.stdout,
          "--vibe-sessions: one row for each session, with its cost and title, only from the month asked")
    p = vibe("--month", "2020-01")
    check("Vibe, 2020-01: €0.58 estimated, from $0.68" in p.stdout, "--vibe-sessions --month: another month")
    p = subprocess.run([sys.executable, str(TOOL), "--vibe-sessions", "--vibe", str(v / "does-not-exist")],
                       capture_output=True, text=True)
    check(p.returncode == 0 and ": €0.00 estimated, from $0.00 at the prices in config.toml, sessions: 0" in p.stdout,
          "--vibe-sessions: without Vibe, zero, with no error")

    # The state of the panel: the Vibe sessions enter as chats. They stay out of the totals
    # and out of the share of the week of Claude. The file of the window stays only Claude's.
    reset = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    j = pathlib.Path(tmp) / "state"
    (j / "logs").mkdir(parents=True)
    p = subprocess.run([sys.executable, str(TOOL), "--state", "--logs", str(j / "logs"), "--vibe", str(v),
                        "--app", str(j / "app"), "--cache", str(j / "cache.json"), "--week", "30",
                        "--reset", reset, "--weeks", str(j / "weeks")], capture_output=True, text=True)
    try:
        s = json.loads(p.stdout)
    except ValueError:
        s = {"chats": [], "totals": {}}
    ch = {c["code"]: c for c in s["chats"] if c.get("tool") == "vibe"}
    check(set(ch) == {"aaaa", "bbbb", "cccc", "dddd"},
          f"--state: the Vibe sessions are chats with their tool ({sorted(ch)} {p.stderr.strip()[-200:]})")
    a = ch.get("aaaa", {})
    check(a.get("usd") == 2.84 and a.get("model") == "large-4" and a.get("weekly") is None
          and a.get("state") == "working" and a.get("title") == "title aaaa",
          "--state: the Vibe chat has its cost, model and title, with no share of the week of Claude")
    check(s["totals"].get("usd") == 0 and not s["totals"].get("by_model"),
          "--state: the totals of Claude do not include the Vibe sessions")
    check(s.get("vibe") == {"month": month, "usd": 3.84, "eur": 3.26, "sessions": 3, "no_price": 1},
          f"--state: the sum of the month for Vibe ({s.get('vibe')})")
    window = [json.loads(f.read_text()) for f in (j / "weeks").glob("*.json")]
    check(window and all(c.get("tool") != "vibe" for c in window[0]["chats"]),
          "--state: the file of the 7-day window stays only Claude's")

print()
print("  ✓ all tests pass" if failed == 0 else f"  ✗ {failed} tests failed")
sys.exit(1 if failed else 0)
