---
name: end-of-session
description: Use when closing a work session - when "end of session", "closing the session", "write the state" is said, or when /end-of-session is typed.
---

# End of session

Read from git what changed, write the state, propose what is missing. Three phases, in
this order, because the values are verified before they are written.

**Only one file is rewritten: `STATE.md`.** `README.md`, `AGENTS.md`, the modules, and
`IMPACT.md` are not written automatically — what would be worth adding to them is reported.

⚠ **Nothing reaches the disk before phase 3.** Phases 1 and 2 only read.

## Phase 1 — gather the facts

### Which repositories, and in which order

From the workspace root: the environment itself, `records/` if it is a git repository,
plus every folder in `projects/` that is a git repository, with the repositories under
it — a sub-project, a domain. **Touched** means it has something uncommitted, or it has commits
in the interval below. The rest are skipped silently.

**Reading went down the tree, from the root to the file; writing climbs back up.** The
repositories touched are taken from the bottom up: the sub-project or the domain, then the
project, then the environment and the personal layer. Each thing found stops at the
first level that contains it whole, and each repository's state file gets only its own.

| the thing found is true… | where it is written |
|---|---|
| only in this sub-project or domain | its records; a candidate for its `AGENTS.md` |
| in every sub-project or domain of the project | the project's records; the project's `AGENTS.md` |
| in every project, or on the laptop | `records/` at the root; the `AGENTS.md` here |

The climbing test: does the claim stay true without the name of the sub-project or of the
project in it? Then it climbs one level. The root's state file only mentions the projects
with open work items, with the path written in prose; a work item's handoff sits in the
state file of its repository.

⚠ **`records/` is ignored by the framework's repository, so it does not appear in its
`git status`.** It is looked for on disk: `test -d records/.git`.

```bash
git -C <repository> fetch --quiet
git -C <repository> status --porcelain
git -C <repository> status -sb | head -1
```

### Which interval

Propose, in this order:

1. what is not on origin, plus what is uncommitted — `git log --oneline origin/<branch>..HEAD`;
   this interval is unambiguous and asks for no confirmation;
2. if that comes out empty, the commits after the last write of the state file, **with the
   time of each**, and **confirmation is awaited** from the human, or another starting point:

```bash
git log --format='%h %ad %s' --date=format:'%H:%M' --since="$(python3 -c 'import os,time;print(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(os.stat("STATE.md").st_mtime)))')"
```

⚠ **The second edge is approximate, by one commit.** The state file is written **before** the
closing commit of the previous session, so that commit falls inside the interval. That is why
the time of each commit is shown: the longest pause in the list is the true edge, and the human
picks it. The state file's time is read with `python3`: `date -r` is GNU-only.

### What changed, and which numbers

`git -C <repository> diff --stat <interval>`, plus `status --porcelain`. No number is
remembered: the block the repository publishes itself is run — for the environment,
`README.md`, "The landmarks, re-measured"; for a project, the table of commands in `AGENTS.md`.

## Phase 2 — a single report, nothing on disk

Six parts, in this order, because each one feeds the next:

1. **The repositories and the interval**, as confirmed, from the bottom up.
2. **The checks** — their output, with what failed brought to the front.
3. **`IMPACT.md`** — the files in the diff with no row in their repository's map.
4. **`AGENTS.md` and the modules** — the candidates, each at its level: a pitfall that
   repeated, a decision closed in the session; one that concerns a single tool goes into
   that tool's module. Proposals, never written.
5. **The records** — which entry is missing, with its proposed text and its level.
6. **The new state file** of every repository touched, whole, with the handoff and the
   report when the next session is another one — the execution of a plan, its review —,
   with the work item's row in the work index moved to "In progress", and with the
   template's divergence when it is not empty. The forms and the command are in
   [references/state-and-records.md](references/state-and-records.md).

### What leaves the state file

`STATE.md` is the only file designed to **shrink**. The old state file is read and, for each
thing open in it, the question is whether the diff closed it.

| What closed | Where it goes |
|---|---|
| a system problem repaired | `records/journal/` of the repository that keeps the machine or the tool — the entry is proposed |
| a pitfall caught | `records/pitfalls/` at its level — the entry is proposed |
| a decision of the human's, which has to hold | `records/decisions/` at its level — the entry is proposed |
| a work item whose last plan was merged into `main` | its closing — proposed, phase 3 |
| a decision worth explaining | `docs/explanation/` — **reported, not written** |
| something the agent learned that has to hold | `records/memory/` — committed together with the records |
| the rest | deleted; git keeps it anyway |

⚠ **The state file does not exceed 150 lines.** An execution's report and any long list leave
for the work item's folder, as `execution-report.md`; the state file keeps the handoff and a
link to it.

⚠ **Nothing is ever written under `docs/`.** Documentation has its own skill, which asks for
verified values and for a decision about what already exists on the subject. A closing that
wrote explanations would skip both.

## Phase 3 — write, after "yes"

The list of everything to be written — the state files, each entry with its index row and
its level, the closing of a work item — is shown whole, and the human may strike a row from
it. Then a single "yes" writes everything that remains; at the end what was not written is listed.

1. **The state files**, on disk, from the bottom up.
2. **The record entries**, each with its row added to the folder's `INDEX.md`. A record without
   an index is skipped, and that is said.
3. **The closing of a work item**, if the human said yes: `closing.md` in the folder, then, from
   the root of the repository, `python3 <workspace root>/bin/move-md.py <…>/open/<folder>
   <…>/closed/<folder>`, the row moved to "Closed" and the leftovers to "Backlog". No work item
   is closed with a leftover that has no destination.
4. **Commit and push**, in every repository touched, from the bottom up. On an `execute/*`
   branch the branch is pushed; it enters `main` only by the closing rule of the `execute`
   skill, never from here. No `Co-Authored-By`; the message says why.

⚠ **The environment's state file is ignored by git** and does not go into the commit; a
project's state file does.

⚠ **The handoff copies the plan header, it does not decide it.** The model, the effort, and
the closing are written by the planning session in the plan; the state file repeats them,
together with the folder in which the session is opened and the model for each tool from its
module, so that the human finds them without opening the plan.

## What breaks

| The situation | What is done |
|---|---|
| a check fails | it does not block the closing; the output goes into "What does not work" in the state file, and it is said openly that the closing is on a failed check |
| no repository touched | say so and stop, without writing the state file: a state file rewritten with no work behind it deletes the old state for nothing, and for the environment beyond recovery |
| the repository has no `STATE.md` | report it; do not create it |
| the repository has no `IMPACT.md` | one line, not a list with the whole diff |
| `origin` is missing | commit locally and say plainly that nothing was pushed |
| the branch is behind origin | say so **before** the commit, not after |
