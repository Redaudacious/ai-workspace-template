#!/usr/bin/env python3
"""Gemini's memento in Antigravity: a `PreInvocation` hook, called before every model call.
It reminds the model to say in chat which skill it read and which file it changed, to look
up the source before it offers options, and to stop after a skipped answer.

The written rules were not enough: Gemini 3.1 Pro stayed silent between tools and announced
the skill only at the end. The memento reads the model's last response in the conversation
log and injects a transient message only after those two moments. Otherwise it returns `{}`.
`bin/antigravity.sh` registers it in `~/.gemini/config/hooks.json`.
"""
import json
import sys

EDITS = {"write_to_file", "replace_file_content", "multi_replace_file_content"}
SEARCHES = {"search_web", "read_url_content"}
# Looking up the source before the options belongs to the spec session. After these skills, a
# question with a "Recommended" option is the closing "yes", and the reminder would send
# Gemini to the web.
NO_SEARCH = ("plans", "writing-plans", "execute", "executing-plans")


def steps(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f.read().splitlines()]


def has_recommended_option(args):
    return any("Recommended" in str(o) for q in args.get("questions") or [] for o in q.get("options") or [])


def memento(payload):
    all_steps = steps(payload["transcriptPath"])
    responses = [s for s in all_steps if s.get("type") == "PLANNER_RESPONSE"]
    step = responses[-1] if responses else {}
    last = max((i for i, s in enumerate(all_steps) if s.get("type") == "PLANNER_RESPONSE"), default=len(all_steps))
    skipped = any("User Skipped" in str(s.get("content")) for s in all_steps[last + 1:])
    calls = [c for s in responses for c in s.get("tool_calls") or []]
    searched = any(c.get("name") in SEARCHES for c in calls) or any(
        c.get("name") == "view_file" and str((c.get("args") or {}).get("AbsolutePath")).endswith(
            tuple(f"/{s}/SKILL.md" for s in NO_SEARCH)) for c in calls)
    artifacts = payload.get("artifactDirectoryPath")
    messages = []
    for call in step.get("tool_calls") or []:
        args = call.get("args") or {}
        path = args.get("AbsolutePath") or args.get("TargetFile") or ""
        if call.get("name") == "view_file" and path.endswith("/SKILL.md"):
            name = path.split("/")[-2]
            # using-superpowers is read at every start, so announcing it would be noise.
            if name == "using-superpowers":
                continue
            message = (f"You just read the skill `{name}`. Now write `Using {name} to [purpose]` in the chat, "
                       "not only in your thinking, in the same response as your next tool call.")
        elif call.get("name") in EDITS and not (artifacts and path.startswith(artifacts)):
            message = (f"You just changed `{path.rsplit('/', 1)[-1]}`. Now write one full sentence in the chat, "
                       "in the same response as your next tool call: what changed, what the result was, "
                       "and what comes next.")
        elif call.get("name") == "ask_question" and (skipped or (not searched and has_recommended_option(args))):
            parts = []
            if not searched and has_recommended_option(args):
                # Bench spec stage, round 1: the options with `cron` and `systemd` came with no
                # search, although GEMINI.md requires one.
                parts.append("You asked a question with options, and this conversation has no search. An "
                             "option that names a tool, a service or a package from outside the workspace "
                             "rests on its source. Search for it now with `search_web` and read the page "
                             "with `read_url_content`, before the design, as GEMINI.md says.")
            if skipped:
                # Round 2: "You skipped the question, I take it as a yes". Round 3: stopping alone
                # replaced the search, because without an interface every question is skipped.
                # Now the two work together.
                parts.append("The answer to the question was skipped, so it is not a yes. "
                             + ("After the search, end your turn" if len(parts) else "End your turn now")
                             + ": write the question in the chat and call no tool until the human answers, "
                             "as GEMINI.md says.")
            message = " ".join(parts)
        else:
            continue
        if message not in messages:
            messages.append(message)
    return {"injectSteps": [{"ephemeralMessage": " ".join(messages)}]} if messages else {}


if __name__ == "__main__":
    try:
        print(json.dumps(memento(json.load(sys.stdin)), ensure_ascii=False))
    except Exception:  # the hook blocks the agent loop: an error of its own must not stop it
        print("{}")
