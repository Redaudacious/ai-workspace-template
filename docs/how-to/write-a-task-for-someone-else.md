# How to write a task for someone else to execute

This guide is for anyone preparing a task that another session or worker will execute.
There are two cases:

- a task from a plan (the list of tasks, each with its verifier, that another session
  executes), carried out by a new session;
- the task file that the bridge (the tool that gives the worker the task and returns the
  diff only if the verifier passed) gives to a local worker (a model that runs on one of
  the human's machines and takes small tasks).

The executor does not see the conversation; it knows only what the task says. Why the
work is split this way:
[Splitting the work across models](../explanation/splitting-work-across-models.md).

## 1. Check first that it is worth sending

Three questions, in this order. A "no" to any of them stops the task from being sent.

| Question | If not |
|---|---|
| Does the task have a completion criterion the executor can verify on its own? | write the criterion first; otherwise it stops whenever it sees fit |
| Can the task be described without any context from the conversation so far? | write whatever context is needed directly into the task |
| Does executing it take longer than writing, sending, and verifying the task? | do it on the spot |

The last question rules out most tasks. A fix of a few lines costs more to delegate
than to resolve on the spot, because a new executor starts cold.

## 2. Write the instruction, in five parts

The instruction is self-contained and consists of five parts:

1. **What must be done**, in a single sentence.
2. **Where** — exact file paths, not descriptions.
3. **What not to touch** — just as important, and usually forgotten.
4. **How to know it is done** — the command that must exit with 0, that is the
   verifier (the command that says by itself whether a task succeeded).
5. **What to report** — exactly what the sender wants back.

An example that includes all five:

```
Fix the space check in bin/archive.sh.

Currently it requires a fixed 5 GB. It must require the space occupied by what is
to be archived, plus a 1 GB margin — measured with `du -sk` on the source directory.

Do NOT touch anything in bin/restore.sh; it is a separate path, with its own tests.

Done means: `bash tests/archive.sh` exits with 0, and the new test fails if the
fix is removed. Show both runs.

Report: the diff applied, the test output, and anything found along the way that was
not fixed.
```

The "what not to touch" section provides vital protection: an executor that spots a
neighboring issue will fix it out of goodwill, expanding the diff far beyond the task.

⚠ **Never omit the line requesting "anything found along the way that was not fixed".**
Whoever inspects the code learns things no one asked for; without this prompt, those
findings are lost without a trace.

## 3. Verify what came back

**The report is not evidence.** What changed is read directly from git, and that it
works is proven by the sender running the completion command again:

```bash
git diff --stat && git status --porcelain
```

⚠ **Read the full diff, not just its summary.** A report claiming "the function was
repaired" can easily conceal a rewrite done along the way.

⚠ **Verify any added test in pairs.** It must fail with the fix removed and pass with
it in place; otherwise it protects nothing, and the test suite passes silently without
a warning.

## 4. Decide what to do with what came back

- **keep it** — the tests pass and the diff matches what was requested;
- **request it again**, with a corrected instruction — typically the third or fourth
  part was missing;
- **discard it** — the diff sprawled beyond the task, or solved the wrong problem.

Discarding work must remain cheap. Keeping a half-good diff merely because "effort went
into it" introduces code changes that nobody decided to make.

## Where it applies

| Who executes | Where the task sits | Who verifies |
|---|---|---|
| an execution session | a task from the plan, with the `Who` label | the execution session, then the review |
| a local worker, through the bridge | the task file, written from the task text | the bridge runs the verifier, and the session runs it again |
| a model of the other tool, through `bin/tool-bridge.sh` | the same task file | the same: the bridge, then the session |

The `Who` label is the line that says who does a task in the plan, and the review is the
new session that reads what execution did and decides on the merge.

Subagents (another Claude, started from a session) are not used. The rule is in
`AGENTS.md` (the file with the common rules every session loads, in any tool), under
"Who does what".
