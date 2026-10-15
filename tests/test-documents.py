#!/usr/bin/env python3
"""Test for `bin/documents.py`.

No testing framework: each test makes a git repository in a temporary folder, commits
the code, the documents and the map at fixed times, then calls the tool as a separate
process. It is run with `python3 tests/test-documents.py`.
"""
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


TOOL = project_root() / "bin" / "documents.py"

MAP = ("# Map\n\n## Checks\n\n| a | b | c | check |\n|---|---|---|---|\n\n"
       "## Documents\n\n| document | the code it describes |\n|---|---|\n"
       "| `README.md` | `bin/tool.sh` |\n| `docs/history.md` | — |\n")


def commit(base, files, day, message="p", delete=()):
    """Write the files, delete `delete`, and commit at the fixed time of the given day."""
    for path, content in files.items():
        f = base / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding="utf-8")
    for path in delete:
        (base / path).unlink()
    date = f"2026-01-{day:02d}T10:00:00"
    env = dict(os.environ, GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
    for args in (["add", "-A"],
                 ["-c", "user.email=p@p", "-c", "user.name=p", "commit", "-qm", message]):
        subprocess.run(["git", "-C", str(base), *args], capture_output=True, check=True, env=env)


def repository(d, doc_map=MAP):
    base = pathlib.Path(d)
    subprocess.run(["git", "init", "-q", str(base)], check=True)
    commit(base, {"IMPACT.md": doc_map, "README.md": "# R\n", "docs/history.md": "# H\n",
                  "bin/tool.sh": "echo 1\n"}, day=1)
    return base


def run(base, *options):
    p = subprocess.run([sys.executable, str(TOOL), str(base), *options],
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def test_everything_current_exits_0():
    with tempfile.TemporaryDirectory() as d:
        code, output = run(repository(d))
    assert code == 0, output


def test_code_changed_after_document_needs_a_reread():
    with tempfile.TemporaryDirectory() as d:
        base = repository(d)
        commit(base, {"bin/tool.sh": "echo 2\n"}, day=2)
        code, output = run(base)
    assert code == 1, output
    assert "reread needed: README.md" in output, output
    assert "docs/history.md" not in output, output
    assert "documentation" in output, output


def test_document_changed_after_code_is_current():
    with tempfile.TemporaryDirectory() as d:
        base = repository(d)
        commit(base, {"bin/tool.sh": "echo 2\n"}, day=2)
        commit(base, {"README.md": "# R\n\nIt now says 2.\n"}, day=3)
        code, output = run(base)
    assert code == 0, output


def test_reread_mark_in_message_clears_the_document():
    with tempfile.TemporaryDirectory() as d:
        base = repository(d)
        commit(base, {"bin/tool.sh": "echo 2\n"}, day=2)
        commit(base, {"other.txt": "x\n"}, day=3,
               message="Something else changes, and README.md is reread and still true")
        code, output = run(base)
    assert code == 0, output


def test_romanian_mark_in_message_clears_the_document():
    with tempfile.TemporaryDirectory() as d:
        base = repository(d)
        commit(base, {"bin/tool.sh": "echo 2\n"}, day=2)
        commit(base, {"other.txt": "x\n"}, day=3,
               message="Altceva se schimbă, iar README.md e recitit și încă adevărat")
        code, output = run(base)
    assert code == 0, output


def test_mark_older_than_the_code_does_not_count():
    with tempfile.TemporaryDirectory() as d:
        base = repository(d)
        commit(base, {"other.txt": "x\n"}, day=2, message="README.md is reread")
        commit(base, {"bin/tool.sh": "echo 2\n"}, day=3)
        code, output = run(base)
    assert code == 1, output


def test_uncommitted_change_needs_a_reread():
    with tempfile.TemporaryDirectory() as d:
        base = repository(d)
        (base / "bin/tool.sh").write_text("echo 3\n", encoding="utf-8")
        code, output = run(base)
    assert code == 1, output
    assert "uncommitted" in output, output


def test_missing_section_exits_2():
    with tempfile.TemporaryDirectory() as d:
        code, output = run(repository(d, doc_map="# Map\n\n## Checks\n"))
    assert code == 2, output
    assert "no map" in output, output


def test_romanian_section_name_works():
    with tempfile.TemporaryDirectory() as d:
        base = repository(d, doc_map=MAP.replace("## Documents", "## Documentele"))
        commit(base, {"bin/tool.sh": "echo 2\n"}, day=2)
        code, output = run(base)
    assert code == 1, output
    assert "reread needed: README.md" in output, output


def test_complete_passes_on_the_whole_map():
    with tempfile.TemporaryDirectory() as d:
        code, output = run(repository(d), "--complete")
    assert code == 0, output


def test_complete_catches_a_document_without_a_row():
    with tempfile.TemporaryDirectory() as d:
        base = repository(d)
        (base / "docs/new.md").write_text("# New\n", encoding="utf-8")
        code, output = run(base, "--complete")
    assert code == 1, output
    assert "no row: docs/new.md" in output, output


def test_complete_catches_vanished_code():
    with tempfile.TemporaryDirectory() as d:
        base = repository(d)
        commit(base, {}, day=2, delete=["bin/tool.sh"])
        code, output = run(base, "--complete")
    assert code == 1, output
    assert "code no longer exists: README.md -> bin/tool.sh" in output, output


def test_complete_catches_a_vanished_document():
    with tempfile.TemporaryDirectory() as d:
        base = repository(d)
        commit(base, {}, day=2, delete=["docs/history.md"])
        code, output = run(base, "--complete")
    assert code == 1, output
    assert "document no longer exists: docs/history.md" in output, output


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"{len(tests)} tests passed")


if __name__ == "__main__":
    main()
