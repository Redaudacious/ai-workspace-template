#!/usr/bin/env python3
"""Which values were lost when some documents were rewritten.

    python3 bin/values.py <revision> <path>... [--removed <file>]

It is run from the repository's root. It compares the markdown documents under the given
paths, as they were at <revision> and as they are now on disk, and prints every value
that existed before and no longer appears anywhere after.

A whole rewrite, done by a model, can lose without a sign a verified number, a flag or a
path. The tool turns "no value lost" into a command that exits with 0 or with 1, that is
a task verifier.

The values of a document: the text between backticks, the lines of the code blocks, the
targets of the links and the numbers in prose with at least two digits. A value moved
into another document is not a loss: it is looked for in the whole set from after.

The file of values removed on purpose has one line per value, with a tab between the
columns: the value, the document, the reason. A line that starts with `#` is a comment.
It exits with 1 if any missing value is left unwritten there, with 2 if the revision
cannot be read.

⚠ The tool compares documents written in the same language. In a translation, the paths
and the names change after a map, so there the check is `check-docs.py` plus the review.
"""
import argparse
import pathlib
import posixpath
import re
import subprocess
import sys

# The same fence as in `check-docs.py`: a block of four backticks that contains one of
# three is not cut in half.
BLOCK = re.compile(r"^(`{3,})[^\n]*\n(.*?)^\1", re.S | re.M)
CODE = re.compile(r"`([^`\n]+)`")
LINK = re.compile(r"\]\(([^)\s]+)[^)]*\)")
NUMBER = re.compile(r"\d+(?:[.,]\d+)*")


def numbers(text):
    """The numbers with at least two digits: a "4" become "four" is not a loss."""
    return {n for n in NUMBER.findall(text) if sum(c.isdigit() for c in n) >= 2}


def target(document, t):
    """The target of a link, without its anchor, as a path from the repository's root.

    ⚠ The same target is written differently from another folder: `docs/reference/glossary.md`
    from the README is `../reference/glossary.md` from a guide. Without normalization, a
    document moved or split would lose all its links.
    """
    t = t.split("#")[0]
    if not t or re.match(r"^[a-z][a-z0-9+.-]*:", t):
        return t
    return posixpath.normpath(posixpath.join(posixpath.dirname(document), t))


def values(document, text):
    """The values of a document, as a set of (kind, value)."""
    v = set()
    for m in BLOCK.finditer(text):
        v |= {("block", r.strip()) for r in m.group(2).splitlines() if r.strip()}
    prose = BLOCK.sub("", text)
    v |= {("code", c) for c in CODE.findall(prose)}
    v |= {("target", t) for t in (target(document, x) for x in LINK.findall(prose)) if t}
    prose = LINK.sub("]", CODE.sub("", prose))
    v |= {("number", n) for n in numbers(prose)}
    return v


def git(*arguments):
    p = subprocess.run(["git", *arguments], capture_output=True, text=True)
    if p.returncode:
        print(f"values: git {' '.join(arguments)}: {p.stderr.strip()}", file=sys.stderr)
        sys.exit(2)
    return p.stdout


def before(revision, paths):
    """The documents under the paths, at the revision: (path, text)."""
    for c in git("ls-tree", "-r", "-z", "--name-only", revision, "--", *paths).split("\0"):
        if c.endswith(".md"):
            yield c, git("show", f"{revision}:{c}")


def after(paths):
    """The documents under the paths, from disk: tracked or new, without the ignored ones."""
    for c in git("ls-files", "-z", "--cached", "--others", "--exclude-standard",
                 "--", *paths).split("\0"):
        f = pathlib.Path(c)
        if c.endswith(".md") and f.is_file():
            yield c, f.read_text(encoding="utf-8")


def removed_on_purpose(file):
    """The values in the first column of the file of values removed on purpose."""
    if not file:
        return set()
    lines = pathlib.Path(file).read_text(encoding="utf-8").splitlines()
    return {r.split("\t")[0].strip() for r in lines
            if r.strip() and not r.startswith("#")}


def main():
    ap = argparse.ArgumentParser(description="the values lost in a rewrite")
    ap.add_argument("revision", help="the state from before, for instance `main`")
    ap.add_argument("paths", nargs="+", help="documents or folders of documents")
    ap.add_argument("--removed", help="the file of values removed on purpose")
    a = ap.parse_args()

    where = {}
    for document, text in before(a.revision, a.paths):
        for v in values(document, text):
            where.setdefault(v, set()).add(document)

    documents = dict(after(a.paths))
    everything = " ".join("\n".join(documents.values()).split())
    targets = {x for d, t in documents.items() for k, x in values(d, t) if k == "target"}
    nums = numbers(everything)

    def still_there(kind, x):
        # ⚠ A number is looked for as a whole number, not as a piece of text: `150` does
        # not stay in the document only because `1500` appears. The rest is looked for as
        # text, with spaces and lines squeezed into a single space, so that a command
        # moved from prose into a block, or a prompt broken differently across lines,
        # does not look lost.
        if kind == "number":
            return x in nums
        x = " ".join(x.split())
        if kind == "target":
            return x in targets or x in everything
        return x in everything

    missing = {}
    for (kind, x), docs in where.items():
        if not still_there(kind, x):
            missing.setdefault(x, set()).update(docs)

    on_purpose = removed_on_purpose(a.removed)
    unwritten = 0
    for x, docs in sorted(missing.items(), key=lambda p: (sorted(p[1]), p[0])):
        if x in on_purpose:
            continue
        unwritten += 1
        print(f"MISSING\t{x}\t{', '.join(sorted(docs))}")
    print(f"values before: {len(where)}, missing: {len(missing)}, "
          f"removed on purpose: {len(missing) - unwritten}, unwritten: {unwritten}")
    return 1 if unwritten else 0


if __name__ == "__main__":
    sys.exit(main())
