# The greeting: the spec

Written on 2026-09-22, in the spec session, from the [request](request.md). Requirements
are settled there, so this document does not reopen them: it decides only what the request
leaves unsaid, so the plan has nothing left to choose.

## What the script does and why

`greeting.sh` takes a name as its argument and prints `hello, <name>` to standard output.
It does nothing else: it is the tutorial's exercise project, and its purpose is to pass
through the four sessions of the house, not to be useful.

Its test, `tests/test-greeting.sh`, calls it with the name `Ana` and expects exactly
`hello, Ana`. It lives in `tests/` because the framework's `./test` collector — the script
that finds and runs every test in the workspace — looks there.

## The edge case: the call without a name

The request does not specify what happens when the script is called without a name. The
decision: the script prints a usage message to standard error, `usage: greeting.sh <name>`,
and exits with code 2. The test covers this case too, so it has two checks, not one.

Code 2 is what the system's standard tools use for "wrong arguments", distinguishing it
from 1, "ran but failed".

## The rejected alternative: without a name, greet the world

Printing `hello, world` when called without an argument is friendly, but it conceals a
wrong call: a script that forgets to pass the name would receive a valid greeting and the
mistake would go unnoticed. An exit code other than 0 stops the calling chain, and the
message says what was missing.

## What this session leaves

This spec and the handoff (the note in `STATE.md` for the next session) to the plans
session, which writes the plan and the folder's `README.md`. No local worker, as the
request specifies: every task in the plan is done in the session.
