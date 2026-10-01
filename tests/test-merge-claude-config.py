#!/usr/bin/env python3
"""Test for `bin/merge-claude-config.py`.

No testing framework: each test fabricates a temporary HOME and calls the tool as a
separate process. It is run with `python3 tests/test-merge-claude-config.py`.
"""
import atexit
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile


def project_root():
    """The project's root: the folder that holds the `test` collector."""
    d = pathlib.Path(os.environ.get("TESTS_ROOT") or __file__).resolve()
    if d.is_file():
        d = d.parent
    while d != d.parent:
        if os.access(d / "test", os.X_OK):
            return d
        d = d.parent
    raise SystemExit("cannot find the project root")


TOOL = project_root() / "bin" / "merge-claude-config.py"
LOCK = project_root() / "plugins.lock.json"


def fabricated_home(initial_settings):
    h = pathlib.Path(tempfile.mkdtemp())
    atexit.register(shutil.rmtree, h, True)  # otherwise a fabricated HOME is left behind on every run
    (h / ".claude").mkdir(parents=True)
    if initial_settings is not None:
        (h / ".claude/settings.json").write_text(json.dumps(initial_settings))
    return h


def run(home):
    p = subprocess.run([sys.executable, str(TOOL), str(LOCK), str(home)],
                        capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def test_foreign_plugin_survives():
    """A plugin the lockfile does not know stays enabled.

    ⚠ That is exactly the defect: until today the restore rewrote `settings.json` from
      scratch, so on a machine where the human was already using Claude Code it deleted
      their plugins without saying anything.
    """
    h = fabricated_home({"enabledPlugins": {"theirs@their-market": True},
                         "theme": "dark"})
    code, output = run(h)
    assert code == 0, output
    s = json.loads((h / ".claude/settings.json").read_text())
    assert s["enabledPlugins"]["theirs@their-market"] is True, s
    assert s["theme"] == "dark", s
    assert s["enabledPlugins"]["superpowers@superpowers-marketplace"] is True, s


def test_empty_home_merges_as_before():
    h = fabricated_home(None)
    code, output = run(h)
    assert code == 0, output
    s = json.loads((h / ".claude/settings.json").read_text())
    assert len(s["enabledPlugins"]) == 4, s


def test_broken_json_is_not_rewritten():
    """A file we cannot read is not replaced with an empty one."""
    h = fabricated_home(None)
    (h / ".claude/settings.json").write_text("{ not json")
    code, output = run(h)
    assert code == 2, output
    assert "refused" in output, output
    assert (h / ".claude/settings.json").read_text() == "{ not json"


def test_claude_code_also_reads_agents_md():
    """The setting that makes Claude Code read `AGENTS.md` on its own.

    ⚠ Without it, a session opened in a project does not see the shared rules: their
      import from the root's `CLAUDE.md` steps outside the session folder and does not
      expand. Measured on 1 October 2026, in the session logs.
    """
    h = fabricated_home({"pluginConfigs": {"other@market": {"options": {"x": 1}}}})
    code, output = run(h)
    assert code == 0, output
    s = json.loads((h / ".claude/settings.json").read_text())
    agents = s["pluginConfigs"]["agents-md@builtin"]["options"]
    assert agents["instructionFiles"] == "claude-md-and-agents-md", s
    assert s["pluginConfigs"]["other@market"] == {"options": {"x": 1}}, s


def test_human_strict_choice_remains():
    h = fabricated_home({"pluginConfigs": {"agents-md@builtin": {"options": {"instructionFiles": "claude-md"}}}})
    code, output = run(h)
    assert code == 0, output
    s = json.loads((h / ".claude/settings.json").read_text())
    assert s["pluginConfigs"]["agents-md@builtin"]["options"]["instructionFiles"] == "claude-md", s
    assert "claude-md" in output and "warning" in output, output


failed = 0
for name, fn in list(globals().items()):
    if name.startswith("test_") and callable(fn):
        try:
            fn()
            print(f"  ✓ {name}")
        except AssertionError as e:
            failed += 1
            print(f"  ✗ {name}: {e}")

print(f"\n  tests failed: {failed}")
sys.exit(1 if failed else 0)
