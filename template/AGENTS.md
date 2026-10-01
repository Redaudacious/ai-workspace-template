# How work is done in this project

⚠ **This pair is optional:** this file and the `CLAUDE.md` beside it, which imports it.
Both load at every session start, so every line is paid for every time. A project gets
them when it has something to say that **costs if it is not known**. If none of the
questions below has an answer, delete both files.

The shared rules live in `AGENTS.md` at the workspace root and load on their own; how,
each tool's module explains. Only project-specific rules belong here.

## Commands

What is run, from where, and what does **not** work from where it might seem to.

| What | The command |
|---|---|
| build | |
| tests | |
| map verification | `../../bin/check-maps.sh .` |
| documentation verification | `python3 ../../bin/check-docs.py .` |

## Source and pull direction

The question: **is there a folder in the repository that is a copy of something on
another machine?** If so, a change made here is lost at the next sync — write that down.
If the whole repository is the source of truth, delete the section.

## Reading order

The question: **where does someone who has never seen the project start?** The entry
point, then what it calls. Three or four lines, not a full map.

## What is not touched

The question: **which closed decision would someone reopen without knowing it was
closed?** Each item with its reason; history in `records/decisions/`.

## The pitfalls that get forgotten

The question: **what has already cost time twice?**

A pitfall caught once goes into `records/pitfalls/`. Only those that have repeated
come up here — otherwise the file grows at every session and no one reads it.
