---
name: end-of-session
description: Use when closing a work session, when the user says "end of session", "close the session", or "write the state".
---

# End of session

Read from git what changed, write the state, and propose what is missing. Work in three phases, in this order, because you check the values before you write them.

**Rewrite `STATE.md`.** Write the documents that `bin/documents.py` lists, and only with the `documentation` skill. Do not write `AGENTS.md`, the modules, or `IMPACT.md` automatically. Report what they lack.

⚠ **Nothing reaches the disk before phase 3.** Phases 1 and 2 only read.

## Phase 1 — gather the facts

### Which repositories, and in which order

Start from the workspace root. Take the environment itself. Take `records/` if it is a git repository. Take every folder in `projects/`, with a git repository or without one. Also take the repositories under those folders, such as a game or a domain. **Touched** means the repository holds uncommitted changes, or commits in the interval below. A folder without git is touched when `find <folder> -newer <folder>/STATE.md` finds a file. Skip the rest silently.

**Reading went down the tree, from the root to the file. Writing climbs back up.** Take the touched repositories from the bottom up. Start with the game or domain, then the project, then the environment and the personal layer. Put each finding at the first level that contains it whole. Each state file gets only its own findings.

| The finding is true… | Where to write it |
|---|---|
| only in this game or domain | its records, and a candidate for its `AGENTS.md` |
| in any game or domain of the project | the project's records, and the project's `AGENTS.md` |
| in any project, or in the environment itself | `records/` at the root, and `AGENTS.md` at the root |

The climbing test: does the claim stay true without the name of the game or the project in it? Then climb one level. The root state file names the projects with open work items, by path in prose. The handoff of a work item sits in the state file of its own repository.

⚠ **The framework repository ignores `records/`. It does not appear in the framework's `git status`.** Test whether it exists on disk: `test -d records/.git`.

```bash
git -C <repository> fetch --quiet
git -C <repository> status --porcelain
git -C <repository> status -sb | head -1
```

### Which interval

Propose the interval in this order:

1. Take the commits that are not on origin, plus the uncommitted changes: `git log --oneline origin/<branch>..HEAD`. This interval is unambiguous. It needs no approval.
2. If that list is empty, take the commits after the last write of the state file, **with the time of each commit**. **Wait for the human to approve**, or to give another starting point:

```bash
git log --format='%h %ad %s' --date=format:'%H:%M' --since="$(python3 -c 'import os,time;print(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(os.stat("STATE.md").st_mtime)))')"
```

⚠ **The second edge is approximate, by one commit.** You write the state file **before** the closing commit of the previous session. That commit therefore falls inside the interval. For this reason, the list shows the time of each commit. The longest pause in the list is the true edge, and the human chooses it. Read the state file time with `python3`. The `date -r` option works only with GNU.

### What changed, and which numbers

Run `git -C <repository> diff --stat <interval>`, and `git -C <repository> status --porcelain`. Do not reuse any number from memory. Also run `python3 <workspace root>/bin/documents.py <repository>`. Run the block that the repository publishes itself. For the environment, that block is in `README.md`, under "The landmarks, re-measured". For a project, it is the table of commands in `AGENTS.md`.

## Phase 2 — a single report, nothing on disk

Write the report in six parts, in this order. Each part feeds the next one.

1. **The repositories and the interval**, as approved, from the bottom up.
2. **The checks.** Give their output, with the failures first.
3. **`IMPACT.md` and the documents.** List the files in the diff that have no row in the map of their repository. List also the documents that `documents.py` reports, each with its repair or with the mark "reread".
4. **`AGENTS.md` and the modules.** List the candidates, each at its own level. A candidate can be a pitfall that repeated, or a decision closed in the session. A candidate about one tool goes into the module of that tool. Propose candidates. Never write them.
5. **The records.** Name each missing entry, with its proposed text and its level.
6. **The new state file** of every repository touched, in full. Include the handoff and the report when the next session is another one, such as `plans` or `orchestration`. Move the work item's row in the work index to "In progress". Include the template's divergence when it is not empty. The formats are in [references/state-and-records.md](references/state-and-records.md). **Read the reference before you write the state file.** The handoff needs a prompt and a model for each tool.

### What leaves the state file

`STATE.md` is the only file designed to **shrink**. Read the old state file. For each open item in it, check whether the diff closed it.

| What closed | Where it goes |
|---|---|
| a system problem repaired | `records/journal/` of the repository that keeps the machine or the tool. Propose the entry. |
| a pitfall caught | `records/pitfalls/` at its level. Propose the entry. |
| a decision of the human, which must hold | `records/decisions/` at its level. Propose the entry. |
| a work item whose last plan merged into `main` | its closing. Propose it in phase 3. |
| a decision worth explaining | `docs/explanation/`. **Report it. Do not write it.** |
| something the agent learned, which must hold | `records/memory/`. Commit it with the records. |
| the rest | Delete it. Git keeps it anyway. |

⚠ **The state file does not exceed 150 lines.** Move the report of an execution, and any long list, to the work item's folder. Name the file `report-<plan name>.md`, as the `execute` skill says. In the state file, keep the handoff and a link to the report.

⚠ **Write under `docs/` and in `README.md` only with the `documentation` skill**, and only the documents that `documents.py` lists. That skill requires verified values, and a decision about what already exists on the topic.

## Phase 3 — write, after "yes"

Show the complete list of everything to be written. Each state file and record entry goes on it, with its index row and its level. A work item closing goes on it too. The human can strike a row from the list. Then one "yes" writes everything that remains. At the end, list what was not written.

1. **The state files**, on disk, from the bottom up. Git ignores the environment's state file. A project's state file goes into the commit.
2. **The record entries**, each with its row added to the folder's `INDEX.md`. Skip a record folder that has no index. Say so.
3. **Usage evidence**, for a chat that worked on a work item with a folder, in a private repository. Run `python3 <workspace root>/bin/usage.py --evidence <session code>`. The method is in the same reference.
4. **The closing of a work item**, if the human said yes. Write `closing.md` in the folder, with the total from `python3 <workspace root>/bin/usage.py --work <folder>`. Then, from the root of the repository, run `python3 <workspace root>/bin/move-md.py <…>/open/<folder> <…>/closed/<folder>`. Move the row to "Closed", and the leftovers to "Backlog". Do not close a work item with a leftover that has no destination.
5. **Commit and push** in every repository touched, from the bottom up. On an `execute/*` branch, push the branch. The orchestrator merges it into `main` after the verdict, never the closing. Do not write `Co-Authored-By`. The commit message says why.
6. **The last message to the human**, in the chat, after any session. State what the human must do. Then give the next prompt, with the folder and the model of each tool above it. The form is in the same reference.

⚠ **The handoff copies, it does not decide.** The `spec` and `plans` roles use the large tier at `high` effort. The `orchestration` role uses the large tier at `medium` effort. A manual execution takes the header of the plan. Repeat them in the state file. Write the folder where the session opens, and the model of each tool, from its module. The human then finds them without opening the plan.

## What breaks

| The situation | What to do |
|---|---|
| a check fails | Do not block the closing. Write the output under "What does not work" in the state file. Say openly that you close on a failed check. |
| no repository touched | Say so, and stop. Do not write the state file. A state file rewritten with no work behind it deletes the old state for nothing. In the environment, that loss is permanent. |
| the repository has no `STATE.md` | Report it. Do not create it. |
| the repository has no `IMPACT.md` | Write one line, not a list of the whole diff. |
| `origin` is missing | Commit locally. Say plainly that nothing reached origin. |
| the branch is behind origin | Say so **before** the commit, not after. |
| a listed document stays undone | Put a leftover in the work queue, with its path, and a row in "What does not work". |
| the project folder is not a git repository | Write the state file on disk. Skip the commit and the push. Tell the user that the work is not saved in git. |
