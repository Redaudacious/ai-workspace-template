#!/usr/bin/env python3
"""Test for `check-docs.py`.

No testing framework: each test builds its tree in a temporary folder, calls the tool as
a separate process and checks the output plus the exit code. It is run with
`python3 tests/test-check-docs.py`.
"""
import os
import pathlib
import subprocess
import sys
import tempfile

def project_root():
    """The project's root: the folder that holds the `test` collector.

    ⚠ It is NOT asked from git and NOT counted in hyphens. A project without its own
      repository gets from git the root of the workspace; and a count from the file's own
      folder breaks at every move — it broke RIGHT HERE on 16 September 2026, when the
      file left `bin/` for `tests/` and began looking for the tool next to itself, where
      it no longer was.
    """
    d = pathlib.Path(os.environ.get("TESTS_ROOT") or __file__).resolve()
    if d.is_file():
        d = d.parent
    while d != d.parent:
        if os.access(d / "test", os.X_OK):
            return d
        d = d.parent
    raise SystemExit("cannot find the project root")


TOOL = project_root() / "bin" / "check-docs.py"


def write_tree(base, files):
    """Writes a tree of markdown into a folder."""
    for path, content in files.items():
        f = base / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding="utf-8")


def run(files):
    """Builds the tree, calls the tool, returns (code, output)."""
    with tempfile.TemporaryDirectory() as d:
        base = pathlib.Path(d)
        write_tree(base, files)
        p = subprocess.run(
            [sys.executable, str(TOOL), str(base)],
            capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr



def run_with_bits(files, executables=()):
    """Like `run`, but puts the execute bit on the named files.

    ⚠ It exists because `write_tree` writes files without the bit, and the bit is exactly
      what is tested here: since 16 September 2026 the test collector discovers by it, so
      a test without the bit would never run and nothing would say so.
    """
    with tempfile.TemporaryDirectory() as d:
        base = pathlib.Path(d)
        write_tree(base, files)
        for path in executables:
            (base / path).chmod(0o755)
        p = subprocess.run(
            [sys.executable, str(TOOL), str(base)],
            capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr


def run_with_git(files, gitignore, executables=()):
    """Like `run`, but the tree is a git repository with the given `.gitignore`.

    ⚠ It exists because the personal layer rule ASKS GIT whether `records/` is ignored,
      and that is exactly the distinction it makes: in the workspace the folder is ignored
      and a link to it is broken on a fresh clone; in a project it is tracked, and the same
      link is good.
    """
    with tempfile.TemporaryDirectory() as d:
        base = pathlib.Path(d)
        write_tree(base, files)
        for path in executables:
            (base / path).chmod(0o755)
        (base / ".gitignore").write_text(gitignore, encoding="utf-8")
        for args in (["init", "-q"], ["add", "-A"],
                     ["-c", "user.email=p@p", "-c", "user.name=p",
                      "commit", "-qm", "p"]):
            subprocess.run(["git", "-C", str(base), *args],
                           capture_output=True)
        p = subprocess.run([sys.executable, str(TOOL), str(base)],
                           capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr


def test_link_into_the_personal_layer_fails():
    code, output = run_with_git({
        "README.md": "# R\n\n[the decisions](records/decisions/INDEX.md)\n",
        "records/decisions/INDEX.md": "# D\n",
    }, "records/\n")
    assert code == 1, output
    assert "PERSONAL" in output, output


def test_a_tracked_records_is_not_a_personal_layer():
    code, output = run_with_git({
        "README.md": "# R\n\n[the decisions](records/decisions/INDEX.md)\n",
        "records/decisions/INDEX.md": "# D\n",
    }, "nothing/\n")
    assert code == 0, output
    assert "PERSONAL" not in output, output


def test_path_to_the_personal_layer_written_in_prose_does_not_fail():
    code, output = run_with_git({
        "README.md": "# R\n\nThe house rules sit in `records/house-rules.md`.\n",
    }, "records/\n")
    assert code == 0, output
    assert "PATH" not in output, output


def test_clean_tree():
    code, output = run({
        "README.md": "# Project\n\n[Guide](docs/how-to/guide.md)\n",
        "docs/how-to/guide.md": "# How to do it\n\nThe button is pressed.\n",
    })
    assert code == 0, output
    assert "failures: 0" in output, output


def test_broken_link():
    code, output = run({
        "README.md": "# Project\n\n[Missing](docs/how-to/nothing.md)\n",
    })
    assert code == 1, output
    assert "BROKEN" in output, output


def test_orphan():
    code, output = run({
        "README.md": "# Project\n\nNo link.\n",
        "docs/how-to/guide.md": "# How to do it\n\nThe button is pressed.\n",
    })
    assert code == 1, output
    assert "ORPHAN" in output, output
    assert "guide.md" in output, output


def test_target_folder_makes_the_children_reachable():
    """A link to a folder covers the documents inside."""
    code, output = run({
        "README.md": "# Project\n\n[Guides](docs/how-to/)\n",
        "docs/how-to/guide.md": "# How to do it\n\nThe button is pressed.\n",
    })
    assert code == 0, output


def test_the_projects_inside_do_not_enter():
    """Run on the workspace, its own `docs/` is verified, not the projects'."""
    code, output = run({
        "README.md": "# Environment\n\n[Guide](docs/reference/guide.md)\n",
        "docs/reference/guide.md": "# How to do it\n\nThe button is pressed.\n",
        "projects/other/docs/broken.md": "# Other\n\n[Missing](nothing.md)\n",
    })
    assert code == 0, output
    assert "broken.md" not in output, output


def test_the_state_is_not_an_orphan():
    """`STATE.md` is ignored by git, so a link to it would be broken on a fresh clone.
    The map names it without linking it, on purpose."""
    code, output = run({
        "README.md": "# Project\n\nThe state is in `STATE.md`, local.\n",
        "STATE.md": "# State\n\nNothing open.\n",
    })
    assert code == 0, output


SENTENCE = ("The tool exits with zero when the thing verified is in order "
            "and with something else when it is not.")


def test_sentence_repeated_on_the_same_line():
    code, output = run({
        "README.md": f"# Project\n\n[One](docs/reference/a.md) [Two](docs/reference/b.md)\n",
        "docs/reference/a.md": f"# One\n\n{SENTENCE}\n",
        "docs/reference/b.md": f"# Two\n\n{SENTENCE}\n",
    })
    assert code == 1, output
    assert "REPEATED" in output, output


def test_sentence_repeated_broken_across_lines():
    """Markdown breaks the sentence over several lines, in a different place in each file."""
    code, output = run({
        "README.md": "# Project\n\n[One](docs/reference/a.md) [Two](docs/reference/b.md)\n",
        "docs/reference/a.md": ("# One\n\nThe tool exits with zero when the thing verified\n"
                      "is in order and with something else when it is not.\n"),
        "docs/reference/b.md": ("# Two\n\nThe tool exits with zero when the thing\n"
                      "verified is in order and with something else when it is not.\n"),
    })
    assert code == 1, output
    assert "REPEATED" in output, output


def test_a_list_is_not_a_sentence():
    """Two documents with the same short list rows are not a repetition."""
    items = "- one\n- two\n- three\n"
    code, output = run({
        "README.md": "# Project\n\n[One](docs/reference/a.md) [Two](docs/reference/b.md)\n",
        "docs/reference/a.md": f"# One\n\n{items}",
        "docs/reference/b.md": f"# Two\n\n{items}",
    })
    assert code == 0, output


def test_document_too_big():
    code, output = run({
        "README.md": "# Project\n\n[Big](docs/reference/big.md)\n",
        "docs/reference/big.md": "# Big\n\n" + "line\n" * 500,
    })
    assert code == 1, output
    assert "TOO BIG" in output, output


def test_state_exempt_from_size():
    code, output = run({
        "README.md": "# Project\n\nThe state is in `STATE.md`.\n",
        "STATE.md": "# State\n\n" + "line\n" * 500,
    })
    assert code == 0, output


def test_the_records_are_exempt():
    code, output = run({
        "README.md": "# Project\n\nNothing.\n",
        "records/journal/2026-01-01-one.md": f"# One\n\n{SENTENCE}\n" + "line\n" * 500,
        "records/journal/2026-01-02-other.md": f"# Other\n\n{SENTENCE}\n",
    })
    assert code == 0, output


def test_the_same_name_in_two_folders_only_reports():
    code, output = run({
        "README.md": "# Project\n\n[One](docs/reference/x.md) [Two](docs/explanation/x.md)\n",
        "docs/reference/x.md": "# Reference\n\nThe value is 4.\n",
        "docs/explanation/x.md": "# Explanation\n\nThe reason is another.\n",
    })
    assert code == 0, output
    assert "report:" in output, output


def test_broken_anchor():
    code, output = run({
        "README.md": "# Project\n\n[One](docs/reference/x.md#measured-figures)\n",
        "docs/reference/x.md": "# Reference\n\n## Something else\n\nNothing.\n",
    })
    assert code == 1, output
    assert "ANCHOR" in output, output


def test_good_anchor():
    code, output = run({
        "README.md": "# Project\n\n[One](docs/reference/x.md#the-naïve-figures)\n",
        "docs/reference/x.md": "# Reference\n\n## The naïve figures\n\nFour.\n",
    })
    assert code == 0, output


def test_anchor_with_punctuation_and_multiple_spaces():
    """The heading has a long dash, digits glued to a hyphen, and two spaces."""
    code, output = run({
        "README.md": "# Project\n\n[One](docs/reference/x.md#1011-september-the-panel-shell)\n",
        "docs/reference/x.md": "# Reference\n\n## 10–11 September — the  panel shell\n\nYes.\n",
    })
    assert code == 0, output


def test_the_anchors_in_records_are_verified():
    """A broken link in a record is a failure, although the record is not rewritten.

    ⚠ This test asserted exactly the opposite until 16 September 2026, on the argument
    that an old entry is allowed to point to a heading that has since moved. Practice
    contradicted it: on 15 September 2026, the widened verification brought out 46 broken
    links from `records/`, and all were repaired by hand. A link to a section that no
    longer exists does not preserve the history, it makes it unreadable.
    What stays exempt is the CONTENT — the size, the repeated sentences, the reachability.
    """
    code, output = run({
        "README.md": "# Project\n\n[Rec](records/pitfalls/2026-01-01-one.md)\n",
        "records/pitfalls/2026-01-01-one.md": "# One\n\n[Jump](../../README.md#does-not-exist)\n",
    })
    assert code == 1, output
    assert "ANCHOR" in output, output


def test_link_inside_a_code_block_is_not_a_link():
    code, output = run({
        "README.md": (
            "# Project\n\nExample:\n\n"
            "```markdown\n[Something](docs/invented.md)\n```\n"),
    })
    assert code == 0, output
    assert "BROKEN" not in output, output


def test_four_backtick_block_is_removed_whole():
    """A block of four that contains one of three is not cut in half."""
    code, output = run({
        "README.md": (
            "# Project\n\nExample:\n\n"
            "````markdown\n```\n[Something](docs/invented.md)\n```\n````\n"
            "\nThe text after the block.\n"),
    })
    assert code == 0, output
    assert "BROKEN" not in output, output


def test_link_outside_the_block_is_still_verified():
    """Removing the blocks is not allowed to blind the normal verification."""
    code, output = run({
        "README.md": (
            "# Project\n\n```\ncode\n```\n\n[Missing](docs/nothing.md)\n"),
    })
    assert code == 1, output
    assert "BROKEN" in output, output


def test_path_aged_by_a_move():
    """The repository HAS the file, but the document names it in the old place."""
    code, output = run({
        "README.md": "# Project\n\nThe tool sits in `bin/tool.sh`.\n",
        "servers/tools/tool.sh": "#!/bin/bash\necho\n",
    })
    assert code == 1, output
    assert "PATH" in output, output
    assert "bin/tool.sh" in output, output


def test_path_from_another_tree_is_not_a_path_from_here():
    """A plugin package has its own paths. They are not this repository's."""
    code, output = run({
        "README.md": ("# Project\n\nThe hook is `hooks/ponytail-subagent.js`, "
                      "and the bootstrap `scripts/bootstrap-rtk.mjs`.\n"),
    })
    assert code == 0, output


def test_github_repository_name_is_not_a_path():
    """`obra/superpowers-marketplace` looks exactly like `folder/file`."""
    code, output = run({
        "README.md": "# Project\n\n| Source | `obra/superpowers-marketplace` |\n",
    })
    assert code == 0, output


def test_a_lone_folder_name_is_not_a_path():
    """In a table that describes `docs/`, the row is called `tutorial/`.

    A single segment with a trailing slash is a label, not a path: writing the whole path
    in every row would be noise, and the table already gives the context.
    """
    code, output = run({
        "README.md": "# Project\n\n[Contents](docs/README.md)\n",
        "docs/README.md": ("# The documentation\n\n| `tutorial/` | a single one |\n\n"
                           "[Guide](tutorial/guide.md)\n"),
        "docs/tutorial/guide.md": "# Guide\n\nThe button is pressed.\n",
    })
    assert code == 0, output


def test_path_in_prose_that_exists():
    """The target is not a document, on purpose.

    A `.md` named ONLY in prose would fail as an orphan — it is reached by clicking, not
    by backticks — and the test would pass for a different reason than the one pursued.
    """
    code, output = run({
        "README.md": "# Project\n\nThe tool sits in `bin/tool.sh`.\n",
        "bin/tool.sh": "#!/bin/bash\necho\n",
    })
    assert code == 0, output


def test_the_system_path_is_not_verified():
    code, output = run({
        "README.md": ("# Project\n\nThe tool is installed in "
                      "`/usr/local/bin/panel-mc`, and the state in "
                      "`/var/lib/workshop/`.\n"),
    })
    assert code == 0, output


def test_a_command_is_not_a_path():
    """A string with spaces, with `|`, `$`, `*` or `...` is a command, not a path."""
    code, output = run({
        "README.md": ("# Project\n\nThis is run: `go test -count=1 ./...`, "
                      "and the identifier is `p|kind|what|server`.\n"),
    })
    assert code == 0, output


def test_the_path_from_a_record_is_not_verified():
    """A record describes a day on which that path existed. It is not rewritten."""
    code, output = run({
        "README.md": "# Project\n\n[Journal](records/journal/)\n",
        "records/journal/2026-01-01-something.md": (
            "# Something\n\nBack then the tool sat in `bin/vanished.sh`.\n"),
    })
    assert code == 0, output


def test_document_outside_the_kinds():
    code, output = run({
        "README.md": "# Project\n\n[Something](docs/strayed.md)\n",
        "docs/strayed.md": "# Something\n\nIt is not in any kind of documentation.\n",
    })
    assert code == 1, output
    assert "KIND" in output, output
    assert "strayed.md" in output, output


def test_guides_is_no_longer_a_kind():
    """Since 18 September 2026 the guides sit in `how-to/`, in all the repositories."""
    code, output = run({
        "README.md": "# Project\n\n[Guide](docs/guides/guide.md)\n",
        "docs/guides/guide.md": "# How to do it\n\nThe button is pressed.\n",
    })
    assert code == 1, output
    assert "KIND" in output, output


def test_the_english_kind_is_accepted():
    code, output = run({
        "README.md": "# R\n\n[g](docs/reference/g.md)\n",
        "docs/reference/g.md": "# G\n",
    })
    assert code == 0, output
    assert "KIND" not in output, output


def test_the_documentation_readme_is_not_astray():
    """`docs/README.md` is the table of contents, not a document of a particular kind."""
    code, output = run({
        "README.md": "# Project\n\n[Contents](docs/README.md)\n",
        "docs/README.md": "# The documentation\n\n[Guide](how-to/guide.md)\n",
        "docs/how-to/guide.md": "# How to do it\n\nThe button is pressed.\n",
    })
    assert code == 0, output


TREE_DOC = """# The repository tree

```
servers/       the servers and their panel
shared/        what two or more domains need
docs/          tutorial/ how-to/ reference/ explanation/
README.md
```

Each domain holds everything it needs.
"""

TREE_LINK = (
    "# Project\n\n"
    "[The tree](docs/reference/repository-tree.md)\n")


def test_tree_declared_but_missing_from_disk():
    code, output = run({
        "README.md": TREE_LINK,
        "docs/reference/repository-tree.md": TREE_DOC,
        "servers/checks/nothing.txt": "empty\n",
    })
    assert code == 1, output
    assert "TREE" in output, output
    assert "shared" in output, output


def test_folder_on_disk_undeclared():
    code, output = run({
        "README.md": TREE_LINK,
        "docs/reference/repository-tree.md": TREE_DOC,
        "servers/checks/nothing.txt": "empty\n",
        "shared/nothing.txt": "empty\n",
        "sneaked/nothing.txt": "empty\n",
    })
    assert code == 1, output
    assert "TREE" in output, output
    assert "sneaked" in output, output


def test_tree_that_matches():
    code, output = run({
        "README.md": TREE_LINK,
        "docs/reference/repository-tree.md": TREE_DOC,
        "servers/checks/nothing.txt": "empty\n",
        "shared/nothing.txt": "empty\n",
    })
    assert code == 0, output


def test_without_a_tree_document_nothing_is_verified():
    """A repository not yet restructured has no way to know the shape. It is silent, it does not fail."""
    code, output = run({
        "README.md": "# Project\n\n[Guide](docs/how-to/guide.md)\n",
        "docs/how-to/guide.md": "# How to do it\n\nThe button is pressed.\n",
    })
    assert code == 0, output
    assert "TREE" not in output, output


def test_the_tree_is_found_under_its_name():
    code, output = run({
        "README.md": "# P\n\n[a](docs/reference/repository-tree.md)\n",
        "docs/reference/repository-tree.md": "# Tree\n\n```\nmissing/\n```\n",
    })
    assert code == 1, output
    assert "TREE" in output, output


def test_broken_link_from_a_record():
    code, output = run({
        "README.md": "# Project\n\n[Journal](records/journal/)\n",
        "records/journal/2026-01-01-something.md": (
            "# Something\n\nSee [the guide](../../docs/how-to/missing.md).\n"),
    })
    assert code == 1, output
    assert "BROKEN" in output, output
    assert "missing.md" in output, output


def test_the_long_record_does_not_fail_on_size():
    code, output = run({
        "README.md": "# Project\n\n[Journal](records/journal/)\n",
        "records/journal/2026-01-01-something.md": "# Something\n\n" + "line\n" * 500,
    })
    assert code == 0, output
    assert "TOO BIG" not in output, output


def test_a_name_that_appears_in_two_places_is_not_caught():
    """`SKILL.md` is a generic name: it cannot be known which one is meant.

    When the name at the tail appears in several places, the path written may be from
    another tree altogether — a plugin package, for instance. It stays silent.
    """
    code, output = run({
        "README.md": ("# Project\n\nRead `caveman/SKILL.md`.\n"
                      "[One](docs/reference/a.md) [Two](docs/reference/b.md)\n"),
        "docs/reference/a.md": "# One\n\nNothing.\n",
        "docs/reference/b.md": "# Two\n\nNothing.\n",
        "one/SKILL.md": "# One\n",
        "two/SKILL.md": "# Two\n",
    })
    assert code == 0, output
    assert "PATH" not in output, output


# ── the shape of the test folders ─────────────────────────────────


def test_file_in_tests_without_the_execute_bit():
    _, output = run_with_bits({
        "README.md": "# Project\n",
        "servers/tests/a.sh": "#!/bin/bash\nexit 0\n",
    })
    assert "NOT EXECUTABLE" in output, output


def test_executable_file_in_tests_is_accepted():
    code, output = run_with_bits({
        "README.md": "# Project\n",
        "servers/tests/a.sh": "#!/bin/bash\nexit 0\n",
    }, executables=["servers/tests/a.sh"])
    assert "TESTS:" not in output, output
    assert code == 0, output


def test_test_without_a_shebang():
    _, output = run_with_bits({
        "README.md": "# Project\n",
        "servers/tests/a.py": "import sys\n",
    }, executables=["servers/tests/a.py"])
    assert "SHEBANG" in output, output


def test_target_that_falls_on_the_installed_path():
    """The exact form that hid five broken tests: the tool looked for where it is
    INSTALLED, so the test can run only on the machine that has it installed."""
    code, output = run_with_bits({
        "README.md": "# Project\n",
        "servers/tests/a.sh":
            '#!/bin/bash\nCTL="${1:-/usr/local/bin/servers-command}"\n',
    }, executables=["servers/tests/a.sh"])
    assert "INSTALLED" in output, output
    assert code == 1, output


def test_target_in_the_repository_is_accepted():
    code, output = run_with_bits({
        "README.md": "# Project\n",
        "servers/tests/a.sh":
            '#!/bin/bash\nCTL="${1:-$R/servers/tools/servers-command}"\n',
    }, executables=["servers/tests/a.sh"])
    assert "TESTS:" not in output, output
    assert code == 0, output



def test_the_mention_of_usr_local_is_not_a_target():
    """⚠ The negative pair of the test above, and without it the rule would have been
    turned off the day it was put in: the first writing caught any mention, so eight
    innocent tests — fabricated trees, strings searched in the tool's text, and the
    question "is the library installed?" by which a test finds out whether it has to set
    up a mount.
    """
    code, output = run_with_bits({
        "README.md": "# Project\n",
        "servers/tests/a.sh":
            "#!/bin/bash\n"
            'if [ ! -r /usr/local/share/workshop/library.sh ]; then :; fi\n'
            'mkdir -p "$T/r/usr/local/bin"\n'
            "cat > u <<'U'\nExecStart=/usr/local/bin/check-mc\nU\n",
    }, executables=["servers/tests/a.sh"])
    assert "TESTS:" not in output, output
    assert code == 0, output


def test_tool_without_any_test_is_only_a_warning():
    code, output = run_with_bits({
        "README.md": "# Project\n",
        "servers/tools/u": "#!/bin/bash\n",
        "servers/tests/a.sh": "#!/bin/bash\n",
    }, executables=["servers/tools/u", "servers/tests/a.sh"])
    # ⚠ It shows in the output, but does NOT raise the number of failures: the verifier
    #   cannot know whether the tool's verdict is the human's. An interactive panel is
    #   judged at the keyboard and rightly stays without a test.
    assert "UNTESTED" in output, output
    assert code == 0, output


def test_a_file_named_tools_does_not_stop_the_verification():
    """`*/tools` can be a FILE, not a folder: a project's test may be called
    `tests/tools`. The verifier skips it instead of crashing with `NotADirectoryError`."""
    code, output = run_with_bits({
        "README.md": "# Project\n",
        "tests/tools": "#!/bin/bash\n",
    }, executables=["tests/tools"])
    assert "Traceback" not in output, output
    assert code == 0, output


def test_tool_named_by_a_test_is_not_reported():
    code, output = run_with_bits({
        "README.md": "# Project\n",
        "servers/tools/u": "#!/bin/bash\n",
        "servers/tests/a.sh": "#!/bin/bash\n# tests u\n",
    }, executables=["servers/tools/u", "servers/tests/a.sh"])
    assert "UNTESTED" not in output, output
    assert code == 0, output


def test_long_paragraph_is_a_failure():
    """Since 19 September 2026 a paragraph over four lines fails.

    Until then it was a warning, so as not to stop the verifiers of the projects that had
    long paragraphs and were working on branches. The last one, with 202, is at zero, so
    the exemption has nobody left to protect.
    """
    code, output = run({
        "README.md": "# P\n\none\ntwo\nthree\nfour\nfive\n",
    })
    assert "PARAGRAPH" in output, output
    assert code == 1, output


def test_four_line_paragraph_passes():
    code, output = run({"README.md": "# P\n\none\ntwo\nthree\nfour\n"})
    assert "PARAGRAPH" not in output, output


def test_the_code_block_list_and_table_are_not_paragraphs():
    code, output = run({"README.md": (
        "# P\n\n```\n1\n2\n3\n4\n5\n6\n```\n\n"
        "- a\n- b\n- c\n- d\n- e\n\n"
        "| a |\n|---|\n| 1 |\n| 2 |\n| 3 |\n| 4 |\n")})
    assert "PARAGRAPH" not in output, output


def test_a_paragraph_glued_to_a_list_is_counted_up_to_it():
    code, output = run({"README.md": "# P\n\none\ntwo\n- a\n- b\n- c\n- d\n"})
    assert "PARAGRAPH" not in output, output


def test_the_state_and_the_records_are_exempt_from_paragraphs():
    long = "one\ntwo\nthree\nfour\nfive\n"
    code, output = run({
        "README.md": "# P\n",
        "STATE.md": "# S\n\n" + long,
        "records/journal/2026-01-01-x.md": "# X\n\n" + long,
    })
    assert "PARAGRAPH" not in output, output


# ── the example ──────────────────────────────────────────────────


TO_EXAMPLE = "# P\n\n[The example](example/README.md)\n"


def test_the_example_is_checked():
    code, output = run({
        "README.md": TO_EXAMPLE,
        "example/README.md": "# Example\n\n[The plan](records/work/missing.md)\n",
    })
    assert code == 1, output
    assert "BROKEN" in output and "missing.md" in output, output


def test_the_example_records_are_checked_in_full():
    """The example's records are there to be read, not a record that grows."""
    code, output = run({
        "README.md": TO_EXAMPLE,
        "example/README.md": "# Example\n\n[The closing](records/work/closing.md)\n",
        "example/records/work/closing.md": "# The closing\n\none\ntwo\nthree\nfour\nfive\n",
    })
    assert code == 1, output
    assert "PARAGRAPH" in output, output


def test_an_orphan_in_the_example():
    code, output = run({
        "README.md": TO_EXAMPLE,
        "example/README.md": "# Example\n\nNo link.\n",
        "example/records/work/forgotten.md": "# Forgotten\n\nNobody links here.\n",
    })
    assert code == 1, output
    assert "ORPHAN" in output and "forgotten.md" in output, output


def test_a_wrong_path_in_the_example_fails():
    code, output = run({
        "README.md": TO_EXAMPLE,
        "example/README.md": "# Example\n\nThe script is `bin/greeting.sh`.\n",
        "example/greeting.sh": "#!/bin/bash\necho hello\n",
    })
    assert code == 1, output
    assert "PATH" in output and "bin/greeting.sh" in output, output


def test_a_clean_example_passes():
    """The paths in the example's prose resolve against `example/`, and
    `example/records/` is tracked: it is not the personal layer, although it has its name.

    ⚠ `.gitignore` has the pattern anchored, as in the framework. An unanchored one,
      `records/`, would ignore the example's records too.
    """
    code, output = run_with_git({
        "README.md": TO_EXAMPLE,
        "example/README.md": "# Example\n\n[The work items](records/work/INDEX.md)\n",
        "example/records/work/INDEX.md": "# The work items\n\nThe test is `tests/test-greeting.sh`.\n",
        "example/tests/test-greeting.sh": "#!/bin/bash\nexit 0\n",
    }, "/records/\n", executables=["example/tests/test-greeting.sh"])
    assert code == 0, output
    for sign in ("PERSONAL", "PATH", "KIND"):
        assert sign not in output, output


GOOD_PAIR = {
    "README.md": "# R\n\n[The rules](AGENTS.md) and [the module](CLAUDE.md).\n",
    "AGENTS.md": "# The rules\n\nA rule.\n",
    "CLAUDE.md": "@AGENTS.md\n\n## Claude Code only\n\nSomething.\n",
}


def test_the_clean_pair_passes():
    code, output = run_with_git(dict(GOOD_PAIR, **{
        "README.md": "# R\n\n[The rules](AGENTS.md), [Claude](CLAUDE.md), [Gemini](GEMINI.md).\n",
        "GEMINI.md": "@AGENTS.md\n",
    }), "")
    assert code == 0, output
    assert "MODULE" not in output, output


def test_agents_without_claude_fails():
    files = dict(GOOD_PAIR)
    del files["CLAUDE.md"]
    files["README.md"] = "# R\n\n[The rules](AGENTS.md)\n"
    code, output = run_with_git(files, "")
    assert code == 1, output
    assert "MODULE" in output and "CLAUDE.md" in output, output


def test_module_without_agents_fails():
    code, output = run_with_git({
        "README.md": "# R\n\n[The rules](AGENTS.md) and [the module](CLAUDE.md).\n",
        "AGENTS.md": "# The rules\n\nA rule.\n",
        "CLAUDE.md": "@AGENTS.md\n",
        "tool/GEMINI.md": "@AGENTS.md\n",
    }, "")
    assert code == 1, output
    assert "MODULE: " in output and "tool/GEMINI.md" in output, output


def test_module_without_import_fails():
    files = dict(GOOD_PAIR, **{"CLAUDE.md": "# The old rules\n\nThe whole text.\n"})
    code, output = run_with_git(files, "")
    assert code == 1, output
    assert "MODULE" in output and "@AGENTS.md" in output, output


def test_the_pair_in_a_subfolder_is_verified():
    files = dict(GOOD_PAIR, **{"template/AGENTS.md": "# The project\n"})
    code, output = run_with_git(files, "")
    assert code == 1, output
    assert "template/AGENTS.md" in output, output


def test_agents_too_big_fails():
    big = "# The rules\n\n" + "".join(f"- rule {i:05d} " + "x" * 60 + "\n" for i in range(330))
    code, output = run_with_git(dict(GOOD_PAIR, **{"AGENTS.md": big}), "")
    assert code == 1, output
    assert "MODULE" in output and "bytes" in output, output


def test_agents_long_in_lines_has_only_the_byte_threshold():
    """`AGENTS.md` does not enter the 400-line threshold: its limit is in bytes,
    the one at which Antigravity cuts it, and the English translation turns out
    longer in lines, not in bytes."""
    long = "# The rules\n\n" + "".join(f"- rule {i}\n" for i in range(420))
    code, output = run_with_git(dict(GOOD_PAIR, **{"AGENTS.md": long}), "")
    assert code == 0, output
    assert "TOO BIG" not in output, output


def test_agents_of_exactly_23800_bytes_fails():
    """The threshold leaves room for the header of the local file that includes it
    in Antigravity."""
    exact = "# R\n\n" + "x" * (23800 - len("# R\n\n") - 1) + "\n"
    assert len(exact.encode()) == 23800
    code, output = run_with_git(dict(GOOD_PAIR, **{"AGENTS.md": exact}), "")
    assert "MODULE" in output and "23800 bytes" in output, output


def test_claude_md_with_old_rules_unlinked_is_an_orphan():
    """A `CLAUDE.md` with the full rules, without `AGENTS.md` beside it, is a document."""
    code, output = run_with_git({
        "README.md": "# R\n",
        "CLAUDE.md": "# The old rules\n\nThe whole text.\n",
    }, "")
    assert "ORPHAN" in output and "CLAUDE.md" in output, output


def test_the_module_in_a_folder_with_diacritics_is_verified():
    code, output = run_with_git(dict(GOOD_PAIR, **{
        "café/CLAUDE.md": "@AGENTS.md\n",
    }), "")
    assert code == 1, output
    assert "café/CLAUDE.md" in output, output


def test_the_module_not_linked_from_readme_is_not_an_orphan():
    """A project started from the template links from the map to `AGENTS.md`; the
    one-line module beside it is not a document."""
    code, output = run_with_git(dict(GOOD_PAIR, **{
        "README.md": "# R\n\n[The rules](AGENTS.md)\n"}), "")
    assert code == 0, output
    assert "ORPHAN" not in output, output


def test_the_uncommitted_pair_is_verified():
    """The new project guide runs the verification before the first commit."""
    with tempfile.TemporaryDirectory() as d:
        base = pathlib.Path(d)
        write_tree(base, {"README.md": "# R\n\n[The rules](AGENTS.md)\n",
                          "AGENTS.md": "# The rules\n"})
        subprocess.run(["git", "-C", str(base), "init", "-q"], capture_output=True)
        p = subprocess.run([sys.executable, str(TOOL), str(base)],
                           capture_output=True, text=True)
    assert "MODULE" in p.stdout and "CLAUDE.md" in p.stdout, p.stdout


def test_the_copy_in_a_work_item_folder_is_not_a_module():
    code, output = run_with_git(dict(GOOD_PAIR, **{
        "records/work/open/w/copy/CLAUDE.md": "# A working copy of the rules\n",
    }), "")
    assert code == 0, output
    assert "MODULE" not in output, output


def test_the_repository_without_agents_is_not_verified():
    code, output = run_with_git({
        "README.md": "# R\n\n[The rules](CLAUDE.md)\n",
        "CLAUDE.md": "# The old rules\n\nThe whole text.\n",
    }, "")
    assert code == 0, output
    assert "MODULE:" not in output, output


def test_modules_ignored_by_git_are_not_verified():
    code, output = run_with_git(dict(GOOD_PAIR, **{
        "projects/p/CLAUDE.md": "# The project's old rules\n",
    }), "projects/\n")
    assert code == 0, output
    assert "MODULE" not in output, output


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"{len(tests)} tests passed")


if __name__ == "__main__":
    main()
