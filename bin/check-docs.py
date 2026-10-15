#!/usr/bin/env python3
"""Verifies the documentation of a tree: links and reachability.

Lifted out of the `documentation` skill, so that it is no longer copied by hand at each
use. It exits with 1 if any hard check fails.

`records/` enters only the check of links and anchors, and the `RECORD` rule. A record is
appended to, not rewritten, so it is allowed to be long and to repeat a phrase from an
older entry — but a broken link in it costs a session, and a rewritten entry loses its
history.
"""
import collections
import os
import pathlib
import re
import subprocess
import sys

LINK = re.compile(r"\]\(([^)#]+)(#[^)]*)?\)")

# A code fence of any length, closed with exactly as many backticks as it was opened
# with. ⚠ A pattern with exactly three would cut a block of four up to its inner fence
# and leave the rest outside — that is, exactly the case it repairs.
BLOCK = re.compile(r"^(`{3,})[^\n]*\n.*?^\1", re.S | re.M)


def without_blocks(text):
    """The text without the code blocks.

    Inside a block, a link is an illustration or test data, not a claim about this
    repository. A plan containing tests once produced 13 false failures at a stroke, on
    16 September 2026.
    """
    return BLOCK.sub("", text)


# `STATE.md` is a state, not documentation: it is ignored by git, so a link to it would
# be broken on a fresh clone, and a `README.md` that links it would be wrong. The links
# FROM it are still verified — they are the next session's prompt, and a broken one
# there costs a session.
EXEMPT = {"STATE.md"}

# A path written in prose: only letters, digits, dot, hyphen and `/`. Anything with a
# space, `|`, `$`, `*`, `?`, `:`, `<` or `...` is a command, an identifier or a template,
# not a path — and a check that confuses them becomes noise and gets turned off.
PATH_IN_PROSE = re.compile(r"`([\w.\-]+(?:/[\w.\-]+)*/?)`")

# System paths are not the repository's and cannot exist in it.
SYSTEM_PREFIXES = ("/", "~", "http")

TREE_DOC = "reference/repository-tree.md"
# A tree row that starts at the left margin declares a root folder. The children's rows
# start with the drawing characters, so they fall out by themselves.
TREE_ROW = re.compile(r"^([\w.\-]+)/")

LINE_LIMIT = 400
MIN_DUPLICATE_SENTENCE = 70
PARAGRAPH_LIMIT = 4
KINDS = ("tutorial", "how-to", "reference", "explanation")

# The name under which the documentation root sits. `documentation/` and `guides/` left on
# 18 September 2026, by the user's decision: `docs/` and `how-to/` everywhere. A folder
# with the old name FAILS: the documents in it would no longer be read, and silence would
# look exactly like a clean repository.
DOC_FOLDERS = ("docs",)
OLD_NAMES = ("documentation",)

# The name of the personal layer. In the workspace it is the clone of a private
# repository and is ignored: the records and the memory do not come with the
# template. In a project it is its own record, tracked — that is why the rules below
# ask git, not the name.
PERSONAL_FOLDER = "records"

# The framework's example project: a whole work item, frozen after its merge into main.
# It is read in full, its records included: it is there to be read, not a record that
# grows, and without the check nothing in it would say it broke. The paths in its prose
# belong to the project of the example, so they are resolved against its folder too.
EXAMPLE_FOLDER = "example"


def documents(root):
    """The documents that enter the verification.

    `glob`, not `rglob`: given a workspace root, its own `docs/` is read, not those of
    the projects inside. With `rglob`, a run at the root read 69 files of which 50
    belonged to the projects — and the result "the environment is clean" was really
    about another tree.

    The third term is for the case when the root given is a `docs/` itself: without it,
    the pattern would match nothing and the verification would pass reading a single file.

    Only the personal layer at the root goes out: `example/records/` belongs to the
    example, is tracked by git and is read like any document.
    """
    found = set(root.glob("*.md"))
    for folder in DOC_FOLDERS + (EXAMPLE_FOLDER,):
        found |= set(root.glob(f"{folder}/**/*.md"))
    if root.name in DOC_FOLDERS:
        found |= set(root.rglob("*.md"))
    found = {f for f in found if f.relative_to(root).parts[0] != PERSONAL_FOLDER}
    return sorted(found - git_ignored(root, found))


def git_ignored(root, files):
    """What git ignores is not the project's documentation.

    The session files — `PROMPT-*.md` and the others in `.gitignore` — are not handed
    to anyone together with the repository, so there is no reason for them to be linked
    from `README.md` and no reason for the verification to fail on them as orphans. The
    rule is read from `git`, not written here: a pattern copied here would silently part
    from `.gitignore` at its first change.
    """
    if not files:
        return set()
    p = subprocess.run(["git", "-C", str(root), "check-ignore", "--stdin"],
                       input="\n".join(str(f) for f in files),
                       capture_output=True, text=True)
    return {pathlib.Path(line) for line in p.stdout.splitlines() if line}


def record_sources(root):
    """The files in `records/` whose LINKS are verified.

    A record is appended to, not rewritten, so it is allowed to be long and to repeat a
    phrase from an older entry: it does not enter size, repeated phrases, kinds or
    reachability. But a broken link in it costs a session, because that is where someone
    looks up what has already been hit. This widening brought out 46 broken links from a
    corpus that reported zero, on 15 September 2026.

    What the git that holds the records ignores is not a record, as in `git_ignored`: the
    copy of a project from a bench run sits beside the report, outside git. The question
    goes to the records folder, which can be a repository of its own, like the personal
    layer. A folder ignored entirely and without a repository of its own is read in full.
    """
    found = sorted((root / PERSONAL_FOLDER).rglob("*.md"))
    personal = root / PERSONAL_FOLDER
    if not found or (personal_ignored(root) and not (personal / ".git").exists()):
        return found
    p = subprocess.run(["git", "-C", str(personal), "check-ignore", "--stdin"],
                       input="\n".join(str(f.resolve()) for f in found),
                       capture_output=True, text=True)
    outside = {pathlib.Path(line) for line in p.stdout.splitlines() if line}
    return [f for f in found if f.resolve() not in outside]


HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.M)


def anchor(heading):
    """The anchor that a heading gives, in the form GitHub composes.

    Capitals go down, punctuation disappears entirely — the long dash too, and the
    backticks — and what remains is joined with hyphens. Adjacent spaces give a single
    hyphen: "10–11 September — the shell" becomes `1011-september-the-shell`, not
    `1011-september--the-shell`.
    """
    s = re.sub(r"[^\w\s-]", "", heading.strip().lower(), flags=re.U)
    return re.sub(r"\s+", "-", s.strip())


def anchors(f):
    """The anchors that a document offers.

    The code blocks go out first: a `#` at the start of a line inside a bash block is a
    comment, not a heading.
    """
    text = without_blocks(f.read_text(encoding="utf-8"))
    return {anchor(m.group(1)) for m in HEADING.finditer(text)}


def links(f):
    """The internal targets of a document, as (written, resolved path, anchor)."""
    for m in LINK.finditer(without_blocks(f.read_text(encoding="utf-8"))):
        target = m.group(1)
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        yield target, (f.parent / target).resolve(), (m.group(2) or "")[1:]


def broken(files):
    for f in files:
        for target, path, _ in links(f):
            if not path.exists():
                yield f, target


def paths_in_prose(text):
    """The strings between backticks that look like a path in the repository.

    The code blocks go out first: there a path is an illustration, not a claim about
    this repository.
    """
    for m in PATH_IN_PROSE.finditer(without_blocks(text)):
        c = m.group(1)
        # ⚠ The trailing slash does not make a name into a path. In a table that
        # describes `docs/`, the row is called `tutorial/`, and writing the whole path in
        # every row would be noise: the table already gives the context.
        if c.startswith(SYSTEM_PREFIXES) or "..." in c:
            continue
        if "/" not in c.rstrip("/"):
            continue
        yield c


def repository_names(root):
    """How many things bear each short name in the repository, files and folders.

    ⚠ THE LIST COMES FROM GIT when a repository exists. At the workspace root,
    `projects/` is ignored and holds whole other repositories: read from disk, their
    names would mix with the environment's, and a path in rules to a project's file
    would look like an environment path written wrongly. The rule is the same as the one
    in `git_ignored`: what git ignores is not this repository's.

    Without a repository — the case of a tree fabricated by a test — it is read from disk.
    """
    p = subprocess.run(["git", "-C", str(root), "ls-files"],
                       capture_output=True, text=True)
    if p.returncode == 0:
        paths = [pathlib.PurePath(line) for line in p.stdout.splitlines() if line]
    else:
        paths = [c.relative_to(root) for c in root.rglob("*")
                 if not any(x.startswith(".") for x in c.relative_to(root).parts)]
    # ⚠ The folders are gathered into a SET first. Counted once per file inside, any
    # folder with two files would look like a repeated name, and the verification would
    # go silent on all the folder paths.
    everything = set()
    for path in paths:
        everything.add(path)
        everything.update(p for p in path.parents if p.name)
    return collections.Counter(c.name for c in everything)


def existed(root, f, c):
    """The path once belonged to the repository: a commit touches it, though it is missing today."""
    for base in (root, f.parent):
        rel = os.path.relpath(base / c, root)
        if rel.startswith(".."):
            continue
        p = subprocess.run(["git", "-C", str(root), "log", "-1", "--format=%h", "--", rel],
                           capture_output=True, text=True)
        if p.stdout.strip():
            return True
    return False


def stale_paths(files, root):
    """The paths named in prose that look like a path aged by a move.

    ⚠ THE RULE IS NARROW ON PURPOSE, and it was narrowed after its first form brought out
    47 rows on the environment's documentation, **all false**. They fell into three
    classes, and none is a path of the repository: GitHub repository names written
    `owner/repository`, folder labels from a table written `tutorial/`, and real paths but
    from another tree — the files inside a plugin package. Syntactically, `bin/tool`
    and `hooks/ponytail-subagent.js` are identical, so no syntactic narrowing can tell
    them apart.

    What tells them apart is the repository itself: a path is its own if **the name at
    the tail exists somewhere in it**. Then the path written is not a fiction, but a real
    thing named in the wrong place — that is, exactly what a move of folders produces,
    which is the defect the verification exists for.

    A path to a DELETED file is caught from the git history: a commit touches it, so the
    path once belonged to the repository. The price that remains, said openly: a path to a
    name that appears in several places is not caught.
    """
    names = repository_names(root)
    example = (root / EXAMPLE_FOLDER).resolve()
    for f in files:
        in_example = example in f.resolve().parents
        bases = (root, f.parent) + ((example,) if in_example else ())
        for c in paths_in_prose(f.read_text(encoding="utf-8")):
            if any((b / c).exists() for b in bases):
                continue
            # In the example, `records/` is the example's own: a wrong path from there fails.
            if (c.startswith(f"{PERSONAL_FOLDER}/") and not in_example
                    and personal_ignored(root)):
                continue
            # A path that is missing today but has a commit in the history belonged to a
            # deleted or moved file. `IMPACT.md` is exempt: it names the old names on purpose.
            if f.name != "IMPACT.md" and existed(root, f, c):
                yield f, c
                continue
            # ⚠ Only a UNIQUE name proves anything. `SKILL.md` appears in every plugin
            # package: given twice, the path written may be from another tree altogether,
            # and the verification has no way to choose.
            if names[pathlib.PurePath(c.rstrip("/")).name] != 1:
                continue
            yield f, c


def personal_ignored(root):
    """Is the personal layer ignored at this root?

    `check-ignore` answers from patterns, not from disk, so it answers correctly on a
    fresh clone too, where the folder is missing altogether. The trailing slash is
    mandatory: the pattern `records/` matches only a folder, and `check-ignore records`
    exits with 1.
    """
    p = subprocess.run(["git", "-C", str(root), "check-ignore", "-q",
                        f"{PERSONAL_FOLDER}/"], capture_output=True)
    return p.returncode == 0


def links_into_personal(files, root):
    """The framework's links to the personal layer. FAILURES.

    On the user's machine the folder exists, so the link resolves and the broken-link
    check goes silent. On a fresh clone the folder is missing and the same link is broken
    — that is, the mistake is invisible on exactly the machine where it is made. Only
    the LINKS fail: a path written in prose is how the framework names its contract with
    the personal layer, and stays allowed.
    """
    if not personal_ignored(root):
        return
    personal = (root / PERSONAL_FOLDER).resolve()
    for f in files:
        for target, path, _ in links(f):
            try:
                path.resolve().relative_to(personal)
            except ValueError:
                continue
            yield f, target


def broken_anchors(files):
    """The links to a heading that does not exist in the target document.

    Without this check, splitting a large document silently breaks every link that
    pointed to a moved section: the path stays good, so the broken-link check passes, and
    the reader lands at the top of another document.
    """
    offered = {f.resolve(): anchors(f) for f in files}
    for f in files:
        for target, path, anc in links(f):
            if not anc or path not in offered:
                continue
            if anc not in offered[path]:
                yield f, target, anc


def orphans(files, root):
    """The documents that cannot be reached by clicking, starting from `README.md`.

    A link to a folder makes the documents inside reachable: that is how the map in a
    `README.md` looks, which links to `docs/how-to/`, not to each guide separately.
    """
    graph = collections.defaultdict(set)
    for f in files:
        for _, path, _ in links(f):
            if path.is_dir():
                graph[f.resolve()].update(c.resolve() for c in path.glob("*.md"))
            elif path.suffix == ".md":
                graph[f.resolve()].add(path)
    seen, stack = set(), [(root / "README.md").resolve()]
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        stack.extend(graph.get(cur, ()))
    # The modules are agent files, not documents: `wrong_modules` handles their
    # pairing, and a one-line `CLAUDE.md` does not belong on the map.
    return sorted(f for f in files
                  if f.name not in EXEMPT
                  and not (f.name in MODULE and (f.parent / "AGENTS.md").exists())
                  and f.resolve() not in seen)


def sentences(text):
    """The sentences of a document, with the lines of a paragraph glued back together.

    Markdown breaks a sentence over several lines, and the break falls in a different
    place in each file. A per-line check would miss exactly the repetitions that matter.
    List rows stay separate: a list of links is not a sentence, and gluing them once
    produced a "sentence" of 146 words and a false threshold.
    """
    text = without_blocks(text)
    for block in re.split(r"\n\s*\n", text):
        lines = [r.strip() for r in block.splitlines()]
        lines = [r for r in lines if r and not r.startswith(("|", "#", ">"))]
        pieces, current = [], []
        for r in lines:
            if re.match(r"^([-*+]|\d+\.)\s", r):
                if current:
                    pieces.append(" ".join(current))
                    current = []
                pieces.append(re.sub(r"^([-*+]|\d+\.)\s+", "", r))
            else:
                current.append(r)
        if current:
            pieces.append(" ".join(current))
        for b in pieces:
            for s in re.split(r"(?<=[.!?])\s+", b):
                s = s.strip()
                if s:
                    yield s


def repeated(files):
    """The long sentences that appear in two or more documents."""
    where = collections.defaultdict(set)
    for f in files:
        for s in sentences(f.read_text(encoding="utf-8")):
            if len(s) >= MIN_DUPLICATE_SENTENCE:
                where[s].add(f)
    return {s: fs for s, fs in where.items() if len(fs) > 1}


LIST_OR_BLOCK = re.compile(r"^\s*([-*+]|\d+\.)\s|^\s*[|#><]")


def long_paragraphs(files):
    """The prose paragraphs longer than `PARAGRAPH_LIMIT` lines.

    A paragraph is a run of non-empty lines, outside the code blocks, up to the first
    empty line or the first row of a list, table, heading, quote or HTML. A paragraph
    glued to a list is counted only up to the list.

    `STATE.md` is exempt: it is a state, rewritten at every closing.
    """
    for f in files:
        if f.name in EXEMPT:
            continue
        for block in re.split(r"\n\s*\n", without_blocks(f.read_text(encoding="utf-8"))):
            lines = []
            for r in block.splitlines():
                if not r.strip():
                    continue
                if LIST_OR_BLOCK.match(r):
                    break
                lines.append(r)
            if len(lines) > PARAGRAPH_LIMIT:
                yield f, len(lines), lines[0].strip()[:60]


def too_big(files):
    """The documents that have grown past the limit.

    `STATE.md` is exempt: it is a state, not documentation, and it shrinks by itself as
    what closes leaves it.

    `AGENTS.md` has its own limit, in bytes, at `wrong_modules`: it is the limit at which
    Antigravity cuts it, and holds the same for any language. The line threshold would hit
    the English text first, because English turns out longer in lines, not in bytes.
    """
    for f in files:
        if f.name in EXEMPT or f.name == "AGENTS.md":
            continue
        n = len(f.read_text(encoding="utf-8").splitlines())
        if n > LINE_LIMIT:
            yield f, n


def wrong_kinds(files, root):
    """The documents that sit under the documentation root, but in no kind.

    The `README.md` there is the table of contents and has no kind — it is itself the map
    of the others.
    """
    for f in files:
        try:
            rel = f.resolve().relative_to(root.resolve()).parts
        except ValueError:
            continue
        if not rel or rel[0] not in DOC_FOLDERS:
            continue
        if len(rel) == 2 and rel[1] == "README.md":
            continue
        if len(rel) < 3 or rel[1] not in KINDS:
            yield f, f"is not in one of the kinds {', '.join(KINDS)}"


def declared_tree(root):
    """The folder names from the first code block of the tree document.

    It returns `None` — not an empty set — when the document is missing. The distinction
    matters: without a document nothing is verified, while with an empty document the
    tree should be empty too.
    """
    for folder in DOC_FOLDERS:
        d = root / folder / TREE_DOC
        if d.exists():
            break
    else:
        return None
    blocks = re.findall(r"^`{3,}[^\n]*\n(.*?)^`{3,}",
                        d.read_text(encoding="utf-8"), flags=re.S | re.M)
    if not blocks:
        return None
    return {m.group(1) for m in
            (TREE_ROW.match(r) for r in blocks[0].splitlines()) if m}


def wrong_tree(root):
    """What is declared and missing, and what is on disk and undeclared.

    The pattern is the one in `IMPACT.md`, where each row carries a command that must
    exit with 0: the document does not describe the tree, it IS its verification.
    """
    declared = declared_tree(root)
    if declared is None:
        return
    on_disk = {d.name for d in root.iterdir()
               if d.is_dir() and not d.name.startswith(".")}
    for name in sorted(declared - on_disk):
        yield name, "declared in the document, but does not exist on disk"
    for name in sorted(on_disk - declared):
        yield name, "exists on disk, but is not declared in the document"


def name_in_two_folders(files):
    """The same file name in two kinds of documentation.

    It is legitimate — a subject may need both a reference and an explanation — so it is
    reported, not failed. The report only says where someone should look.
    """
    where = collections.defaultdict(set)
    for f in files:
        if f.parent.name in KINDS:
            where[f.name].add(f.parent.name)
    return {n: fs for n, fs in where.items() if len(fs) > 1}


# A TARGET that falls on the installed path: `CTL="${1:-/usr/local/bin/x}"` or
# `REG=/usr/local/...`. It does not match a mention in an `if`, in a `sed` or in a
# fabricated tree.
# ⚠ CAPITALS ONLY, that is, a shell variable by convention. With `[A-Za-z_]` it
#   also matched `ExecStart=/usr/local/bin/tool` from a systemd unit fabricated in a
#   heredoc — a false positive in a test that precisely probes the migration of names.
#   ponytail: a variable written in lowercase escapes. It is tightened when one appears.
INSTALLED_TARGET = re.compile(
    r'^\s*[A-Z][A-Z0-9_]*=\s*"?(\$\{[0-9]+:-)?/usr/local/')


def test_folders(root):
    """The project's test folders, at a domain or at the root.

    Folders only: a FILE with this name belongs to the project, not to the convention.
    """
    return [d for d in sorted(root.glob("*/tests")) + sorted(root.glob("tests")) if d.is_dir()]


def wrong_tests(root):
    """What breaks the shape of the test folders. FAILURES.

    Since 16 September 2026 the `test` collector discovers by the EXECUTE BIT and does not
    look at the extension. That makes discovery simple and open to any language, but it
    moves two kinds of mistake into silence, and the checks here bring them to light:

    ⚠ A test without the bit never runs, and nothing says so. When the rule was put in,
      TWELVE of 49 files lacked the bit — among them a test that was already running in
      the suite and two that had never run.

    ⚠ A test with the bit but without a shebang is taken by the kernel and given to
      `/bin/sh`, which reads Python as shell and BLOCKS reading its input. It does not
      crash — it waits. It cost two runs of ten minutes cut by `timeout`, on the day the
      rule was put in.

    ⚠ A TARGET that falls by default on the INSTALLED path makes the test able to run only
      on the machine that has the tool installed; on the rest it fails, and that failure
      looks identical to a real defect. That is how five broken tests hid inside a number
      the documentation declared normal. The target comes from `TESTS_ROOT`, with an
      optional argument that moves the installed one.

    ⚠ IT LOOKS FOR THE ASSIGNMENT, NOT THE MENTION, and the distinction is what makes the
      rule usable. A test is allowed to write `/usr/local` as much as it likes: it
      fabricates a `$T/r/usr/local/bin` tree to probe a migration, looks for the string in
      the tool's text, or asks whether the installed library exists to know whether it has
      to set up a mount. The first writing of the rule caught all of these — eight files,
      all innocent — and would have been turned off the same day.
    """
    for d in test_folders(root):
        for f in sorted(d.iterdir()):
            if not f.is_file():
                continue
            path = f.relative_to(root)
            if not os.access(f, os.X_OK):
                yield path, "NOT EXECUTABLE: it would never run, and nothing would say so"
                continue
            try:
                body = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if not body.startswith("#!"):
                yield path, "no SHEBANG: the kernel would give it to `/bin/sh`, which blocks"
                continue
            for nr, line in enumerate(body.splitlines(), 1):
                if INSTALLED_TARGET.match(line):
                    yield path, (f"line {nr}: the target falls by default on the "
                                 f"INSTALLED path — it comes from TESTS_ROOT")
                    break


MODULE = ("CLAUDE.md", "GEMINI.md", "MISTRAL.md")
MODULE_FIRST_LINE = "@AGENTS.md"
# Antigravity cuts at 24,000 bytes, measured after inclusion; the local file that
# includes it adds a header of around 110 bytes, so the limit leaves room for it.
AGENTS_LIMIT = 23800
# The cap on the rules loaded at every session, in bytes. A file that grows needs a
# decision, not just one more rule.
SIZE_CAP = {"AGENTS.md": 23707, "CLAUDE.md": 8868}


def sizes_over_cap(root):
    """`AGENTS.md` and `CLAUDE.md` at the given root, over their cap."""
    for name, cap in SIZE_CAP.items():
        f = root / name
        if f.is_file() and f.stat().st_size > cap:
            yield f, f.stat().st_size, cap


def wrong_modules(root):
    """The rule pairs: each `AGENTS.md` with `CLAUDE.md` beside it, each module
    with `AGENTS.md` beside it and with the import on the first line.

    ⚠ Without the setting configured by restore, Claude Code reads an `AGENTS.md`
      located under a `CLAUDE.md` only through the import in the module beside it.
      A module that does not import `AGENTS.md` holds rules outside the shared source.
      Antigravity cuts a rules file of 24,000 bytes without a word.

    The files are taken from `git ls-files`, including uncommitted ones: the rule
    sees the whole repository, and `template/`, but not what git ignores, like
    `projects/`. The records, `records/` and `registre/`, are skipped: a working copy in
    a work item folder is not a module. A repository without any `AGENTS.md`
    has not yet moved to modules and is not verified.
    """
    # `--others`: a new project is checked before the first commit. `-z`: a path
    # with diacritics would otherwise come out in quotes, and would be skipped without a sign.
    p = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--cached", "--others",
                        "--exclude-standard", "--",
                        "*AGENTS.md", *(f"*{m}" for m in MODULE)],
                       capture_output=True, text=True)
    tracked = {root / line for line in p.stdout.split("\0") if line}
    tracked = {f for f in tracked
               if f.name in ("AGENTS.md",) + MODULE and f.is_file()
               and f.relative_to(root).parts[0] not in (PERSONAL_FOLDER, "registre")}
    if not any(f.name == "AGENTS.md" for f in tracked):
        return
    for f in sorted(tracked):
        if f.name == "AGENTS.md":
            if f.parent / "CLAUDE.md" not in tracked:
                yield f, "has no `CLAUDE.md` beside it, with the import for Claude Code"
            n = f.stat().st_size
            if n >= AGENTS_LIMIT:
                yield f, (f"{n} bytes, the limit is {AGENTS_LIMIT}: "
                          f"Antigravity cuts it without a word")
            continue
        if f.parent / "AGENTS.md" not in tracked:
            yield f, "has no `AGENTS.md` beside it"
        first = next((r.strip() for r in f.read_text(encoding="utf-8").splitlines()
                      if r.strip()), "")
        if first != MODULE_FIRST_LINE:
            yield f, f"the first line is “{first}”, not `{MODULE_FIRST_LINE}`"


def untested_tools(root):
    """Tools that no test names. A WARNING, not a failure.

    ⚠ It stays a warning on purpose. The verifier cannot know whether the tool's verdict
      is the user's: an interactive panel is judged with the eyes, at the keyboard, and
      cannot have a test. A failure here would ask for a list of exemptions — that is,
      exactly the kind of hand-written list that the work of 16 September 2026 abolished,
      after one of the eight names in it never matched.
    """
    corpus = []
    for d in test_folders(root):
        for f in d.iterdir():
            if f.is_file():
                try:
                    corpus.append(f.read_text(encoding="utf-8", errors="replace"))
                except OSError:
                    pass
    corpus = "\n".join(corpus)
    # A FILE named `tools` — a project's `tests/tools` test — is not a domain's tools
    # folder; `iterdir()` on it crashed with `NotADirectoryError`.
    for d in sorted(root.glob("*/tools")):
        if not d.is_dir():
            continue
        for f in sorted(d.iterdir()):
            if f.is_file() and os.access(f, os.X_OK) and f.name not in corpus:
                yield f.relative_to(root)


# The records that are appended to and not rewritten, and their old names, from the
# projects older than the template. An entry is a file whose name starts with the date.
APPENDED_RECORDS = ("journal", "pitfalls", "decisions", "jurnal", "capcane", "hotarari")
DATED_ENTRY = re.compile(r"^\d{4}-\d{2}-\d{2}")
LINK_SPAN = re.compile(r"\]\([^)]*\)")


def creators(base, folders):
    """The commit that created each file in `folders`, in a single pass through history.

    The paths are relative to `base`. `--root`: without it, a machine with
    `log.showRoot=false` would not see the entries in the first commit. `--no-renames`: an
    entry moved by `move-md.py` has the move as its creating commit, with the links
    already rewritten. A path created twice, deleted in between, keeps the newest commit,
    the first one that `git log` gives.
    """
    p = subprocess.run(["git", "-C", str(base), "-c", "core.quotePath=false", "log", "--root",
                        "--relative", "--no-renames", "--diff-filter=A", "--name-only",
                        "--format=commit %H", "--", *folders],
                       capture_output=True, text=True)
    created, commit = {}, None
    for line in p.stdout.splitlines() if p.returncode == 0 else ():
        if line.startswith("commit "):
            commit = line.split()[1]
        elif line and commit:
            created.setdefault(line, commit)
    return created


def changed_records(root):
    """The record entries, in `records/` and `registre/`, whose text changed after the
    commit that created them. FAILURES.

    A record is appended to, not rewritten: a mistake in an old entry is repaired in a new
    entry. The links are ignored, because `bin/move-md.py` rewrites them legitimately when
    it moves a folder. An entry not yet committed is skipped.

    ⚠ The old text comes from a single `git cat-file --batch`, not from a `git show` per
      file: the test of 8 October 2026, on 160 entries of the personal layer, took 7.7
      seconds asking git once for each.
    """
    for base in (root / PERSONAL_FOLDER, root / "registre"):
        folders = [n for n in APPENDED_RECORDS if (base / n).is_dir()]
        if not folders:
            continue
        created = creators(base, folders)
        entries = [c for c in sorted(created)
                   if DATED_ENTRY.match(pathlib.PurePath(c).name) and (base / c).is_file()]
        if not entries:
            continue
        prefix = subprocess.run(["git", "-C", str(base), "rev-parse", "--show-prefix"],
                                capture_output=True, text=True).stdout.strip()
        request = "".join(f"{created[c]}:{prefix}{c}\n" for c in entries)
        batch = subprocess.run(["git", "-C", str(base), "cat-file", "--batch"],
                               input=request.encode("utf-8"), capture_output=True).stdout
        pos = 0
        for c in entries:
            end = batch.index(b"\n", pos)
            header = batch[pos:end].split()
            if len(header) < 3:  # "<request> missing": the commit does not have the path
                pos = end + 1
                continue
            size = int(header[2])
            old = batch[end + 1:end + 1 + size].decode("utf-8", errors="replace")
            pos = end + 1 + size + 1
            new = (base / c).read_text(encoding="utf-8", errors="replace")
            if LINK_SPAN.sub("]()", old) != LINK_SPAN.sub("]()", new):
                yield (base / c).relative_to(root)


# Coverage of the criteria: the number of each criterion in the spec, the head of each plan.
CRITERIA_SECTION = re.compile(r"^## How to see that it worked[^\n]*\n(.*?)(?=^## |\Z)",
                              re.M | re.S)
# From this day, a spec with criteria also needs the documents section. Earlier folders do not fail.
DOCUMENTS_FROM = "2026-10-15"
DOCUMENTS_SECTION = re.compile(r"^## Documents\s*$", re.M)
CRITERION = re.compile(r"^\s*[-*]\s+\*\*(C\d+)\*\*", re.M)
BRANCH = re.compile(r"^\*\*Branch:\*\*", re.M)
CRITERIA_HEAD = re.compile(r"^\*\*Criteria:\*\*[ \t]*(.*)$", re.M)


def criteria(folder):
    """The spec's criteria from a work item folder, and the failures of their coverage.

    It returns (the criteria from the spec, the failures). A spec without numbered
    criteria gives two empty lists: work items written before the form do not fail.

    A plan is a file with `**Branch:**` at the start of a line, outside the code blocks;
    its head names the criteria it closes, or `none`, with the reason. The code blocks go
    out first: a plan that fabricates other plans in its tests does not close their
    criteria.
    """
    spec = folder / f"{folder.name}-design.md"
    if not spec.is_file():
        return [], [f"SPEC: `{spec.name}` is missing from {folder}"]
    spec_text = without_blocks(spec.read_text(encoding="utf-8"))
    m = CRITERIA_SECTION.search(spec_text)
    from_spec = list(dict.fromkeys(CRITERION.findall(m.group(1)))) if m else []
    if not from_spec:
        return [], []
    failures, covered = [], set()
    if folder.name[:10] >= DOCUMENTS_FROM and not DOCUMENTS_SECTION.search(spec_text):
        failures.append(f"SPEC: {spec.name} has no `## Documents` section")
    for plan in sorted(folder.glob("*.md")):
        text = without_blocks(plan.read_text(encoding="utf-8"))
        if plan == spec or not BRANCH.search(text):
            continue
        head = CRITERIA_HEAD.search(text)
        if not head:
            failures.append(f"PLAN: {plan.name} has no `**Criteria:**` row under `**Branch:**`")
            continue
        named = ([] if head.group(1).startswith("none")
                 else re.findall(r"\bC\d+\b", head.group(1)))
        for c in named:
            if c not in from_spec:
                failures.append(f"FOREIGN: {plan.name} names {c}, which the spec does not have")
        covered.update(named)
    for c in from_spec:
        if c not in covered:
            failures.append(f"UNCOVERED: {c} is not in the head of any plan")
    return from_spec, failures


def main_criteria(folder):
    """`--criteria <folder>`, run by the `plans` and `orchestration` skills, not by the usual
    verification: a planning session is allowed to write only some of the plans."""
    from_spec, failures = criteria(folder)
    for c in failures:
        print(c)
    if not from_spec and not failures:
        print(f"skipped: the spec in {folder} has no numbered criteria")
        return 0
    print(f"criteria: {len(from_spec)}, failures: {len(failures)}")
    return 1 if failures else 0


def main():
    if sys.argv[1:2] == ["--criteria"]:
        return main_criteria(pathlib.Path(sys.argv[2]))
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    files = documents(root)
    # Links are verified on the whole corpus, so that a target in `docs/` named from a
    # record is found. The rest of the checks stay on `files`.
    everything = files + record_sources(root)
    failures = 0

    for f, target in broken(everything):
        print(f"BROKEN: {f} -> {target}")
        failures += 1

    for f, target in links_into_personal(files, root):
        print(f"PERSONAL: {f} -> {target} — the personal layer does not come with the clone")
        failures += 1

    for f, c in stale_paths(files, root):
        print(f"PATH: {f} — `{c}` does not exist")
        failures += 1

    for f, reason in wrong_kinds(files, root):
        print(f"KIND: {f} — {reason}")
        failures += 1

    for name in OLD_NAMES:
        if (root / name).is_dir():
            print(f"NAME: `{name}/` — the documentation sits in `docs/`, the guides in `docs/how-to/`")
            failures += 1

    for name, reason in wrong_tree(root):
        print(f"TREE: `{name}/` — {reason}")
        failures += 1

    for f, reason in wrong_tests(root):
        print(f"TESTS: {f} — {reason}")
        failures += 1

    for f, reason in wrong_modules(root):
        print(f"MODULE: {f.relative_to(root)} — {reason}")
        failures += 1

    for f, n, cap in sizes_over_cap(root):
        print(f"SIZE: {f.name} — {n} bytes, the cap is {cap}")
        failures += 1

    for f in changed_records(root):
        print(f"RECORD: {f} changed after its commit")
        failures += 1

    # ⚠ It does NOT raise `failures`: it is a warning. See `untested_tools`.
    for f in untested_tools(root):
        print(f"UNTESTED: {f} — no test names it")

    # ⚠ A failure since 19 September 2026, at the end of the work item that brought the
    #   last repository with long paragraphs from 202 to zero. Until then it was a
    #   warning, so as not to stop the verifiers of the projects that were working on
    #   branches.
    for f, n, start in long_paragraphs(files):
        print(f"PARAGRAPH: {f} — {n} lines, the limit is {PARAGRAPH_LIMIT}: “{start}…”")
        failures += 1

    if (root / "README.md").exists():
        for f in orphans(files, root):
            print(f"ORPHAN: {f} — it cannot be reached by clicking from README.md")
            failures += 1
    else:
        print(f"WARNING: {root}/README.md is missing, reachability is not checked")

    for f, target, anc in broken_anchors(everything):
        print(f"ANCHOR: {f} -> {target}#{anc} — the heading does not exist there")
        failures += 1

    for s, fs in sorted(repeated(files).items()):
        print(f"REPEATED in {len(fs)} documents: {s[:80]}")
        for f in sorted(fs):
            print(f"         {f}")
        failures += 1

    for f, n in too_big(files):
        print(f"TOO BIG: {f} — {n} lines, the limit is {LINE_LIMIT}")
        failures += 1

    for name, folders in sorted(name_in_two_folders(files).items()):
        print(f"report: `{name}` appears in {', '.join(sorted(folders))}"
              f" — check that it is not repeated")

    print(f"documents read: {len(files)}, failures: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
