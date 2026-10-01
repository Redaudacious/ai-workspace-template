#!/usr/bin/env python3
"""Test for `example/`: it has the forms the skills ask for.

⚠ THE FORMS ARE READ FROM THE SKILLS, not from a list written here. If a skill changes
  its form, the test fails, and the example cannot fall behind without it showing. The
  old tutorial handed over a replaced flow precisely because it had nothing like this.

It is run with `python3 tests/test-example.py`.
"""
import os
import pathlib
import re
import sys


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


R = project_root()
SKILLS = R / "skills"
EXAMPLE = R / "example"
BLOCK = re.compile(r"^(`{3,})[^\n]*\n.*?^\1", re.S | re.M)
failed = []


def read(path):
    return path.read_text(encoding="utf-8")


def fail(message):
    failed.append(message)
    print(f"  ✗ {message}")


def form(text, title):
    """The first ```markdown block after the given title: the form in the skill."""
    m = re.search(r"^```markdown\n(.*?)^```", text[text.index(title):], re.S | re.M)
    return m.group(1)


def headings(text):
    """The headings of a document, without those in code blocks."""
    return [r.strip() for r in BLOCK.sub("", text).splitlines() if re.match(r"#{1,6} ", r)]


def pattern(line):
    """A line of the form, with the placeholders `<...>` as "anything"."""
    pieces = re.split(r"<[^>]*>", line.strip())
    return re.compile("^" + ".+".join(re.escape(p) for p in pieces) + "$")


def in_order(where, found, required, mandatory=None):
    """Every heading found is one of the form, in its place; the mandatory ones exist."""
    patterns = [pattern(t) for t in required]
    i = 0
    for t in found:
        while i < len(patterns) and not patterns[i].match(t):
            i += 1
        if i == len(patterns):
            fail(f'{where}: "{t}" is not in the form, or not in its place')
            return
        i += 1
    for t in (required if mandatory is None else mandatory):
        if not any(pattern(t).match(g) for g in found):
            fail(f'{where}: "{t}" is missing')


def the_folder():
    folders = sorted(d for d in (EXAMPLE / "records/work/closed").glob("*") if d.is_dir())
    if len(folders) != 1:
        fail(f"the example has {len(folders)} closed folders, not one")
        return None
    return folders[0]


def plan_header(folder):
    """The labels in the plan header and the label of each task, from `execute`."""
    text = " ".join(read(SKILLS / "execute/SKILL.md").split())
    header = re.search(r"plan header \(([^)]*)\)", text)
    label = re.search(r"in the `(\w+)` label", text)
    if not header or not label:
        fail("the `execute` skill no longer names the plan header and the task label")
        return
    plans = [f for f in folder.glob("*.md") if not f.name.endswith("-design.md")
             and f.name not in ("README.md", "request.md", "closing.md")]
    if not plans:
        fail("the example's folder has no plan")
    for plan in plans:
        text = read(plan)
        for e in re.findall(r"`([^`]+)`", header.group(1)):
            if not re.search(rf"^\*\*{re.escape(e)}:\*\*", text, re.M):
                fail(f'{plan.name}: the header has no "{e}"')
        tasks = len(re.findall(r"^### Task", text, re.M))
        who = len(re.findall(rf"^\*\*{label.group(1)}:\*\*", text, re.M))
        if not tasks or tasks != who:
            fail(f'{plan.name}: {tasks} tasks, {who} "{label.group(1)}" labels')


def state_and_handoffs():
    """The example's state file and the handoffs quoted in the story, after the form in
    `end-of-session`.

    A heading of the form under which the first line starts with "<Only" belongs to a
    section that appears only sometimes; all the others are mandatory.
    """
    f = form(read(SKILLS / "end-of-session/references/state-and-records.md"),
             "## The state file: `STATE.md`")
    lines = f.splitlines()
    required, mandatory = [], []
    for i, r in enumerate(lines):
        if re.match(r"#{1,6} ", r):
            required.append(r)
            nxt = next((x for x in lines[i + 1:] if x.strip()), "")
            if not nxt.startswith("<Only"):
                mandatory.append(r)
    in_order("STATE.md", headings(read(EXAMPLE / "STATE.md")), required, mandatory)

    handoff = f[f.index("### The handoff"):].split("\n### ")[0]
    labels = re.findall(r"^\| (\w+) \|", handoff, re.M)
    story = BLOCK.sub("", read(EXAMPLE / "README.md"))
    sections = re.split(r"^### The handoff\s*$", story, flags=re.M)[1:]
    if not sections:
        fail('the story quotes no handoff under "### The handoff"')
    for n, s in enumerate(sections, 1):
        s = re.split(r"^#{1,6} ", s, flags=re.M)[0]
        found = re.findall(r"^\| (\w+) \|", s, re.M)
        if found != labels:
            fail(f"handoff {n} in the story has the rows {found}, not {labels}")


def the_closing(folder):
    """`closing.md`, after the form in `documentation`."""
    f = form(read(SKILLS / "documentation/references/details.md"), "### `closing.md`")
    text = read(folder / "closing.md")
    in_order("closing.md", headings(text), [r for r in f.splitlines() if re.match(r"#{1,6} ", r)])
    date = next(r for r in f.splitlines() if r.startswith("Date:"))
    if not any(pattern(date).match(r) for r in text.splitlines()):
        fail('closing.md: the line "Date: … · State: … · Closed by: …" is missing')


def work_readme(folder):
    """The sections of a folder's `README.md`, after the list in `documentation`."""
    text = read(SKILLS / "documentation/references/details.md")
    listing = text[text.index("### The folder's `README.md`"):].split("\n### ")[0]
    required = ["## " + s.rstrip(".") for s in re.findall(r"^\d+\. \*\*(.+?)\*\*", listing, re.M)]
    found = [t for t in headings(read(folder / "README.md")) if t.startswith("## ")]
    in_order("the work item's README.md", found, required)


def main():
    if not EXAMPLE.is_dir():
        fail("`example/` is missing")
    else:
        folder = the_folder()
        state_and_handoffs()
        if folder:
            plan_header(folder)
            the_closing(folder)
            work_readme(folder)
    if failed:
        print(f"  ✗ {len(failed)} failed")
        return 1
    print("  ✓ the example has the forms from the skills: all tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
