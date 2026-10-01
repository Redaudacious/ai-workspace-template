# The greeting: the work item, for people

The work item is the tutorial's exercise project: a two-line script, carried through the
four sessions of the house. This document is its human-readable version; the execution
session does not read it — it reads the plan.

## What is being pursued

A script, `greeting.sh`, that accepts a name and prints `hello, <name>`, plus a test (a
script that calls the code and checks the output) that the framework's suite runs on
every push. Nothing more: what the exercise teaches is the process, not the script.

## Why now

The framework's tutorial promises that a three-line request goes through spec, plan,
execution, and review without the human writing any code. That promise is verified on
the smallest possible project, so that any missed step surfaces immediately rather than
hiding inside a larger one.

## The steps, without code

1. A new branch, `execute/greeting`, is started from an up-to-date `main`.
2. The test is written and seen failing, because the script does not exist yet.
3. The script is written and the test is seen passing; one commit.
4. A row goes into the impact map (the table of what breaks at each change, with the
   command that checks it), so that a change to the script is caught by the maps tool;
   one commit.

## The debatable decisions, with their risk

**Without a name, the script refuses, with code 2**, instead of greeting the world. The
argument: a bad call must be visible, and a valid greeting would mask it. The risk:
whoever expects a `hello, world` gets an error; the message says so.

**No `AGENTS.md`** (the file with the rules every project session loads, with a
`CLAUDE.md` beside it). The project
has nothing to say that would cost if unknown, and the file would be paid for at every
launch. The risk is nil as long as the project stays a single script.

**No local worker** (a model running on one of the human's machines that takes small
tasks). The request includes one so the exercise works anywhere. The risk: nothing in
the exercise demonstrates delegation; the framework's own work items show that, not the
tutorial.

## What the work item does NOT do

- It gives the script no other arguments, no `--help`, and no multiple names.
- It writes no documentation in `docs/`: there is nothing to explain.
- It does not touch the framework: everything sits in `projects/exercise`.

## How to see that it succeeded

`./greeting.sh Ana` prints `hello, Ana`; `bash tests/test-greeting.sh` prints
`✓ 2 tests passed`; `bin/check-maps.sh` from the workspace root runs the script's row
with `failed: 0`. The review ran them on `main` and wrote the results in the
[closing](closing.md).

## Where the rest is

- [The request](request.md), word for word.
- [The spec](2026-09-22-greeting-design.md), with the edge case and the rejected
  alternative.
- [The plan](2026-09-22-greeting.md), with the code and the verifiers of each task.
- [The closing](closing.md), with the evidence.
