#!/usr/bin/env python3
"""The framework reminder, sent at the end of a model reply, for Claude Code and for Vibe.

The tool's hook calls it with the hook input on stdin: `Stop` for Claude (`transcript_path`, the
session log, and `stop_hook_active`), `post_agent` for Vibe (`transcript_path`, the session folder).
The script reads the session steps with the bench parsers. At the first slip in the last reply, it
prints the decision that sends the model one sentence: `block` for Claude, `deny` for Vibe, with
the reminder in `reason`. With no slip, or on any error, it prints nothing and exits 0: a broken
reminder must not stop the session.

  reminder.py --tool claude|vibe
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "bench"))
import tools  # noqa: E402
import checks  # noqa: E402

SKILL = "You loaded the {0} skill without announcing it. Write the sentence now: \"Using {0} to <purpose>.\""
PERCENT = "Tell the human how much is done, in percent, and how much time is left, with the sentence \"N% done; about M minutes left.\""
READER = "Framework rule: past two pages, the reader agent does the research."
ROLE = "The human asked for the {0} role. Load the {0} skill now, before any other tool. Written code does not replace the role."
# The role the human asked for and its skill, in the wording of requests in AGENTS.md, the bench and the handoffs.
ROLES = (("spec", re.compile(r"\blet'?s (?:write|do) the spec\b|\bwrite the spec\b|\bspec session\b", re.I)),
         ("plans", re.compile(r"\bwrite the plans?\b|\bthe plans are to be written\b"
                              r"|\bplans session\b", re.I)),
         ("orchestration", re.compile(r"\borchestrat(?:e|es|ing)\b|\borchestration session\b", re.I)))


def requested_role(steps):
    """The skill of the role asked for in the human's last message, when the session never loaded it; else None."""
    human = next((s["text"] for s in reversed(steps) if s["kind"] == "human"), "")
    loaded = {s["target"].split(":")[-1] for s in steps if s["kind"] == "skill"}
    return next((skill for skill, pattern in ROLES if pattern.search(human) and skill not in loaded), None)


def vibe_entries(folder):
    """The entries of the Vibe session at the moment of the hook, from `journal/*.jsonl`. The journal
    keeps the entries of the turn as they happen (`projection_delta`). The reply under judgment is
    only in the last request to the `post_agent_turn` hook, so it is added at the end as the model's message."""
    entries, candidate = {}, None
    for f in sorted(Path(folder, "journal").glob("*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            p = e.get("payload") or {}
            if e.get("type") == "projection_delta":
                for x in p.get("delta") or []:
                    entry = x.get("entry")
                    if x.get("op") in ("append_entry", "replace_entry") and isinstance(entry, dict) and entry.get("id"):
                        entries[entry["id"]] = entry
            elif e.get("type") == "action_intent" and p.get("kind") == "hook":
                request = p.get("request") or {}
                if request.get("hook") == "post_agent_turn":
                    candidate = ((request.get("input") or {}).get("candidate") or {}).get("message") or {}
    result = list(entries.values())
    if candidate is not None:
        text = [c for c in candidate.get("content") or [] if c.get("type") == "text"]
        result.append({"id": "candidate", "type": "message", "role": "assistant", "content": text})
    return result


def slip(steps, tool):
    """The reminder for the first slip in the last reply (the steps since the human's last message), or None.
    The order: role asked for without its skill, unannounced skill, percentages, pages."""
    if not steps:
        return None
    i0 = next(i for i, s in enumerate(steps) if s["turn"] == steps[-1]["turn"])
    last = steps[i0:]
    if any(s["kind"] == "reminder" for s in last):
        return None  # at most one reminder per reply
    # One reminder per turn, so it carries all of them: each unannounced skill, then the percentages, then the reader.
    unannounced = list(dict.fromkeys(steps[i]["target"].split(":")[-1] for i in checks._skills(steps)
                                     if i >= i0 and not checks.announced(steps, i, False)))
    messages = [SKILL.format(unannounced[0]) + (f" The same for {', '.join(unannounced[1:])}." if unannounced[1:] else "")] if unannounced else []
    role = requested_role(steps)
    if role:  # the worst slip goes first: without the role, the rest of the session is on the wrong path
        messages.insert(0, ROLE.format(role))
    if checks.first_change(last) is not None and not any(
            s["kind"] == "text" and checks.PERCENT.search(s["text"]) for s in last):
        messages.append(PERCENT)
    # For Claude, the panel reminds about pages. For Vibe, the reader loads no skills and may read.
    if (tool == "vibe" and any(s["kind"] == "skill" for s in steps)
            and sum(map(checks.page_read, steps)) > 2 and any(map(checks.page_read, last))):
        messages.append(READER)
    if len(messages) > 1:  # numbered, so the model does not fix only the first
        return f"You have {len(messages)} things to fix, all of them, in the next reply: " + " ".join(f"({n}) {m}" for n, m in enumerate(messages, 1))
    return messages[0] if messages else None


def main():
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("--tool", choices=("claude", "vibe"), required=True)
    tool = a.parse_args().tool
    try:
        data = json.loads(sys.stdin.read() or "{}")
        if data.get("stop_hook_active"):
            return 0
        if tool == "claude":
            steps = tools.steps_claude(data["transcript_path"])
        else:
            steps = tools.steps_from_entries(vibe_entries(data["transcript_path"]))
        reason = slip(steps, tool)
    except Exception:  # a broken reminder stays silent: the session goes on
        return 0
    if reason:
        print(json.dumps({"decision": "block" if tool == "claude" else "deny", "reason": reason}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
