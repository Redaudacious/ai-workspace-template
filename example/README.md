# The greeting: a work item carried to completion, plain to an outside reader

This folder is a handwritten example. It uses the exact forms that the house's three sessions and the executor leave behind. The framework's tutorial produces the same forms at its end. The dates and commit hashes belong to the example, not to a real run. Read it from top to bottom. Nothing needs to be run.

**The request:** a script `greeting.sh` takes a name and replies `hello, <name>`. A test checks it. The work goes through the three sessions, without a local worker. A local worker is a model that runs on one of the human's machines and gets small tasks. The full text is in [request.md](records/work/closed/2026-09-22-greeting/request.md).

Why three sessions for two lines of code: a session rereads the whole conversation at every step. The conversation where the requirements get settled is the expensive part. The session that held that discussion closes after it writes down what it decided. The next session starts empty, from files only. The forms below are exactly those files.

## The spec session

Opened in `projects/exercise`, on the large tier, with effort (how much thinking time the model is given) `high`. It read the request. It had nothing to clarify, because the requirements were already fixed. It decided the only thing still open: what the script does when called without a name.

It left the **spec** (the document that decides what gets done and how, before the plan): [2026-09-22-greeting-design.md](records/work/closed/2026-09-22-greeting/2026-09-22-greeting-design.md), with the edge case and the rejected alternative.

Then it rewrote the **state file** (`STATE.md`, the project's current state and next steps, rewritten at the end of every session). The state file holds the **handoff**, the note for the next session.

### The handoff

| | |
|---|---|
| session | the plans |
| folder | `projects/exercise` — the session opens there |
| tier | large |
| effort | `high` |
| plan | none yet: this session writes it from the spec |
| branch | none yet: plans are written on `main`, and the execution starts the branch |

```text
Read the spec records/work/open/2026-09-22-greeting/2026-09-22-greeting-design.md and write the work item's plan and its folder's README.md, with the plan header and the Who label on every task. Do not reopen the architecture in the spec. At the end, write the handoff for the orchestration.
```

## The plans session

A new session, again in `projects/exercise`, on the large tier with effort `high`. It read the spec, not the conversation. It wrote the **plan** (the list of tasks, each with its verifier, which an agent executes), with the commands for every step: [2026-09-22-greeting.md](records/work/closed/2026-09-22-greeting/2026-09-22-greeting.md).

It did not test the plan. The code in the plan runs only once, at the executor.

The plan header names who executes: the medium tier with effort `high`. It also names how the work closes, through the orchestrator, and on which branch. Every task carries the `Who` label. Here it is always "session", because the request forbade the local worker. The code is written into the plan, so that execution copies it and does not invent it.

It also wrote the human-readable version of the work item, [README.md](records/work/closed/2026-09-22-greeting/README.md). It has the house's seven sections, from "What is being pursued" to "Where the rest is". Then it wrote the handoff for the orchestration.

### The handoff

| | |
|---|---|
| session | orchestration |
| folder | `projects/exercise` — the session opens there |
| tier | large |
| effort | `medium` |
| plan | [2026-09-22-greeting.md](records/work/closed/2026-09-22-greeting/2026-09-22-greeting.md), then still in `open/`, relative to the folder above |
| branch | from the header of each plan |

```text
Orchestrate the work item records/work/open/2026-09-22-greeting/ with the orchestration skill.
```

## The orchestration session

A new session, on the large tier with effort `medium`. It read the folder's `README.md`. It made the **orchestration state file**, [orchestration.md](records/work/closed/2026-09-22-greeting/orchestration.md), with one row per plan. The row holds the branch, the state and the verdict. Then it started the **executor**, a medium-tier agent with effort `high`. It gave the executor one line of prompt: the plan to execute.

The executor worked on the `execute/greeting` branch. It wrote the test and saw it fail. It wrote the script and saw it pass. Then it added the row to the **impact map** (`IMPACT.md`, the table of what breaks at each change, with the command that checks it). It made one commit per task.

It left [greeting.sh](greeting.sh), [tests/test-greeting.sh](tests/test-greeting.sh), and [IMPACT.md](IMPACT.md). It also left [the report](records/work/closed/2026-09-22-greeting/report-2026-09-22-greeting.md), with one row per task:

| Task | Who did it | The verifier | Deviations from the plan |
|---|---|---|---|
| 0 · the state and the branch | the agent | the branch `execute/greeting`, from an up-to-date `main` — passed | nothing |
| 1 · the test, then the script | the agent | `bash tests/test-greeting.sh` — "✓ 2 tests passed", after failing once | nothing |
| 2 · the row in the impact map | the agent | `bin/check-maps.sh` from the workspace root — `failed: 0` | nothing |

The branch, at the end:

```text
$ git log --oneline main..execute/greeting
b7e04d6 The map knows about greeting.sh, so that a change to it is caught by check-maps, not only by whoever remembers the test
3f9c2a1 The greeting has its test first, then the script, so that a call without a name fails with a sign instead of greeting nobody
```

The orchestrator did not take the report as proof. It ran the test and the map again, and it read the branch diff. Then it wrote the [verdict](records/work/closed/2026-09-22-greeting/verdict-2026-09-22-greeting.md). It merged the branch into `main` with `git merge --ff-only`. With no merge commit, `main` reached `b7e04d6`.

It closed the work item, with three traces:

- **the closing**, [closing.md](records/work/closed/2026-09-22-greeting/closing.md). It holds what came out, the deviations, and the leftovers, each with its destination. It also says where the evidence is.
- the row in [INDEX.md](records/work/INDEX.md), the work index. One row per work item, with its state: the date, the work item, `finished`, and `0` leftovers. The work item's folder, with its spec, plan and closing, moved from `open/` to `closed/`.
- the final state file, [STATE.md](STATE.md), with no report and no handoff, because no session follows. It is the real file in this folder, not a copy.

## The tree

One line per file, in the order they appeared:

```text
example/
├── README.md                     this story
├── STATE.md                      the state file, as the orchestrator left it
├── IMPACT.md                     the map: one row, greeting.sh and its test
├── greeting.sh                   the script
├── tests/
│   └── test-greeting.sh          the test; the framework's ./test runs it
└── records/work/
    ├── INDEX.md                  the work item, under "Closed"
    └── closed/2026-09-22-greeting/
        ├── README.md             the work item, for people
        ├── request.md            the prompt, word for word
        ├── 2026-09-22-greeting-design.md   the spec
        ├── 2026-09-22-greeting.md          the plan
        ├── orchestration.md      the orchestration state file
        ├── report-2026-09-22-greeting.md   the executor's report
        ├── verdict-2026-09-22-greeting.md  the orchestrator's verdict
        └── closing.md            the closing
```

What stayed untouched from `template/`, the skeleton every project starts from, is not copied here. That means the empty indexes of the other records and `docs/`.

The project's rule pair, `AGENTS.md` with `CLAUDE.md` beside it, is also absent. It has nothing to say that would cost if unknown. The files would be paid for at every session start. This is a decision of the plan, not an oversight.

## How it is run

From the workspace root, `./example/greeting.sh Ana` prints `hello, Ana`. The framework's `./test` also runs the example's test, alongside its own. The forms test, `tests/test-example.py`, reads the forms from the skills. It checks every file here against them, so the example cannot fall behind without it being noticed.
