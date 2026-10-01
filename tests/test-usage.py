#!/usr/bin/env python3
"""Test for `bin/usage.py`.

No testing framework: the logs are fabricated in a temporary folder, the tool is called
as a separate process, and the output is read as text.
"""
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
    check("API-equivalent total: $7.45" in p.stdout, "the total of the three: 7.45 $")

print()
print("  ✓ all tests pass" if failed == 0 else f"  ✗ {failed} tests failed")
sys.exit(1 if failed else 0)
