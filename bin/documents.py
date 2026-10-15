#!/usr/bin/env python3
"""Find documents that fell behind the code they describe.

The map is in the `## Documents` section of the repository's `IMPACT.md`. The
section name `## Documentele` also works. Each row links one document
to its code. The code is one or more git patterns between backticks. A row
uses `—` when the document does not describe code.

A document needs a reread when the last commit that touched its code is newer
than the last commit that touched the document or marked it as reread. The tool
keeps no state. It compares git times, so it catches any commit, at any time.
An uncommitted change counts as a change made now.

With `--complete`, the tool checks the map itself. Each document has a row.
Each row has its document on disk. Each pattern still finds a file.

Exit code: 0 nothing to do, 1 something to do, 2 the repository has no map.
"""
import pathlib
import re
import subprocess
import sys
import time

TITLES = {"## Documents", "## Documentele"}
# The reread mark in a commit message, in English and in Romanian.
MARKS = ("reread", "recitit")
CODE = re.compile(r"`([^`]+)`")
# One time for the whole run, so a document and its code that are both uncommitted tie.
NOW = int(time.time())
REMEDY = ("Fix each document with the `documentation` skill. If a document is still true, "
          "name it in the commit message, with its path and the word “reread”.")


def git(repo, *args):
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return p.stdout.strip()


def doc_map(repo):
    """{document: [patterns]} from `IMPACT.md`, or None when the section is missing."""
    f = repo / "IMPACT.md"
    if not f.is_file():
        return None
    rows, found, inside = {}, False, False
    for line in f.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            inside = line.strip() in TITLES
            found = found or inside
            continue
        if not inside or not line.startswith("|") or set(line.strip()) <= set("|-: "):
            continue
        cells = line.strip().strip("|").split("|")
        if len(cells) < 2:
            continue
        doc = CODE.findall(cells[0])
        if doc:  # the table header has no backticks
            rows[doc[0]] = CODE.findall(cells[1])
    return rows if found else None


def changed_at(repo, patterns):
    """Time of the last change to the patterns: the commit time, or now if uncommitted."""
    if git(repo, "status", "--porcelain", "--", *patterns):
        return NOW
    t = git(repo, "log", "-1", "--format=%ct", "--", *patterns)
    return int(t) if t else 0


def reread_at(repo, doc):
    """Time of the last commit whose message names the document and has a reread mark."""
    times = [git(repo, "log", "-1", "--format=%ct", "-F", "-i", "--all-match",
                 f"--grep={doc}", f"--grep={mark}") for mark in MARKS]
    return max((int(t) for t in times if t), default=0)


def stale(repo, rows):
    for doc, patterns in sorted(rows.items()):
        if not patterns:
            continue
        code = changed_at(repo, patterns)
        if code > max(changed_at(repo, [doc]), reread_at(repo, doc)):
            why = ("an uncommitted change" if code == NOW
                   else git(repo, "log", "-1", "--format=%h %cs %s", "--", *patterns)[:90])
            yield f"reread needed: {doc} — code: {why}"


def documents(repo):
    """`README.md` and `docs/**/*.md`, tracked or new, without the files git ignores."""
    output = git(repo, "ls-files", "-co", "--exclude-standard", "--", "README.md", "docs/*.md")
    return sorted(set(output.splitlines()))


def gaps(repo, rows):
    for doc in documents(repo):
        if doc not in rows:
            yield f"no row: {doc}"
    for doc, patterns in sorted(rows.items()):
        if not (repo / doc).is_file():
            yield f"document no longer exists: {doc}"
        for pattern in patterns:
            if not git(repo, "ls-files", "-co", "--exclude-standard", "--", pattern):
                yield f"code no longer exists: {doc} -> {pattern}"


def main():
    args = [a for a in sys.argv[1:] if a != "--complete"]
    complete = len(args) < len(sys.argv) - 1
    repo = pathlib.Path(args[0] if args else ".")
    rows = doc_map(repo)
    if rows is None:
        print(f"no map: {repo / 'IMPACT.md'} has no “## Documents” or “## Documentele” section")
        return 2
    problems = list(gaps(repo, rows) if complete else stale(repo, rows))
    for p in problems:
        print(p)
    if problems and not complete:
        print(REMEDY)
    print(f"documents in the map: {len(rows)}, to do: {len(problems)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
