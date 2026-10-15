# The first work item, through the three sessions

The lesson takes a small work item from request to closing, through the three sessions: the spec, the plans and the orchestration. The spec is the document that decides what to do and how. At the end, there is a script that works, a branch merged into `main`, and a closed work item folder. The folder holds the spec, the plan and the closing, with every decision written in it.

The executor's report and the orchestrator's verdict also stay in the folder.

The work item is deliberately small: a script of five lines. Attention stays on the flow, not on the code. Each new session starts with the rules and the skills loaded, so each session costs something, even for an exercise.

The same path, already completed, is in the example. The example is a small project taken from request to `main` and frozen: [example/README.md](../../example/README.md). Each step below links to the file that the example produces, so that your result can be compared with a good one.

The flow diagram is in the [README](../../README.md#how-it-works).

This lesson assumes that you restored the environment with the steps in [Quick start](../../README.md#quick-start). `./bin/check-lock.sh` exits with 0. The new terms are in the [glossary](../reference/glossary.md).

⚠ **Open every session in `projects/exercise`, not at the root.** Only then does `AGENTS.md` load at startup. `AGENTS.md` is the file with the common rules. Every session loads it, in every tool.

The framework rules also load from the `AGENTS.md` at the root. The framework is the repository with the rules, skills and tools common to all projects. The root is a parent folder, so the rules load from there too.

## Step 0 — the exercise project, copied from the template

The project starts from the template: the `template/` folder, from which a new project starts. Run these commands from the root of the workspace, the folder into which you cloned the environment's repository:

```bash
mkdir -p projects/exercise && cp -r template/. projects/exercise/
cd projects/exercise && git init -q -b main && git add -A && git commit -q -m "The exercise starts from the template"
python3 ../../bin/check-docs.py . | tail -1
```

`failures: 0` must appear. The project now has `records/work/INDEX.md`, which is empty. It is the work index: one row for each work item, with its state. The work item will appear there.

## Step 1 — the spec session writes the spec

Open a new session in `projects/exercise`, on the large tier, with the effort `high`. The effort sets how much thinking time the model gets. In Claude Code, the large tier is Opus: in the application's menu, choose the Opus model and the effort `high`. Type:

```
I want a script greeting.sh that takes a name and prints "hello, <name>", plus a test that checks it. The requirements are fixed. Write the spec of the work item in its folder, in records/work/, and hand the plans over to the next session. Closing: the orchestrator. No local worker: the exercise must work on a machine without one too.
```

`Using superpowers:brainstorming` must appear. At the end, `Using end-of-session` must appear. The end-of-session step shows what it is about to write, and asks for a "yes".

Check in a terminal, in `projects/exercise`:

```bash
ls records/work/open/*/
sed -n '/^### The handoff/,/^### Read first/p' STATE.md
```

A folder with the spec, `<folder>-design.md`, must appear. In `STATE.md`, the state file, a handoff table must appear. The state file holds the project's state and what comes next. It is rewritten at the end of each session.

The handoff table is the note in `STATE.md` for the next session, the plans session. It names the folder, the tier, the effort and the prompt to paste.

The session's last message also gives the prompt, the folder and the tier of the next session. The tier does not change here: this session is closing.

In the example, the same step left [the request](../../example/records/work/closed/2026-09-22-greeting/request.md), which is the prompt above. It also left [the spec](../../example/records/work/closed/2026-09-22-greeting/2026-09-22-greeting-design.md).

## Step 2 — the plans session writes the plan

Open a new session, again in `projects/exercise`, again on the large tier (in Claude Code, Opus), with the effort `high`. Paste the prompt from the handoff.

`Using superpowers:writing-plans` must appear. At the end, `Using end-of-session` must appear. The session does not reopen what the spec settled. It does not test the plan either: the code in the plan runs only once, in the executor. The session writes the plan, with its header, and the work item's `README.md`. The plan is a list of tasks. Each task has its verifier, and an agent executes the tasks.

Check:

```bash
ls records/work/open/*/
sed -n '1,/^## /p' records/work/open/*/2026-*-plan*.md 2>/dev/null || head -12 records/work/open/*/*.md
```

Next to the spec, `README.md` and the plan must appear. The first lines of a plan are its header. The header names the tier and the party that merges the work. In the header, the lines `Execution`, `Closing: the orchestrator` and `Branch` must appear. In `STATE.md`, the handoff to the orchestration now appears.

In the example: the [plan](../../example/records/work/closed/2026-09-22-greeting/2026-09-22-greeting.md) and the [work item's README](../../example/records/work/closed/2026-09-22-greeting/README.md).

## Step 3 — the orchestration session carries the plan into `main`

Open a new session in `projects/exercise`, on the large tier (in Claude Code, Opus), with the effort `medium`. Paste the prompt from the handoff:

```
Orchestrate the work item records/work/open/<folder> with the orchestration skill.
```

`Using orchestration` must appear. Then the `executor` agent starts. It is a framework agent that works on the branch in the plan's header. The executor leaves one commit for each task, and one report. The orchestrator writes no code. It verifies.

The orchestrator runs the plan's check again, because an agent's report is not evidence. It writes the verdict in the folder. If everything matches, it merges the branch into `main` with `git merge --ff-only`. At `end-of-session`, it proposes closing the work item. Answer "yes".

Check:

```bash
git branch --show-current
git log --oneline -3
ls records/work/closed/*/
sed -n '/^## Closed/,$p' records/work/INDEX.md
```

`main` must appear. The history must show one commit for each task. The work item's folder must move into `closed/`. The folder then holds `report-…`, `verdict-…`, `orchestration.md` and a new `closing.md`. A row appears under "Closed", with the state `finished` and zero leftovers. A leftover is a task of a work item that is not done.

In the example, the orchestration session is told in [The orchestration session](../../example/README.md#the-orchestration-session). What the step left can be read file by file:

- [the executor's report](../../example/records/work/closed/2026-09-22-greeting/report-2026-09-22-greeting.md)
- [the verdict](../../example/records/work/closed/2026-09-22-greeting/verdict-2026-09-22-greeting.md)
- [closing.md](../../example/records/work/closed/2026-09-22-greeting/closing.md)
- [INDEX.md](../../example/records/work/INDEX.md)
- the final state file, [STATE.md](../../example/STATE.md)

## Step 4 — the cleanup

The exercise is not a real project. From the root of the workspace:

```bash
rm -rf projects/exercise
```

## What you learned

- A work item with a plan goes through three new sessions. Each session runs on its own tier and opens in the project's folder. An agent that the orchestrator starts carries the plan.
- Write the spec and the plans in different sessions. The second session does not reread the discussion.
- Between sessions, the only link is the state file. The handoff names the folder, the tier, the effort and the prompt.
- The plan, the spec and the work item's `README.md` sit in the same folder, in the project's records. A record is a series of dated entries. Add entries, do not rewrite them. The state of each work item sits in the work index there.
- The plan is not tested in the plans session. Its code runs only once, in the executor, and the orchestrator verifies it.
- Close a work item only when every leftover has a destination.
- The announcement `Using [skill]` is the only confirmation that a skill ran.

## What comes next

- The full rules: [AGENTS.md](../../AGENTS.md), with its modules [CLAUDE.md](../../CLAUDE.md) and [GEMINI.md](../../GEMINI.md).
- Why three sessions and an executor: [Splitting the work across models](../explanation/splitting-work-across-models.md).
- A real project: [How to start a new project](../how-to/start-a-new-project.md).
