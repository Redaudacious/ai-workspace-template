# The greeting: a work item carried to completion, plain to an outside reader

This folder is a handwritten example in the exact forms the four sessions leave behind;
the framework's tutorial produces the same form at its end. The dates and commit hashes
belong to the example, not to a real run. Read from top to bottom — nothing needs to be
run.

**The request:** a script `greeting.sh` that takes a name and prints `hello, <name>`,
plus a test that verifies it, carried through all four sessions, without a local worker
(a model that runs on one of the human's machines and handles small tasks). The full text
is in [request.md](records/work/closed/2026-09-22-greeting/request.md).

Why four sessions for two lines of code: a session re-reads the whole conversation at
every step, and the conversation where requirements are settled is the expensive part.
The session that held that discussion closes after writing its decisions, and the next
one starts fresh from files alone. The forms below are exactly those files.

## The spec session

Opened in `projects/exercise`, on Opus, with effort (how much thinking time the model
is given) `max`. It read the request, had nothing to clarify because the requirements
were already fixed, and decided the one thing left open: what the script does when
called without a name.

It left the **spec** (the document that decides what is done and how, written before the
plan):
[2026-09-22-greeting-design.md](records/work/closed/2026-09-22-greeting/2026-09-22-greeting-design.md),
with the edge case and the rejected alternative.

Then it rewrote the **state file** (`STATE.md`, the project's current state and next
steps, rewritten at every end-of-session) with the **handoff** (the note in `STATE.md`
for the next session):

### The handoff

| | |
|---|---|
| session | the plans |
| folder | `projects/exercise` — the session is opened there |
| model | `claude-opus-5-5` |
| effort | `max` |
| plan | none yet: this session writes it from the spec |
| branch | none yet: plans are written on `main`, execution starts the branch |

```text
Read the spec records/work/open/2026-09-22-greeting/2026-09-22-greeting-design.md and
write the work item's plan and its folder's README.md, with the plan header and the Who
label on every task. Do not reopen the architecture in the spec. At the end, hand over
the execution.
```

## The plans session

A new session, again in `projects/exercise`, on Opus `max`. It read the spec — not the
conversation — and wrote the **plan** (the list of tasks, each with its verifier, that
another session executes), with the commands for every step:
[2026-09-22-greeting.md](records/work/closed/2026-09-22-greeting/2026-09-22-greeting.md).

The plan header names who executes (`claude-sonnet-5` with effort `high`), how it closes
(through review), and on which branch. Every task carries the `Who` label — here always
"session", because the request forbade the local worker. The code is written in the plan
so that execution copies it rather than inventing it.

It also wrote the human-readable version of the work item,
[README.md](records/work/closed/2026-09-22-greeting/README.md), with the house's seven
sections from "What is being pursued" to "Where the rest is", then handed over the
execution:

### The handoff

| | |
|---|---|
| session | execution |
| folder | `projects/exercise` — the session is opened there |
| model | `claude-sonnet-5` |
| effort | `high` |
| plan | [2026-09-22-greeting.md](records/work/closed/2026-09-22-greeting/2026-09-22-greeting.md), then still in `open/`, relative to the folder above |
| branch | `execute/greeting` |

```text
Execute the plan records/work/open/2026-09-22-greeting/2026-09-22-greeting.md with the
execute skill. The session's role comes from the plan header.
```

## The execution session

A new session, on Sonnet `high`, cheaper than Opus. It started the `execute/greeting`
branch from `main`, wrote the test and watched it fail, wrote the script and watched the
test pass, then added the row to the **impact map** (`IMPACT.md`, the table of what
breaks at each change and the command that checks it). One commit per task.

It left [greeting.sh](greeting.sh), [tests/test-greeting.sh](tests/test-greeting.sh),
and [IMPACT.md](IMPACT.md), plus the execution report in the state file, one row per
task:

| Task | Who did it | The verifier | Deviations from the plan |
|---|---|---|---|
| 0 · the state and the branch | the session | the branch `execute/greeting`, from an up-to-date `main` — passed | nothing |
| 1 · the test, then the script | the session | `bash tests/test-greeting.sh` — "✓ 2 tests passed", after failing once | nothing |
| 2 · the row in the impact map | the session | `bin/check-maps.sh` from the workspace root — `failed: 0` | nothing |

The branch at the end:

```text
$ git log --oneline main..execute/greeting
b7e04d6 The map knows about greeting.sh, so that a change to it is caught by check-maps, not only by whoever remembers the test
3f9c2a1 The greeting has its test first, then the script, so that a call without a name fails with a sign instead of greeting nobody
```

Execution merges nothing into `main`: the plan header requires review. It pushed the
branch and handed over:

### The handoff

| | |
|---|---|
| session | review |
| folder | `projects/exercise` — the session is opened there |
| model | `claude-opus-5-5` |
| effort | `high` |
| plan | [2026-09-22-greeting.md](records/work/closed/2026-09-22-greeting/2026-09-22-greeting.md), then still in `open/`, relative to the folder above |
| branch | `execute/greeting` |

```text
Review the execution of the plan records/work/open/2026-09-22-greeting/2026-09-22-greeting.md,
on the branch execute/greeting. Read only the report in STATE.md, the plan and
`git diff main...execute/greeting`, then run the verifiers again. Decide: merge into
main, a repair, or a small plan back for execution.
```

## The review session

A new session, on Opus `high`. It read the report, the plan, and the branch diff — not
the earlier chats — ran the test and the map again, and merged the branch into `main`
with `git merge --ff-only`: no merge commit, `main` reached `b7e04d6`.

Then it closed the work item, leaving three traces:

- **the closing**, [closing.md](records/work/closed/2026-09-22-greeting/closing.md):
  what came out, the deviations, the leftovers each with its destination, and where the
  evidence is;
- the row in [INDEX.md](records/work/INDEX.md), the work index (one row per work item,
  with its state): the date, the work item, `finished`, `0` leftovers; the work item's
  folder (containing its spec, plan, and closing) moved from `open/` to `closed/`;
- the final state file, [STATE.md](STATE.md), with no report and no handoff because no
  session follows: it is the real file in this folder, not a copy.

## The tree

One line per file, in the order they appeared:

```text
example/
├── README.md                     this story
├── STATE.md                      the state file, as the review left it
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
        └── closing.md            the closing
```

What stayed untouched from `template/`, the skeleton every project starts from, is not
copied here: the empty indexes of the other records and `docs/`.

The project's rule pair — `AGENTS.md` with `CLAUDE.md` beside it — is also absent: it
has nothing to say that would cost if unknown, and the files would be paid for at every
launch. This is a decision of the plan, not an oversight.

## How it is run

From the workspace root, `./example/greeting.sh Ana` prints `hello, Ana`, and the
framework's `./test` also runs the example's test alongside its own. The forms test,
`tests/test-example.py`, reads the forms from the skills and checks every file here
against them, so the example cannot fall behind without it being noticed.
