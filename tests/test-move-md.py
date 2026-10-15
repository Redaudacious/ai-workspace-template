#!/usr/bin/env python3
"""Test for `bin/move-md.py`.

No testing framework: each case makes a git repository in a temporary folder, calls the
tool as a separate process and reads the files afterwards.
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


TOOL = project_root() / "bin" / "move-md.py"
failed = 0


def check(condition, message):
    global failed
    if condition:
        print(f"  ✓ {message}")
    else:
        failed += 1
        print(f"  ✗ {message}")


def repository(base, files):
    """Writes the files and commits them, so that the tool finds them in git."""
    for path, content in files.items():
        f = base / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding="utf-8")
    for command in (["init", "-q", "-b", "main"], ["add", "-A"],
                    ["-c", "user.name=test", "-c", "user.email=test@local",
                     "commit", "-q", "-m", "tree"]):
        subprocess.run(["git", "-C", str(base), *command], check=True)


def move(base, source, destination):
    p = subprocess.run([sys.executable, str(TOOL), source, destination],
                       cwd=base, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def read(base, path):
    """The content of a file, or empty if it is missing: a missed move is a failure, not a crash."""
    f = base / path
    return f.read_text(encoding="utf-8") if f.exists() else ""


PLAN = """# The plan

**Spec:** [the spec](../specs/s.md)

The guide: [guide](../../docs/how-to/g.md).

```
[example](../specs/s.md)
```

[external](https://example.org/x.md) and [broken](../does-not-exist.md).
"""

TREE = {
    "README.md": "# R\n\n[plan](records/plans/p.md) and [spec](records/specs/s.md#title)\n",
    "docs/how-to/g.md": "# G\n\nSee [the plan](../../records/plans/p.md).\n",
    "docs/other.md": "# A\n\n[guide](how-to/g.md)\n",
    "records/plans/INDEX.md": "| [p](p.md) | [spec](../specs/s.md) |\n",
    "records/plans/p.md": PLAN,
    "records/specs/s.md": "# S\n\n## Title\n\n[the plan](../plans/p.md)\n",
}


def case_files_moved_one_by_one():
    with tempfile.TemporaryDirectory() as d:
        base = pathlib.Path(d)
        repository(base, TREE)
        other = read(base, "docs/other.md")
        code1, out1 = move(base, "records/specs/s.md",
                           "records/work/closed/d/s-design.md")
        code2, out2 = move(base, "records/plans/p.md",
                           "records/work/closed/d/p.md")
        check(code1 == 0 and code2 == 0, f"both moves exit with 0 ({code1}, {code2})")
        check(not (base / "records/plans/p.md").exists()
              and (base / "records/work/closed/d/p.md").exists(),
              "the plan is at the new place, not at the old one")
        tracked = subprocess.run(["git", "-C", str(base), "ls-files"],
                                 capture_output=True, text=True).stdout
        check("records/work/closed/d/p.md" in tracked,
              "the move is done through git, not only on disk")
        p = read(base, "records/work/closed/d/p.md")
        check("[the spec](s-design.md)" in p, "the plan → spec link becomes a neighbor")
        check("[guide](../../../../docs/how-to/g.md)" in p,
              "the link to docs/ is recalculated for the new depth")
        check("[example](../specs/s.md)" in p, "the code block stays untouched")
        check("[external](https://example.org/x.md)" in p, "the external link stays")
        check("[broken](../does-not-exist.md)" in p, "the already broken link stays as it was")
        s = read(base, "records/work/closed/d/s-design.md")
        check("[the plan](p.md)" in s, "the spec → plan link becomes a neighbor")
        r = read(base, "README.md")
        check("[plan](records/work/closed/d/p.md)" in r,
              "the link from README to the plan follows the move")
        check("[spec](records/work/closed/d/s-design.md#title)" in r,
              "the anchor stays after the move")
        g = read(base, "docs/how-to/g.md")
        check("[the plan](../../records/work/closed/d/p.md)" in g,
              "the link from a guide to the plan follows the move")
        i = read(base, "records/plans/INDEX.md")
        check("[p](../work/closed/d/p.md)" in i
              and "[spec](../work/closed/d/s-design.md)" in i,
              "the old index points to the new places")
        check(read(base, "docs/other.md") == other,
              "a document with no links to what was moved stays identical")


def case_folder_moved():
    with tempfile.TemporaryDirectory() as d:
        base = pathlib.Path(d)
        readme = "# X\n\n[plan](x.md)\n\n[guide](../../../../docs/how-to/g.md)\n"
        repository(base, {
            "docs/how-to/g.md": "# G\n",
            "records/work/INDEX.md": "[x](open/x/README.md)\n",
            "records/work/open/x/README.md": readme,
            "records/work/open/x/x.md": "# Plan X\n\n[back](README.md)\n",
        })
        code, out = move(base, "records/work/open/x", "records/work/closed/x")
        check(code == 0, f"moving a folder exits with 0 ({code})")
        check(read(base, "records/work/closed/x/README.md") == readme,
              "in the folder moved at the same depth nothing changes")
        check(read(base, "records/work/INDEX.md") == "[x](closed/x/README.md)\n",
              "the index points to the moved folder")


def case_refusals():
    with tempfile.TemporaryDirectory() as d:
        base = pathlib.Path(d)
        repository(base, TREE)
        # ⚠ The code alone is not enough: `python3` on a file that is missing also exits
        #   with 2, so the refusals would pass even without the tool. Its message is
        #   asked for too.
        code, out = move(base, "records/plans/p.md", "records/specs/s.md")
        check(code == 2 and "refused:" in out,
              f"the destination that already exists is refused with 2 ({code})")
        check((base / "records/plans/p.md").exists(), "after the refusal, the source stays")
        (base / "new.md").write_text("# new\n", encoding="utf-8")
        code, out = move(base, "new.md", "other/new.md")
        check(code == 2 and "refused:" in out,
              f"the source that is not in git is refused with 2 ({code})")
        code, out = move(base, "missing.md", "other/missing.md")
        check(code == 2 and "refused:" in out,
              f"the source that is missing is refused with 2 ({code})")


if __name__ == "__main__":
    case_files_moved_one_by_one()
    case_folder_moved()
    case_refusals()
    print(f"failed: {failed}")
    sys.exit(1 if failed else 0)
