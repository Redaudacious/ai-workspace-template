# The greeting: the spec

Written on 2026-09-22, in the spec session, from the [request](request.md). The request settles the requirements. This document does not reopen them. It decides only what the request leaves unsaid, so the plan has nothing left to choose.

## What the script does and why

`greeting.sh` takes a name as its argument. It prints `hello, <name>` to standard output. It does nothing else. It is the tutorial's exercise project. Its purpose is to run all three sessions of the framework, not to be useful.

Its test, `tests/test-greeting.sh`, calls the script with the name `Ana`. It expects exactly `hello, Ana`. The test lives in `tests/` because the framework's `./test` runner looks there. The runner is the script that finds and runs every test in the workspace.

## The edge case: the call without a name

The request does not say what happens when a caller runs the script without a name. The decision: the script prints a usage message to standard error, `usage: greeting.sh <name>`, and exits with code 2. The test checks this case too, so it has two checks, not one.

Code 2 is the code that the system's standard tools use for wrong arguments. It differs from code 1, which means the script ran but failed.

## The rejected alternative: without a name, greet the world

Printing `hello, world` without an argument is friendly. But it hides a wrong call. A script that forgets to pass the name receives a valid greeting, and nobody learns of the mistake. An exit code other than 0 stops the chain that called the script. The message says what was missing.

## What this session leaves

This spec and the handoff go to the plans session. The handoff is the note in `STATE.md` for the next session. The plans session writes the plan and the folder's `README.md`. There is no local worker, as the request asks. The session does every task in the plan.
