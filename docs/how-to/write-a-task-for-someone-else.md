# How to write a task for someone else to execute

This guide is for anyone who prepares a task that another session or worker will execute.
There are two cases:

- A task from a plan, taken on by a new session. The plan is a list of tasks, and each
  task has its own verifier. Another session executes the task.
- The task file that the bridge gives to a local worker. The bridge is the tool that gives
  the worker the task, and it returns the diff only if the verifier passed. A local worker
  is a model that runs on one of the user's machines and takes small tasks.

The executor does not see the conversation. It knows only what the task says. Why the work
is split this way: [Splitting the work across models](../explanation/splitting-work-across-models.md).

## 1. Decide first whether the task is worth sending

Three questions, in this order. A "no" to any of them means that you do not send the task.

| Question | If not |
|---|---|
| Does the task have a completion criterion that the executor can verify on its own? | write the criterion first, or it stops whenever it sees fit |
| Can the task be described without any context from the conversation so far? | write the needed context directly into the task |
| Does executing it take longer than writing, sending, and verifying the task? | do it on the spot |

The last question excludes most tasks. A fix of a few lines costs more to delegate than to
resolve on the spot, because a new executor starts cold.

## 2. Write the instruction, in five parts

The instruction is self-contained. It has five parts:

1. **What must be done**, in one sentence.
2. **Where**: exact file paths, not descriptions.
3. **What not to touch**. This part matters as much as the others, and it is often forgotten.
4. **How to know the task succeeded**: the command that must exit with 0. This is the verifier,
   the command that says by itself whether a task succeeded.
5. **What to report**: exactly what the sender wants back.

An example that includes all five:

```
Fix the space check in bin/archive.sh.

Right now it requires a fixed 5 GB. It must require the space that the files to archive
occupy, plus a 1 GB margin. Measure the space with `du -sk` on the source directory.

Do NOT touch anything in bin/restore.sh. It is a separate path, with its own tests.

Done means: `bash tests/archive.sh` exits with 0, and the new test fails if the fix is
removed. Show both runs.

Report: the diff applied, the test output, and anything you found along the way that you
did not fix.
```

The "what not to touch" part protects the work. An executor that sees a nearby problem
fixes it out of goodwill, and the diff becomes larger than the task.

⚠ **Never omit the report line that asks for "anything you found along the way that you did
not fix".** Whoever reads the code learns things that nobody asked for. Without this line,
those findings are lost without a trace.

## 3. Verify what came back

**The report is not evidence.** Read what changed from git. Then the sender runs the
completion command again, to see that the work passes:

```bash
git diff --stat && git status --porcelain
```

⚠ **Read the full diff, not just its summary.** A report that says "I fixed the function"
can hide a rewrite made along the way.

⚠ **Verify any added test in pairs.** It must fail with the fix removed and pass with the fix
in place. Otherwise it protects nothing, and the suite keeps passing without any sign of it.

## 4. Decide what to do with what came back

- **Keep it**: the tests pass, and the diff is the one requested.
- **Request it again**, with an improved instruction. Usually the third or fourth part was missing.
- **Discard it**. The diff went beyond the task, or it solved something else.

Discarding work must remain cheap. Keeping a half-good diff merely because "effort went into
it" introduces code changes that nobody decided to make.

## Where it applies

| Who executes | Where the task sits | Who verifies |
|---|---|---|
| the executor, started by the orchestrator | a task from the plan, with the `Who` label | the executor, then the orchestrator, which runs the verifiers again |
| a local worker, through the bridge | the task file, written from the task text | the bridge runs the verifier, and the session runs it again |
| a model of the other tool, through `bin/tool-bridge.sh` | the same task file | the same: the bridge, then the session |

The `Who` label is the line in the plan that says who does a task. The orchestrator is the
session that gives the plan to the executor, reads what it did, and decides on the merge.

A session starts only house agents as subagents, and only one at a time. A subagent is
another Claude, started by a session. The rule is in `AGENTS.md` (the file with the common
rules that every session loads, in any tool), under "One subagent at a time, in the
foreground, and only from the house agents".
