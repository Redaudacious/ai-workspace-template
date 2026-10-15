#!/usr/bin/env python3
"""Test for `bin/values.py`.

No testing framework: each test makes a git repository in a temporary folder, with the
documents from before committed on `main`, writes the documents from after over them
and calls the tool as a separate process. It is run with `python3 tests/test-values.py`.
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


TOOL = project_root() / "bin" / "values.py"


def write(base, files):
    """Writes the given files; `None` instead of content deletes the file."""
    for path, content in files.items():
        f = base / path
        if content is None:
            f.unlink()
            continue
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding="utf-8")


def run(before, after, paths=("README.md", "docs"), removed=None):
    """Commits `before` on `main`, writes `after` on disk, calls the tool.

    Returns (code, output). `removed`, if given, is the content of the file of values
    removed on purpose.
    """
    with tempfile.TemporaryDirectory() as d:
        base = pathlib.Path(d)
        write(base, before)
        for arguments in (["init", "-q", "-b", "main"], ["add", "-A"],
                          ["-c", "user.email=p@p", "-c", "user.name=p",
                           "commit", "-qm", "before"]):
            subprocess.run(["git", "-C", str(base), *arguments],
                           check=True, capture_output=True)
        write(base, after)
        command = [sys.executable, str(TOOL), "main", *paths]
        if removed is not None:
            (base / "removed.tsv").write_text(removed, encoding="utf-8")
            command += ["--removed", "removed.tsv"]
        p = subprocess.run(command, cwd=base, capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr


README = "# P\n\nThe check: `python3 bin/check-docs.py .`, with 150 lines.\n"


def test_nothing_changed():
    code, output = run({"README.md": README}, {})
    assert code == 0, output
    assert "missing: 0" in output, output


def test_a_value_moved_into_another_document_is_not_a_loss():
    code, output = run({"README.md": README}, {
        "README.md": "# P\n\nThe check lives in the guide, with 150 lines.\n",
        "docs/how-to/guide.md": "# Guide\n\nRun `python3 bin/check-docs.py .`.\n",
    })
    assert code == 0, output


def test_a_lost_value_exits_with_one():
    code, output = run({"README.md": README}, {
        "README.md": "# P\n\nThe check is done with the tool, with 150 lines.\n",
    })
    assert code == 1, output
    # The line is copied into the file of removed values: the value, then the document.
    assert "MISSING\tpython3 bin/check-docs.py .\tREADME.md\n" in output, output


def test_a_lost_value_removed_on_purpose():
    code, output = run({"README.md": README}, {
        "README.md": "# P\n\nThe check is done with the tool, with 150 lines.\n",
    }, removed=("# value\tdocument\treason\n"
                "python3 bin/check-docs.py .\tREADME.md\tthe command now lives in the guide\n"))
    assert code == 0, output
    assert "removed on purpose: 1" in output, output


def test_a_lost_code_line():
    block = "# P\n\n```bash\n./bin/check-lock.sh\n./bin/check-maps.sh\n```\n"
    code, output = run({"README.md": block}, {
        "README.md": "# P\n\n```bash\n./bin/check-lock.sh\n```\n",
    })
    assert code == 1, output
    assert "./bin/check-maps.sh" in output, output


def test_a_value_moved_from_prose_into_a_block_is_not_a_loss():
    code, output = run({"README.md": "# P\n\nRun `./test`.\n"}, {
        "README.md": "# P\n\n```bash\n./test && ./bin/check-maps.sh\n```\n",
    })
    assert code == 0, output


def test_a_prompt_broken_differently_across_lines_is_not_a_loss():
    """A prompt from a block, broken at another place, says the same thing."""
    code, output = run({"README.md": (
        "# P\n\n```\nI want a script greeting.sh that takes a name\n"
        "and prints the greeting, plus a test.\n```\n")}, {
        "README.md": (
            "# P\n\n```\nI want a script greeting.sh that takes\n"
            "a name and prints the greeting, plus a test.\n```\n")})
    assert code == 0, output


def test_a_lost_link_target():
    code, output = run({
        "README.md": "# P\n\n[The glossary](docs/reference/glossary.md)\n",
        "docs/reference/glossary.md": "# Glossary\n",
    }, {
        "README.md": "# P\n\nThe glossary is missing.\n",
    })
    assert code == 1, output
    assert "docs/reference/glossary.md" in output, output


def test_a_target_written_from_another_folder_is_the_same():
    """A link moved into another folder changes its form, not its target."""
    code, output = run({
        "README.md": "# P\n\n[The glossary](docs/reference/glossary.md#records)\n",
        "docs/reference/glossary.md": "# Glossary\n",
    }, {
        "README.md": "# P\n\n[The guide](docs/how-to/guide.md)\n",
        "docs/how-to/guide.md": "# Guide\n\n[The glossary](../reference/glossary.md)\n",
    })
    assert code == 0, output


def test_a_one_digit_number_is_not_a_value():
    code, output = run({"README.md": "# P\n\nThere are 4 plugins.\n"}, {
        "README.md": "# P\n\nThere are four plugins.\n",
    })
    assert code == 0, output


def test_a_lost_number_is_not_covered_by_a_longer_one():
    """`150` does not stay in the document only because `1500` appears."""
    code, output = run({"README.md": "# P\n\nThe threshold is 150 lines.\n"}, {
        "README.md": "# P\n\nThe threshold is 1500 characters.\n",
    })
    assert code == 1, output
    assert "150" in output, output


def test_a_deleted_document_loses_its_values():
    code, output = run({
        "README.md": "# P\n\n[Guide](docs/how-to/guide.md)\n",
        "docs/how-to/guide.md": "# Guide\n\nRun `./bin/restore-env.sh`.\n",
    }, {
        "README.md": "# P\n\nNothing.\n",
        "docs/how-to/guide.md": None,
    })
    assert code == 1, output
    assert "./bin/restore-env.sh" in output, output


def test_a_new_document_has_nothing_to_lose():
    code, output = run({"README.md": README}, {
        "docs/explanation/new.md": "# New\n\nWith `a value` and 42 lines.\n",
    })
    assert code == 0, output


def test_a_revision_that_does_not_exist_exits_with_two():
    """A verifier that cannot read the state from before is not allowed to pass."""
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["git", "-C", d, "init", "-q"], check=True)
        p = subprocess.run([sys.executable, str(TOOL), "does-not-exist", "README.md"],
                           cwd=d, capture_output=True, text=True)
    assert p.returncode == 2, p.stdout + p.stderr


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"{len(tests)} tests passed")


if __name__ == "__main__":
    main()
