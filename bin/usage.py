#!/usr/bin/env python3
"""usage.py — where the tokens went, session by session.

It reads the local logs of Claude Code and counts each session at the API price:
uncached input, cache write, cache read, output. It is not the subscription bill. The
proportions between the columns are what matters.

    python3 bin/usage.py                  # all the sessions on this machine
    python3 bin/usage.py --sessions 5     # only the five most expensive
    python3 bin/usage.py --logs DIR       # another folder of logs
    python3 bin/usage.py --after 2026-09-22 --by-role   # by session role, model and effort
    python3 bin/usage.py --state --week 12 --reset 2026-10-09T07:00:00Z   # for the panel
    python3 bin/usage.py --evidence e345e355   # the evidence of one chat, in its work folder
    python3 bin/usage.py --work FOLDER    # what one piece of work cost, from its evidence
    python3 bin/usage.py --windows DIR    # the 7-day windows, side by side
    python3 bin/usage.py --agent ID       # the cost of one agent, the same tokens on Sonnet, and the context peak
    python3 bin/usage.py --workflow ID    # the agents of a Workflow team: label, model, peak
    python3 bin/usage.py --vibe-sessions  # the Mistral Vibe sessions of the month, with their cost

⚠ A SESSION COUNTS ITS AGENTS. Claude Code writes the log of each agent separately, in
  `<session>/subagents/agent-<id>.jsonl`, next to `agent-<id>.meta.json` with its type.
  Their cost goes into the session that started them.

⚠ AN ANSWER IS COUNTED ONLY ONCE. The log writes an answer with several blocks on
  several lines, each with the same `usage`. Without deduplicating on `message.id`, a
  session would come out two or three times more expensive than it was.

⚠ THE PRICE IS THE EXACT MODEL'S, not the family's. Opus 5.5 costs 4/20 and reads the
  cache at 5%. Opus 5 costs 5/25 and reads it at 10%. At the family's price, a session
  on 5.5 comes out a quarter more expensive than it was, and the cache-read share is
  inflated. The prices below are from the model table of the `claude-api` skill.
  Before you quote a sum, check there.

⚠ THE STATE IS READ IN CHUNKS. With `--state`, each open chat runs the tool every 10
  seconds. The tool keeps how much it read of each log in `~/.cache/work-env-live/usage-state.json`.
  The next run reads only the new rows. A row that is half written waits for the next
  run. Every file is written beside the old one and then moved over it, so two chats
  cannot corrupt it.
"""
import argparse
import collections
import datetime
import json
import os
import pathlib
import re
import statistics
import sys
import time

# (fragment of the model name, $ per million input, $ per million output, cache read
#  as a fraction of the input price). The first matching fragment wins, so the more
#  precise ones sit before their family.
PRICE = [
    ("fable-5-1", 10, 50, 0.025),
    ("mythos-5-1", 10, 50, 0.025),
    ("fable", 10, 50, 0.1),
    ("opus-5-5", 4, 20, 0.05),
    ("opus", 5, 25, 0.1),
    ("sonnet-4-6", 3, 15, 0.1),
    ("sonnet", 2, 10, 0.1),
    ("haiku-5-5", 0.1, 0.5, 0.1),
    ("haiku", 1, 5, 0.1),
]
# Haiku 5.5 has two rates: above 100,000 tokens in a request, all its prices are multiplied by 5.
HAIKU_5_5_THRESHOLD, HAIKU_5_5_MULTIPLIER = 100_000, 5
WRITE_5M = 1.25         # five-minute cache, as a fraction of the input price
WRITE_1H = 2.0          # one-hour cache

# The state of the chats, for the panel in the app.
STATE = pathlib.Path.home() / ".cache" / "work-env-live" / "usage-state.json"
APP = pathlib.Path.home() / ".config" / "Claude" / "claude-code-sessions"
WEEKS = pathlib.Path(__file__).resolve().parent.parent / "records" / "usage" / "weeks"
WORKING_S = 120         # a model step newer than this: the chat is working
WAITING_S = 3600        # a tool without a result keeps the chat "working" for this long at most
KEPT_S = 8 * 86400      # older steps no longer enter any 7-day window
CHAT_TTL = 60           # the minutes of a chat's cache, until the log has written them
WRITE_TOOLS = ("Write", "Edit", "NotebookEdit")
# The folder of a piece of work: `records/work/open/<folder>` or `records/work/<domain>/open/<folder>`.
WORK = re.compile(r"(/[\w./-]*/)?(records/work/(?:[\w-]+/)?open/\d{4}-\d\d-\d\d-[\w-]+)")

# Vibe keeps each session in `$VIBE_HOME/logs/session/unified/<id>/`, with the tokens
# added up in the generation that `CURRENT` names. The prices are those of the models
# declared in `config.toml`, by alias. The format is not documented. It was read from Vibe 2.26.
VIBE = pathlib.Path(os.environ.get("VIBE_HOME") or pathlib.Path.home() / ".vibe")
# The rate on the Mistral price page: the price in euro is the price in dollars × 0.85, on each row.
EUR_PER_USD = 0.85


def price(model):
    return next((p for p in PRICE if p[0] in model), None)


def rows(path):
    with open(path, errors="replace") as f:
        for row in f:
            try:
                yield json.loads(row)
            except ValueError:
                continue


def day(path):
    return next(((d.get("timestamp") or "")[:10] for d in rows(path) if d.get("timestamp")), "")


def cost(u, p):
    """The cost of an answer with `usage` u, at the price p from PRICE, in $ × million by share."""
    _, input_, output, read = p
    cc = u.get("cache_creation") or {}
    w5 = cc.get("ephemeral_5m_input_tokens", 0) if cc else u.get("cache_creation_input_tokens", 0)
    w1 = cc.get("ephemeral_1h_input_tokens", 0)
    context = u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + w5 + w1
    if p[0] == "haiku-5-5" and context > HAIKU_5_5_THRESHOLD:
        input_, output = input_ * HAIKU_5_5_MULTIPLIER, output * HAIKU_5_5_MULTIPLIER
    return collections.Counter(
        input=u.get("input_tokens", 0) * input_,
        written=(w5 * WRITE_5M + w1 * WRITE_1H) * input_,
        read=u.get("cache_read_input_tokens", 0) * read * input_,
        output=u.get("output_tokens", 0) * output,
        context=context,
        steps=1)


def steps(path):
    """(model, effort, cost in $ × million by share) for each answer, counted once."""
    seen = set()
    for d in rows(path):
        m = d.get("message") or {}
        u = m.get("usage")
        if d.get("type") != "assistant" or not u or m.get("id") in seen:
            continue
        seen.add(m.get("id"))
        p = price(m.get("model", ""))
        if not p:
            continue
        yield m["model"].replace("claude-", ""), d.get("perTurnEffort"), cost(u, p)


def agents(path):
    """(type, log) for each agent that the session started."""
    for a in sorted((path.parent / path.stem / "subagents").glob("agent-*.jsonl")):
        yield meta(a).get("agentType", "agent"), a


def meta(a):
    """The file `agent-<id>.meta.json` beside the log of the agent: its type and description."""
    try:
        return json.loads(a.with_suffix(".meta.json").read_text())
    except (OSError, ValueError):
        return {}


def session(path):
    """(day, sums in $ × million, steps per model) for one session, with its agents."""
    c, models = collections.Counter(), collections.Counter()
    for log in [path] + [a for _, a in agents(path)]:
        for model, _, cost_ in steps(log):
            c.update(cost_)
            models[model] += 1
    return day(path), c, models


# The role of the session: the first row whose skills the session called, through the Skill
# tool or as a /command. Orchestration is first, because its skill also loads `execute`.
ROLES = (("orchestration", {"orchestration"}),
         ("execute", {"execute", "executing-plans", "subagent-driven-development"}),
         ("plans", {"plans", "writing-plans"}),
         ("spec", {"spec", "brainstorming"}))
COMMAND = re.compile(r"<command-name>/?([\w:-]+)</command-name>")
# Human rows that the app wrote, not the human. Text that the human pasted comes between
# `<pasted_content …>` tags and stays the human's.
NOT_HUMAN = ("<local-command", "<system-reminder", "<task-notification", "<bash-", "<command-")


def role_from(called, review):
    """The role from ROLES by the skills called. Without them: "review" or "other"."""
    found = next((r for r, skills in ROLES if set(called) & skills), None)
    return found or ("review" if review else "other")


def role(path):
    """The role from ROLES. Without their skills: "review" if the first human message
    mentions it, otherwise "other"."""
    called, first = set(), None
    for d in rows(path):
        c = (d.get("message") or {}).get("content")
        blocks = [b for b in c if isinstance(b, dict)] if isinstance(c, list) else []
        text = c if isinstance(c, str) else " ".join(b.get("text", "") for b in blocks)
        called.update(x.split(":")[-1] for x in COMMAND.findall(text))
        called.update(str((b.get("input") or {}).get("skill", "")).split(":")[-1]
                      for b in blocks if b.get("name") == "Skill")
        if (first is None and d.get("type") == "user" and not d.get("isMeta")
                and text.strip() and not text.lstrip().startswith(NOT_HUMAN)):
            first = text
    return role_from(called, bool(first and re.search(r"\breview", first, re.I)))


def total_of(c):
    return (c["input"] + c["written"] + c["read"] + c["output"]) / 1e6


def share(x, of):
    return f"{x / 1e6 / of:.0%}" if of else "-"


def by_role(files):
    """The cost by session role, then by role, who worked (the session or the agent type),
    model and effort."""
    totals, shares = collections.defaultdict(list), collections.defaultdict(collections.Counter)
    for f in files:
        r, total = role(f), 0.0
        for who, log in [("session", f)] + list(agents(f)):
            for model, effort, c in steps(log):
                shares[(r, who, model, effort or "-")].update(c)
                total += total_of(c)
        if total:
            totals[r].append(total)
    everything = sum(map(sum, totals.values()))
    print(f"sessions: {sum(map(len, totals.values()))}   API-equivalent total: ${everything:.2f}")
    print()
    print(f"{'role':13} {'sessions':>8} {'$':>9} {'share':>5} {'median':>9}")
    for r, v in sorted(totals.items(), key=lambda x: -sum(x[1])):
        print(f"{r:13} {len(v):8} {sum(v):9.2f} {share(sum(v) * 1e6, everything):>5} {statistics.median(v):9.2f}")
    print()
    print(f"{'role':13} {'who':12} {'model':18} {'effort':7} {'$':>9} {'share':>5} {'steps':>6} {'$/step':>7}")
    for (r, who, model, effort), c in sorted(shares.items(), key=lambda x: -total_of(x[1])):
        s = total_of(c)
        print(f"{r:13} {who:12} {model:18} {effort:7} {s:9.2f} {share(s * 1e6, everything):>5} "
              f"{c['steps']:6} {s / c['steps']:7.3f}")
    return 0


# ---------------------------------------------------------------------------------------------
# The state of the chats, for the panel in the app, and the files of the 7-day windows.

def seconds(ts):
    """The ISO 8601 moment from the logs, in seconds. 0 without a moment."""
    try:
        return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except (AttributeError, ValueError):
        return 0.0


def iso(s):
    return datetime.datetime.fromtimestamp(s, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if s else ""


def write_json(path, data):
    """Write beside the old file first, then move over it in one step."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    os.replace(tmp, path)


def work_in(text, cwd):
    """The work folder that the text names, with an absolute path. "" without one."""
    m = WORK.search(text or "")
    if not m:
        return ""
    return m.group(1) + m.group(2) if m.group(1) else os.path.join(cwd or "", m.group(2))


def empty():
    """What the tool remembers about a log between two runs."""
    return {"offset": 0, "ids": [], "steps": [], "usd": 0.0, "usd_sonnet": 0.0, "context": 0, "peak": 0,
            "model": "", "effort": "", "last": 0.0, "request": 0.0, "ttl": 0, "open": [],
            "title": "", "cwd": "", "called": [], "seen_human": False, "review": False,
            "work_message": "", "work_written": ""}


def read_log(path, st, now_s):
    """Add to `st` the rows written in `path` after `st["offset"]`. A row that is half written
    waits for the next run. Steps older than KEPT_S are forgotten, and the sums stay."""
    size = path.stat().st_size
    if size < st["offset"]:            # the log was rewritten: read it from the start
        st.clear()
        st.update(empty())
    with open(path, "rb") as f:
        f.seek(st["offset"])
        chunk = f.read(size - st["offset"])
    end = chunk.rfind(b"\n") + 1
    st["offset"] += end
    open_, called = set(st["open"]), set(st["called"])
    for row in chunk[:end].splitlines():
        try:
            d = json.loads(row)
        except ValueError:
            continue
        if not isinstance(d, dict):
            continue
        ts = seconds(d.get("timestamp"))
        st["cwd"] = d.get("cwd") or st["cwd"]
        m = d.get("message") if isinstance(d.get("message"), dict) else {}
        c = m.get("content")
        blocks = [b for b in c if isinstance(b, dict)] if isinstance(c, list) else []
        if d.get("type") == "custom-title" and d.get("customTitle"):
            st["title"] = d["customTitle"]
        elif d.get("type") == "user":
            open_ -= {b.get("tool_use_id") for b in blocks if b.get("type") == "tool_result"}
            text = c if isinstance(c, str) else " ".join(b.get("text", "") for b in blocks if b.get("type") == "text")
            called.update(x.split(":")[-1] for x in COMMAND.findall(text))
            if ts:
                st["request"] = ts      # the next request starts here, with the clock of its cache
            if (not st["seen_human"] and not d.get("isMeta") and text.strip()
                    and not text.lstrip().startswith(NOT_HUMAN)):
                st["seen_human"] = True
                st["review"] = bool(re.search(r"\breview", text, re.I))
                st["work_message"] = work_in(text, st["cwd"])
        elif d.get("type") == "assistant":
            for b in blocks:
                if b.get("type") != "tool_use":
                    continue
                open_.add(b.get("id"))
                input_ = b.get("input") or {}
                if b.get("name") == "Skill":
                    called.add(str(input_.get("skill", "")).split(":")[-1])
                if b.get("name") in WRITE_TOOLS:
                    written_path = str(input_.get("file_path") or input_.get("notebook_path") or "")
                    st["work_written"] = work_in(written_path, st["cwd"]) or st["work_written"]
            u = m.get("usage")
            if not u or m.get("id") in st["ids"]:
                continue
            st["ids"] = (st["ids"] + [m.get("id")])[-20:]
            p = price(m.get("model", ""))
            if not p:
                continue
            c1 = cost(u, p)
            usd = total_of(c1)
            st["usd"] += usd
            st["usd_sonnet"] += total_of(cost(u, price("sonnet")))
            model = m["model"].replace("claude-", "")
            st["steps"].append([ts, usd, model])
            st["context"], st["model"], st["last"] = c1["context"], model, ts
            st["peak"] = max(st.get("peak", 0), c1["context"])
            st["effort"] = d.get("perTurnEffort") or st["effort"]
            cc = u.get("cache_creation") or {}
            if cc.get("ephemeral_1h_input_tokens"):
                st["ttl"] = 60
            elif cc.get("ephemeral_5m_input_tokens") or (not cc and u.get("cache_creation_input_tokens")):
                st["ttl"] = 5
    st["open"] = sorted(x for x in open_ if x)
    st["called"] = sorted(x for x in called if x)
    st["steps"] = [p for p in st["steps"] if p[0] >= now_s - KEPT_S]
    return st


def app_files(folder, now_s):
    """Log code → the file of the desktop app for the chat: its address (`sessionId`), its name
    in the sidebar, its model and effort. Only the files touched in the last 8 days."""
    chart = {}
    for f in pathlib.Path(folder).glob("*/*/local_*.json"):
        try:
            if f.stat().st_mtime < now_s - KEPT_S:
                continue
            d = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        if isinstance(d, dict) and d.get("cliSessionId"):
            chart[d["cliSessionId"]] = d
    return chart


def state(logs, app_folder, state_file, percent=None, reset=None, vibe=None):
    """The chats with steps in the 7-day window, plus those that are working or have a warm
    cache, each with its agents, and the totals of the window by model and by role. With `vibe`,
    the Mistral Vibe sessions too, as separate chats, plus the sum of the month for Vibe."""
    now_s = time.time()
    try:
        cache = json.loads(pathlib.Path(state_file).read_text())
    except (OSError, ValueError):
        cache = {}
    reset_s = seconds(reset) if reset else 0.0
    start_s = (reset_s or now_s) - 7 * 86400
    app = app_files(app_folder, now_s)
    new = {}

    def log(path):
        st = cache.get(str(path)) or empty()
        try:
            read_log(path, st, now_s)
        except OSError:
            pass
        new[str(path)] = st
        return st

    def in_window(st):
        return sum(p[1] for p in st["steps"] if p[0] >= start_s)

    chats = []
    for f in sorted(pathlib.Path(logs).glob("*/*.jsonl")):
        try:
            if f.stat().st_mtime < now_s - KEPT_S:
                continue
        except OSError:
            continue
        st = log(f)
        agent_list = []
        for a in sorted((f.parent / f.stem / "subagents").glob("agent-*.jsonl")):
            sa, ma = log(a), meta(a)
            agent_list.append(dict(
                id=a.stem.removeprefix("agent-"), type=ma.get("agentType", "agent"),
                description=ma.get("description", ""), model=sa["model"], usd=round(sa["usd"], 4),
                usd_sonnet=round(sa["usd_sonnet"], 4), usd_window=round(in_window(sa), 4),
                weekly=None, context=sa["context"], working=now_s - sa["last"] < WORKING_S))
        if not st["last"] and not agent_list:
            continue
        a = app.get(f.stem, {})
        warm = (st["request"] or st["last"]) + (st["ttl"] or CHAT_TTL) * 60 - now_s
        working = (now_s - st["last"] < WORKING_S
                   or (bool(st["open"]) and now_s - st["last"] < WAITING_S))
        usd_w = in_window(st) + sum(x["usd_window"] for x in agent_list)
        if not working and warm <= 0 and not usd_w:
            continue
        p = price(st["model"])
        rewrite = total_of(cost({"cache_creation": {"ephemeral_1h_input_tokens": st["context"]}}, p)) if p else 0.0
        chats.append(dict(
            code=f.stem[:8], log=f.stem, local=a.get("sessionId"), title=a.get("title") or st["title"],
            project=f.parent.name, cwd=st["cwd"], work=st["work_message"] or st["work_written"],
            role=role_from(st["called"], st["review"]),
            model=(a.get("model") or "").replace("claude-", "") or st["model"],
            effort=a.get("effort") or st["effort"],
            usd=round(st["usd"] + sum(x["usd"] for x in agent_list), 4), usd_window=round(usd_w, 4),
            weekly=None, context=st["context"],
            state="working" if working else "warm" if warm > 0 else "cold",
            warm_min=int(warm // 60) if warm > 0 else None, rewrite_usd=round(rewrite, 2),
            last=iso(st["last"]), agents=agent_list, tool="claude"))

    total = sum(c["usd_window"] for c in chats)
    if percent is not None and total:
        for c in chats:
            c["weekly"] = round(c["usd_window"] / total * percent, 2)
            for x in c["agents"]:
                x["weekly"] = round(x["usd_window"] / total * percent, 2)
    per_model, per_role = collections.Counter(), collections.Counter()
    for c in chats:
        per_role[c["role"]] += c["usd_window"]
    for st in new.values():
        for ts, usd, model in st["steps"]:
            if ts >= start_s:
                per_model[model] += usd
    # The Vibe sessions sit beside the Claude chats, but after the totals. Their money comes
    # from the monthly Mistral sum, not from the limits of Claude, so they have no share of the week.
    ses = vibe_sessions(vibe) if vibe else []
    for s in ses:
        try:
            last = (pathlib.Path(vibe) / "logs/session/unified" / s["id"] / "CURRENT").stat().st_mtime
        except OSError:
            continue
        usd = s["usd"] or 0.0
        # ponytail: the whole session goes in the window where it last worked. Count per step if one lasts days.
        usd_w = usd if last >= start_s else 0.0
        working = now_s - last < WORKING_S
        if not working and not usd_w:
            continue
        chats.append(dict(
            code=s["id"][:8], log=s["id"], local=None, title=s["title"], project="vibe", cwd=s["cwd"] or "",
            work="", role="vibe", model=s["model"] or "?", effort="", usd=round(usd, 4),
            usd_window=round(usd_w, 4), weekly=None, context=0,
            state="working" if working else "cold", warm_min=None, rewrite_usd=0.0,
            last=iso(last), agents=[], tool="vibe"))
    month = datetime.date.today().strftime("%Y-%m")
    in_month = [s for s in ses if s["start"].startswith(month)]
    try:
        write_json(state_file, new)
    except OSError:
        pass  # without the cache, the next run reads everything again
    chats.sort(key=lambda c: -c["usd_window"])
    return {"updated": iso(now_s), "app": bool(app),
            "window": {"start": iso(start_s), "reset": reset, "percent": percent},
            "chats": chats,
            "totals": {"usd": round(total, 2),
                       "by_model": {k: round(v, 2) for k, v in per_model.most_common()},
                       "by_role": {k: round(v, 2) for k, v in per_role.most_common()}},
            "vibe": {"month": month, "usd": round(sum(s["usd"] or 0 for s in in_month), 2),
                     "eur": round(sum(s["usd"] or 0 for s in in_month) * EUR_PER_USD, 2),
                     "sessions": len(in_month), "no_price": sum(s["usd"] is None for s in in_month)}}


def to_disk(s, folder):
    """The file of the window, `<reset day>.json`: the chats with steps in it, and the totals.
    After the reset, the new window has another name, so the old file is not touched again."""
    if not s["window"]["reset"]:
        return None
    d = datetime.datetime.fromtimestamp(seconds(s["window"]["reset"])).strftime("%Y-%m-%d")
    path = pathlib.Path(folder) / f"{d}.json"
    write_json(path, dict(s, chats=[c for c in s["chats"] if c["usd_window"] and c["tool"] == "claude"]))
    return path


def evidence(code, weeks_folder, folder=None):
    """Write the evidence of one chat in the folder of its work, from the weekly files.
    Return (path, "") or (None, the reason)."""
    parts = {}
    for f in sorted(pathlib.Path(weeks_folder).glob("*.json")):
        try:
            s = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        for c in s.get("chats", []):
            if c["log"].startswith(code):
                parts[f.stem] = c
    if not parts:
        return None, f"no weekly file in {weeks_folder} has chat {code}"
    last = parts[max(parts)]
    target = folder or last["work"]
    if not target:
        return None, f"chat {code} has no work folder. Pass --in <folder>"
    d = last["last"][:10] or time.strftime("%Y-%m-%d")
    path = pathlib.Path(target) / "usage" / f"{d}-{last['role']}-{last['code']}.json"
    write_json(path, {"code": last["code"], "title": last["title"], "role": last["role"],
                      "work": str(target), "usd": last["usd"],
                      "weekly": {k: c["weekly"] for k, c in parts.items()},
                      "windows": parts})
    return path, ""


def work_total(folder):
    """(how many pieces of evidence, $, percent of the weekly limits) from `<folder>/usage/*.json`."""
    files = sorted((pathlib.Path(folder) / "usage").glob("*.json"))
    usd = part = 0.0
    for f in files:
        d = json.loads(f.read_text())
        usd += d.get("usd") or 0
        part += sum(v or 0 for v in (d.get("weekly") or {}).values())
    return len(files), usd, part


def windows(folder):
    """The 7-day windows side by side: the percent, the cost, the cost of one percentage point,
    the executor on Haiku next to the price of the same tokens on Sonnet, and the shares by model."""
    print(f"{'reset':10} {'%':>6} {'$':>9} {'$/1%':>7} {'executor haiku $':>17} {'on Sonnet $':>12}  per model")
    for f in sorted(pathlib.Path(folder).glob("*.json")):
        s = json.loads(f.read_text())
        t, pr = s["totals"], s["window"]["percent"] or 0
        h = [x for c in s["chats"] for x in c["agents"] if x["type"] == "executor" and "haiku" in x["model"]]
        shares = " ".join(f"{k}:{v / t['usd']:.0%}" for k, v in t["by_model"].items()) if t["usd"] else ""
        print(f"{f.stem:10} {pr:6.1f} {t['usd']:9.2f} {(t['usd'] / pr if pr else 0):7.2f} "
              f"{sum(x['usd'] for x in h):17.2f} {sum(x['usd_sonnet'] for x in h):12.2f}  {shares}")
    return 0


def agent(logs, aid):
    """The cost of one agent, from its log, of the same tokens at the price of Sonnet, and the
    context peak, that is, the largest request. The agents of a Workflow team sit one folder lower."""
    found = sorted(pathlib.Path(logs).glob(f"*/*/subagents/**/agent-{aid}.jsonl"))
    if not found:
        print(f"usage: no agent {aid} in {logs}", file=sys.stderr)
        return 2
    st = read_log(found[0], empty(), time.time())
    print(f"{meta(found[0]).get('agentType', 'agent')} {st['model']}: ${st['usd']:.2f}. "
          f"Same tokens on Sonnet: ${st['usd_sonnet']:.2f}. Context peak: {st['peak']}")
    return 0


def team(logs, wid):
    """One row for each agent of the team: the label, the model and the context peak, separated by tabs."""
    found = sorted(pathlib.Path(logs).glob(f"*/*/subagents/workflows/{wid}/agent-*.jsonl"))
    if not found:
        print(f"usage: no team {wid} in {logs}", file=sys.stderr)
        return 2
    for g in found:
        st = read_log(g, empty(), time.time())
        print(f"{meta(g).get('description', g.stem)}\t{st['model']}\t{st['peak']}")
    return 0


def vibe_prices(vibe):
    """The prices of the models in the `config.toml` of Vibe, by alias: (input, from cache, output),
    in dollars per million. Without `cached_input_price`, the cache costs the same as input, as Vibe does."""
    import tomllib  # only here, so the rest of the tool runs on Python 3.9 too
    try:
        with open(pathlib.Path(vibe) / "config.toml", "rb") as f:
            conf = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    prices = {}
    for m in conf.get("models", []):
        if "alias" in m:
            input_, cache = m.get("input_price") or 0, m.get("cached_input_price")
            prices[m["alias"]] = (input_, input_ if cache is None else cache, m.get("output_price") or 0)
    return prices


def vibe_sessions(vibe):
    """The Vibe sessions, oldest first: the added-up tokens of each and the cost at the prices
    in `config.toml`. A session on an undeclared model has `usd` None. A half-written session is skipped."""
    prices, found = vibe_prices(vibe), []
    for current in sorted((pathlib.Path(vibe) / "logs/session/unified").glob("*/CURRENT")):
        d = current.parent
        try:
            gen = d / "generations" / json.loads(current.read_text(encoding="utf-8"))["generation"]
            session = json.loads((gen / "projection-state.json").read_text(encoding="utf-8"))["snapshot"]["session"]
            rt = json.loads((gen / "runtime-state.json").read_text(encoding="utf-8")).get("session_metadata") or {}
            meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        except (OSError, ValueError, KeyError, TypeError):
            continue
        u = session.get("tokenUsage") or {}
        cache = u.get("cachedInputTokens") or 0
        input_ = (u.get("inputTokens") or 0) - cache  # inputTokens counts the cache too
        output = u.get("outputTokens") or 0
        p = prices.get(rt.get("active_model"))
        found.append({
            "id": d.name, "start": meta.get("start_time") or "", "end": meta.get("end_time"),
            "cwd": rt.get("cwd") or (meta.get("environment") or {}).get("working_directory"),
            "model": rt.get("active_model"), "title": session.get("preview") or meta.get("title") or "",
            "input": input_, "cache": cache, "output": output,
            "usd": round((input_ * p[0] + cache * p[1] + output * p[2]) / 1e6, 6) if p else None})
    return sorted(found, key=lambda s: s["start"])


def vibe_month(vibe, month):
    """The Vibe sessions that started in the given month, YYYY-MM, one row each, then their sum."""
    ses = [s for s in vibe_sessions(vibe) if s["start"].startswith(month)]
    for s in ses:
        usd = "—" if s["usd"] is None else f"{s['usd']:.2f}"
        print(f"{s['start'][:16]}  {s['model'] or '?':12} {usd:>7} $  {s['title'][:60]}")
    no_price = sum(s["usd"] is None for s in ses)
    total = sum(s["usd"] or 0 for s in ses)
    print(f"Vibe, {month}: €{total * EUR_PER_USD:.2f} estimated, from ${total:.2f} at the prices in config.toml, "
          f"sessions: {len(ses)}" + (f", no price: {no_price}" if no_price else ""))
    return 0


def main():
    ap = argparse.ArgumentParser(description="where the tokens went, per session")
    ap.add_argument("--logs", default=str(pathlib.Path.home() / ".claude" / "projects"))
    ap.add_argument("--sessions", type=int, default=12)
    ap.add_argument("--after", default="", help="only the sessions that started on or after this day, YYYY-MM-DD")
    ap.add_argument("--by-role", action="store_true", help="by session role, then by model and effort")
    ap.add_argument("--state", action="store_true", help="the state of all the chats, as JSON, for the panel in the app")
    ap.add_argument("--week", type=float, metavar="PERCENT", help="with --state: the percent used of the 7-day limit")
    ap.add_argument("--reset", metavar="ISO", help="with --state: when the 7-day limit resets")
    ap.add_argument("--weeks", metavar="FOLDER",
                    help="with --state: write the file of the window here. With --evidence: read from here")
    ap.add_argument("--app", default=str(APP), help="the files of the desktop app, one for each chat")
    ap.add_argument("--cache", default=str(STATE), help="where the tool keeps how much it read of each log")
    ap.add_argument("--evidence", metavar="CODE", help="write the evidence of the chat in the folder of its work")
    ap.add_argument("--in", dest="folder", metavar="FOLDER", help="with --evidence: another folder than the work found")
    ap.add_argument("--work", metavar="FOLDER", help="what the work cost, from the evidence in FOLDER/usage/")
    ap.add_argument("--windows", metavar="FOLDER", help="the weekly files in FOLDER, side by side")
    ap.add_argument("--agent", metavar="ID", help="the cost of one agent, and of the same tokens on Sonnet")
    ap.add_argument("--workflow", metavar="ID", help="the agents of a Workflow team: label, model and context peak")
    ap.add_argument("--vibe", default=str(VIBE), help="the folder of Mistral Vibe, VIBE_HOME. Default ~/.vibe")
    ap.add_argument("--vibe-sessions", action="store_true", help="the Vibe sessions of one month, with their cost")
    ap.add_argument("--month", default=datetime.date.today().strftime("%Y-%m"),
                    help="with --vibe-sessions: the month, YYYY-MM. Default: this month")
    a = ap.parse_args()

    if a.vibe_sessions:
        return vibe_month(a.vibe, a.month)
    if a.windows:
        return windows(a.windows)
    if a.work:
        n, usd, part = work_total(a.work)
        if not n:
            print(f"usage: no evidence in {a.work}/usage/", file=sys.stderr)
            return 2
        print(f"the work cost ${usd:.2f} and {part:.1f}% of the weekly limits, from {n} chats")
        return 0
    if a.evidence:
        path, reason = evidence(a.evidence, a.weeks or WEEKS, a.folder)
        if not path:
            print(f"usage: {reason}", file=sys.stderr)
            return 2
        print(path)
        return 0
    if a.agent:
        return agent(a.logs, a.agent)
    if a.workflow:
        return team(a.logs, a.workflow)
    if a.state:
        s = state(a.logs, a.app, a.cache, a.week, a.reset, a.vibe)
        if a.weeks:
            to_disk(s, a.weeks)
        print(json.dumps(s, ensure_ascii=False))
        return 0

    files = [f for f in sorted(pathlib.Path(a.logs).glob("*/*.jsonl")) if day(f) >= a.after]
    if not files:
        print(f"usage: no logs found in {a.logs}", file=sys.stderr)
        return 2
    if a.by_role:
        return by_role(files)

    sessions = []
    for f in files:
        d, c, models = session(f)
        if c["steps"]:
            sessions.append((d, f.name[:8], c, models))
    if not sessions:
        print(f"usage: no answer with a known model in {a.logs}", file=sys.stderr)
        return 2

    sessions.sort(key=lambda s: -total_of(s[2]))
    t = collections.Counter()
    for s in sessions:
        t.update(s[2])
    total = total_of(t)

    print(f"sessions: {len(sessions)}   API-equivalent total: ${total:.2f}")
    print(f"  output: {share(t['output'], total)}   cache read: {share(t['read'], total)}   "
          f"cache written: {share(t['written'], total)}   input: {share(t['input'], total)}")
    print()
    print(f"{'day':10} {'session':8} {'$':>7} {'steps':>5} {'avg ctx':>9} "
          f"{'output':>6} {'read':>6} {'written':>7}  models")
    for d, sid, c, models in sessions[:a.sessions]:
        s = total_of(c)
        print(f"{d:10} {sid:8} {s:7.2f} {c['steps']:5} {c['context'] // c['steps']:9} "
              f"{share(c['output'], s):>6} {share(c['read'], s):>6} {share(c['written'], s):>7}  "
              + " ".join(f"{k}:{v}" for k, v in models.most_common(3)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
