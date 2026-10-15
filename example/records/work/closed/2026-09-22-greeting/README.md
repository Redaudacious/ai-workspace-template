# The greeting: the work item, for people

The work item is the exercise project of the tutorial: a two-line script that passes through the three sessions of the framework. This document is its version for people. The executor does not read it. It reads the plan.

## What is pursued

A script, `greeting.sh`, takes a name and prints `hello, <name>`. The framework's suite runs a test on every push. The test calls the script and checks the answer. Nothing more. The exercise teaches the process, not the script.

## Why now

The framework's tutorial promises that a three-line request passes through spec, plan, and orchestration. The human writes no code. The exercise checks the promise on the smallest possible project. Then any missed step shows at once, and not inside a larger project.

## The steps, without code

1. Start a new branch, `execute/greeting`, from an up-to-date `main`.
2. Write the test. Run it. It fails, because the script does not exist yet.
3. Write the script. Run the test. It passes. Make one commit.
4. Add a row to the impact map, so that the maps tool catches a change to the script. The impact map is a table of what breaks at each change, with the command that checks it. Make one commit.

## The debatable decisions, with their risk

**Without a name, the script refuses, with code 2.** It does not greet the world. The argument: a bad call must be visible, and a valid greeting would hide it. The risk: whoever expects `hello, world` gets an error. The message says so.

**No `AGENTS.md`.** That is the file with the rules that every session of the project loads, with `CLAUDE.md` beside it. The project has nothing to say that would cost anything if unknown. The file would cost tokens at every session start. The risk is nil as long as the project stays a single script.

**No local worker.** A local worker is a model that runs on one of the human's machines and takes small tasks. The request asks for this, so the exercise works anywhere. The risk: nothing in the exercise shows delegation. The documentation's plan 1 shows it, not the tutorial.

## What the work item does NOT do

- It gives the script no other arguments, no `--help`, and no multiple names.
- It writes no documentation in `docs/`. There is nothing to explain.
- It does not touch the framework. Everything sits in `projects/exercise`.

## How to see that it succeeded

`./greeting.sh Ana` prints `hello, Ana`. `bash tests/test-greeting.sh` prints `✓ 2 tests passed`. `bin/check-maps.sh` from the workspace root runs the script's row with `failed: 0`. The orchestrator ran these commands on `main`. It wrote the results in the verdict and in the [closing](closing.md).

## Where the rest is

- [The request](request.md), word for word.
- [The spec](2026-09-22-greeting-design.md), with the edge case and the rejected alternative.
- [The plan](2026-09-22-greeting.md), with the code and the verifiers of each task.
- [The report](report-2026-09-22-greeting.md) of the executor, one row per task.
- [The verdict](verdict-2026-09-22-greeting.md) of the orchestrator, with what it ran again.
- [The orchestration state file](orchestration.md), with the state of the plan.
- [The closing](closing.md), with the evidence.
