#!/usr/bin/env python3
"""Moves a file or a folder in the repository and rewrites the markdown links.

`git mv` moves the files, but knows nothing about links. A plan moved two folders
down loses every relative path, and the index that pointed to it points at nothing.
The tool moves and recalculates, across the whole repository:

- the links FROM the moved files, because they now leave from another place;
- the links TO the moved files, because the target has moved.

Anchors stay. Code blocks are not touched: there a link is an illustration.
A link that was already broken stays as it was; repairing it is not the move's job.

Only the files in git are read. The environment's `STATE.md` is ignored, so it is not
rewritten here; `end-of-session` rewrites it anyway, at closing.

Usage: python3 bin/move-md.py <source> <destination>
Exits with 0 after the move. Exits with 2, without touching anything, if the source is
missing, is not in git, or the destination already exists.
"""
import os
import pathlib
import re
import subprocess
import sys

# The same form of link as in `check-docs.py`, with the target in a group of its own.
LINK = re.compile(r"(\]\()([^)#]+)((?:#[^)]*)?\))")
# A code fence of any length, up to the fence that closes it.
BLOCK = re.compile(r"^(`{3,})[^\n]*\n.*?^\1[^\n]*$", re.S | re.M)
EXTERNAL = ("http://", "https://", "mailto:", "/", "~")


def refuse(message):
    print(f"refused: {message}", file=sys.stderr)
    sys.exit(2)


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args],
                          capture_output=True, text=True, check=True).stdout


def rewrite(text, path, new, moved):
    """The text of the file `path`, with the links recalculated for the place `new`.

    `moved(p)` gives the new place of a path relative to the root, or the path itself.
    Returns the new text and how many links changed.
    """
    changed = 0

    def replace(m):
        nonlocal changed
        target = m.group(2)
        if target.startswith(EXTERNAL):
            return m.group(0)
        old = pathlib.Path(os.path.normpath(os.path.join(path.parent, target)))
        if old.parts and old.parts[0] == "..":
            return m.group(0)
        if new == path and moved(old) == old:
            return m.group(0)
        if not (ROOT / old).exists():
            return m.group(0)
        relative = os.path.relpath(moved(old), new.parent)
        if target.endswith("/") and not relative.endswith("/"):
            relative += "/"
        if relative == target:
            return m.group(0)
        changed += 1
        return m.group(1) + relative + m.group(3)

    pieces, position = [], 0
    for block in BLOCK.finditer(text):
        pieces.append(LINK.sub(replace, text[position:block.start()]))
        pieces.append(block.group(0))
        position = block.end()
    pieces.append(LINK.sub(replace, text[position:]))
    return "".join(pieces), changed


def main():
    global ROOT
    if len(sys.argv) != 3:
        refuse("usage: move-md.py <source> <destination>")
    source = pathlib.Path(sys.argv[1]).absolute()
    destination = pathlib.Path(sys.argv[2]).absolute()
    if not source.exists():
        refuse(f"{sys.argv[1]} does not exist")
    if destination.exists():
        refuse(f"{sys.argv[2]} already exists")
    start = source if source.is_dir() else source.parent
    ROOT = pathlib.Path(git(start, "rev-parse", "--show-toplevel").strip())
    src = pathlib.Path(os.path.relpath(source, ROOT))
    dst = pathlib.Path(os.path.relpath(destination, ROOT))
    tracked = [pathlib.Path(p) for p in git(ROOT, "ls-files", "-z").split("\0") if p]
    if not any(p == src or src in p.parents for p in tracked):
        refuse(f"{sys.argv[1]} is not in git")

    def moved(p):
        if p == src:
            return dst
        if src in p.parents:
            return dst / p.relative_to(src)
        return p

    new_texts, total = {}, 0
    for path in tracked:
        if path.suffix != ".md":
            continue
        text = (ROOT / path).read_text(encoding="utf-8")
        new, changed = rewrite(text, path, moved(path), moved)
        if changed:
            new_texts[moved(path)] = new
            total += changed

    (ROOT / dst).parent.mkdir(parents=True, exist_ok=True)
    git(ROOT, "mv", str(src), str(dst))
    for path, text in new_texts.items():
        (ROOT / path).write_text(text, encoding="utf-8")
    print(f"moved: {src} -> {dst}; links rewritten: {total} in {len(new_texts)} files")
    return 0


ROOT = None

if __name__ == "__main__":
    sys.exit(main())
