#!/usr/bin/env python3
"""usage.py — where the tokens went, session by session.

It reads Claude Code's local logs and counts each session at the API price: uncached
input, cache write, cache read, output. It is not the subscription's bill; the
proportions between the columns are what matters.

    python3 bin/usage.py                  # all the sessions on this machine
    python3 bin/usage.py --sessions 5     # only the five most expensive
    python3 bin/usage.py --logs DIR       # another folder of logs

⚠ AN ANSWER IS COUNTED ONLY ONCE. The log writes an answer with several blocks on
  several lines, each with the same `usage`. Without deduplicating on `message.id`, a
  session would come out two or three times more expensive than it was.

⚠ THE PRICE IS THE EXACT MODEL'S, not the family's. Opus 5.5 costs 4/20 and reads the
  cache at 5%, Opus 5 costs 5/25 and reads it at 10%: at the family's price, a session
  on 5.5 comes out a quarter more expensive than it was, and the cache-read share is
  inflated. The prices below are from the model table of the `claude-api` skill;
  before quoting a sum, check there.
"""
import argparse
import collections
import json
import pathlib
import sys

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
    ("haiku", 1, 5, 0.1),
]
WRITE_5M = 1.25         # five-minute cache, as a fraction of the input price
WRITE_1H = 2.0          # one-hour cache


def price(model):
    return next((p for p in PRICE if p[0] in model), None)


def session(path):
    """(day, sums in $ × million, steps per model) for one log."""
    c = collections.Counter()
    models = collections.Counter()
    seen = set()
    day = ""
    with open(path, errors="replace") as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            day = day or (d.get("timestamp") or "")[:10]
            m = d.get("message") or {}
            u = m.get("usage")
            if d.get("type") != "assistant" or not u or m.get("id") in seen:
                continue
            seen.add(m.get("id"))
            p = price(m.get("model", ""))
            if not p:
                continue
            _, inp, out, read = p
            cc = u.get("cache_creation") or {}
            w5 = cc.get("ephemeral_5m_input_tokens", 0) if cc else u.get("cache_creation_input_tokens", 0)
            w1 = cc.get("ephemeral_1h_input_tokens", 0)
            c["input"] += u.get("input_tokens", 0) * inp
            c["written"] += (w5 * WRITE_5M + w1 * WRITE_1H) * inp
            c["read"] += u.get("cache_read_input_tokens", 0) * read * inp
            c["output"] += u.get("output_tokens", 0) * out
            c["context"] += u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + w5 + w1
            c["steps"] += 1
            models[m["model"].replace("claude-", "")] += 1
    return day, c, models


def total_of(c):
    return (c["input"] + c["written"] + c["read"] + c["output"]) / 1e6


def share(x, of):
    return f"{x / 1e6 / of:.0%}" if of else "-"


def main():
    ap = argparse.ArgumentParser(description="where the tokens went, per session")
    ap.add_argument("--logs", default=str(pathlib.Path.home() / ".claude" / "projects"))
    ap.add_argument("--sessions", type=int, default=12)
    a = ap.parse_args()

    files = sorted(pathlib.Path(a.logs).glob("*/*.jsonl"))
    if not files:
        print(f"usage: no logs found in {a.logs}", file=sys.stderr)
        return 2

    sessions = []
    for f in files:
        day, c, models = session(f)
        if c["steps"]:
            sessions.append((day, f.name[:8], c, models))
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
    for day, sid, c, models in sessions[:a.sessions]:
        s = total_of(c)
        print(f"{day:10} {sid:8} {s:7.2f} {c['steps']:5} {c['context'] // c['steps']:9} "
              f"{share(c['output'], s):>6} {share(c['read'], s):>6} {share(c['written'], s):>7}  "
              + " ".join(f"{k}:{v}" for k, v in models.most_common(3)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
