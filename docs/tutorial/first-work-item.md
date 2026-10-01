# The first work item, through the four sessions

The lesson takes a small work item from request to closing, through all four sessions:
the spec (the document that decides what is done and how), the plans, the execution and
the review.

At the end there is a working script, a branch merged into `main`, and a closed work
item folder — the folder with its spec, plan and closing — with everything that was
decided written inside it.

The work item is deliberately small — a five-line script — so that attention stays on
the flow, not on the code. Each new session starts with the rules and skills loaded, so
it costs something even for an exercise.

The same path, already walked in full, is in the example (a small project carried whole
through the four sessions and frozen):
[example/README.md](../../example/README.md). Each step below links to the file the
example produced, so the result can be compared with a good one.

The flow diagram is in the [README](../../README.md#how-it-works).

The environment is assumed to be restored following the steps in
[Quick start](../../README.md#quick-start): `./bin/check-lock.sh` exits with 0. New
terms are in the [glossary](../reference/glossary.md).

⚠ **Every session is opened in `projects/exercise`, not at the root.** Only then does
`AGENTS.md` (the file with the common rules, loaded by every session in every tool)
load at launch.

The framework rules (the repository with the rules, skills and tools common to all
projects), from `AGENTS.md` at the root, load from there too, because the root is a
parent.

## Step 0 — the exercise project, copied from the template

The project starts from the template (the `template/` folder, from which a new project
starts). From the workspace root (the folder into which the environment's repository was
cloned):

```bash
mkdir -p projects/exercise && cp -r template/. projects/exercise/
cd projects/exercise && git init -q -b main && git add -A && git commit -q -m "The exercise starts from the template"
python3 ../../bin/check-docs.py . | tail -1
```

`failures: 0` must appear. The project now has `records/work/INDEX.md`, empty: it is the
work index (one row per work item, with its state), and the work item will appear there.

## Step 1 — the spec session writes the spec

Open a new session in `projects/exercise`. From the application's menu, choose the Opus
model and effort (how much thinking time the model is given) `max`. Then type:

```
I want a script greeting.sh that takes a name and prints "hello, <name>", plus a
test that checks it. The requirements are fixed. Write the spec of the work item in
its folder, in records/work/, and hand the plans over to the next session. The
closing: Opus review, so that I go through all four sessions. No local worker: the
exercise must work on a machine without one too.
```

`Using superpowers:brainstorming` must appear and, at the end, `Using end-of-session`.
The closing shows what it is about to write and asks for one "yes".

In a terminal, in `projects/exercise`, check:

```bash
ls records/work/open/*/
sed -n '/^### The handoff/,/^### Read first/p' STATE.md
```

A folder with the spec, `<folder>-design.md`, must appear. In `STATE.md`, the state file
(the project's state and what comes next, rewritten at every end of session), a handoff
table (the note in `STATE.md` for the next session) to the plans session must appear:
the folder, the model, the effort, plus the prompt to paste.

The session's last message also gives the prompt, the folder and the model of the next
session. The model is not changed here: this session is closing.

In the example, the same step left the
[request](../../example/records/work/closed/2026-09-22-greeting/request.md), which is the
prompt above, and the
[spec](../../example/records/work/closed/2026-09-22-greeting/2026-09-22-greeting-design.md).

## Step 2 — the plans session writes the plan

Open a new session, again in `projects/exercise`, again on Opus, effort `max`, and paste
the prompt from the handoff.

`Using superpowers:writing-plans` must appear and, at the end, `Using end-of-session`.
The session does not reopen what was settled in the spec. It writes the plan (the list of
tasks, each with its verifier, that another session executes), with its header, and the
work item's `README.md`.

Check:

```bash
ls records/work/open/*/
sed -n '1,/^## /p' records/work/open/*/2026-*-plan*.md 2>/dev/null || head -12 records/work/open/*/*.md
```

Next to the spec, `README.md` and the plan must appear, and in the plan header (the first
lines of a plan, with the model and who merges the work) the lines `Execution`, `Closing`
and `Branch`. In `STATE.md` now sits the handoff to the execution.

In the example: the
[plan](../../example/records/work/closed/2026-09-22-greeting/2026-09-22-greeting.md) and
the [work item's README](../../example/records/work/closed/2026-09-22-greeting/README.md).

## Step 3 — the execution session carries the plan to the end

Open a new session, in `projects/exercise`. From the menu, choose the model and effort
written in the handoff, then paste the prompt from the handoff.

`Using execute` must appear. The session works without stopping between tasks, on the
branch in the plan header, and also closes with `end-of-session`.

Check:

```bash
git branch --show-current
git log --oneline main..HEAD
```

The branch `execute/…` must appear, with one commit per task. Run the plan's test (a
script that calls the code and checks the answer) once here too, with the command written
in the plan: a session's report is not evidence, the command's output is.

In `STATE.md` now sit the execution report — one row per task — and the handoff to the
review.

In the example, the step is told in
[The execution session](../../example/README.md#the-execution-session), with the report
and the handoff.

## Step 4 — the review session merges and closes

Open a new session, in `projects/exercise`, on Opus, effort `high`, and paste the review
prompt from the handoff.

The reading of the report, of the plan and of the branch diff must appear, then the test
run again. If everything matches, the review merges the branch into `main`. At
`end-of-session` it proposes closing the work item; answer "yes".

Check:

```bash
git branch --show-current
ls records/work/closed/
sed -n '/^## Closed/,$p' records/work/INDEX.md
```

`main` must appear, the work item's folder moved into `closed/`, with a new `closing.md`,
and a row under "Closed" with the state `finished` and zero leftovers (a leftover is a
task not done from a work item).

In the example:
[closing.md](../../example/records/work/closed/2026-09-22-greeting/closing.md),
[INDEX.md](../../example/records/work/INDEX.md) and the final state file,
[STATE.md](../../example/STATE.md).

## Step 5 — the cleanup

The exercise is not a real project. From the workspace root:

```bash
rm -rf projects/exercise
```

## What was learned

- A planned work item goes through four new sessions, each on its own model, each opened
  in the project's folder.
- The spec and the plans are written in different sessions: the second does not re-read
  the discussion.
- Between sessions, the only link is the state file: the handoff says the folder, the
  model, the effort and the prompt.
- The plan, the spec and the work item's `README.md` sit in the same folder, in the
  project's records (a record is a series of dated entries, appended and never
  rewritten), and their state sits in the work index there.
- A work item is closed only when every leftover has a destination.
- The announcement `Using [skill]` is the only confirmation that a skill was applied.

## What comes next

- The rules in full: [AGENTS.md](../../AGENTS.md), with its modules
  [CLAUDE.md](../../CLAUDE.md) and [GEMINI.md](../../GEMINI.md).
- Why four sessions: [Splitting the work across models](../explanation/splitting-work-across-models.md).
- A real project: [How to start a new project](../how-to/start-a-new-project.md).
