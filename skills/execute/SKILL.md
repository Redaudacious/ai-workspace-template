---
name: execute
description: Use in the session that executes a written plan - when STATE.md hands over the execution of a plan, when the plan in a work item's folder has the Execution and Closing lines in its header, or when /execute is typed.
---

# Executing a plan

This session **executes**, it does not decide. The decisions are already written: in
the plan header (`Execution`, `Closing`, `Branch`) and in the `Who` label of each
task. Why the work is split this way: `docs/explanation/splitting-work-across-models.md`.

⚠ **Nothing is read "just in case".** Everything the session reads stays in context
and is paid for at every step after. What is read: the plan, the spec from the same
folder, and the files a task touches. The folder's `README.md` is for people.

## 1. Before the first task

1. **The repository's rules.** The work item's folder sits in the records of the
   repository the plan changes. If the session did not start in that repository's
   folder, its `AGENTS.md` and `IMPACT.md` are read now; how the tool brings in the
   rest of the rule chain is described in its module.
2. **The state of every repository the plan touches**, by the rule in `AGENTS.md`:
   `fetch`, `status -sb`, `status --porcelain`. What is uncommitted and does not
   belong to the plan stays uncommitted: only the paths named by the tasks are committed.
3. **The branch in the plan header**, from an up-to-date `main`: `git switch -c <branch>`.
   If it already exists, work continues on it, from the first task without a commit.
4. **The worker**, only if the plan has a `Who: bridge` task:

   For a house model, the commands are not here. They are read from
   `records/local-workers.md`, the sections `## Preparing and releasing` and
   `## Access`; the other tool's model requires no preparation. The file is missing,
   or `## The workers` has no row with numbers: **the `bridge` tasks are done in the
   session**, and the reason is written once in the report.

   The preparation codes and what is done at each are written there too, because they
   belong to the human's tool, not to the framework.

## 2. Each task

In the order of the plan, **without stopping between them**.

- **`Who: session`** — done here. New code or a repair:
  `superpowers:test-driven-development`. Documentation: the `documentation` skill.
- **`Who: bridge`** — the task file is written in the session's temporary folder,
  from the text of the task, then the bridge runs **in the background**, from the
  root of the repository: the one from `## The bridge` in `records/local-workers.md`
  for a house model, `bin/tool-bridge.sh` for the other tool's model, as described
  in the tool's module. The target, the task file, and the verifier come from the
  task's label.

  | Bridge code | What is done |
  |---|---|
  | 0 | the diff is applied, **the verifier run again here**, commit |
  | 1 | **the reason for the refusal is read from the bridge's output**, then the task is done in the session; in the report, the reason read, never "not read" |
  | 2 | the task is done in the session; in the report, "does not fit the window" |

  ⚠ No access token or key is printed. The bridge's report is not evidence; the evidence is the
  verifier run here.
- **The end of the task:** `git add` on its files, the verifiers, commit.
- **The report** grows by one row per task, in a file in the temporary folder: the
  task, who did it (the session or the model), the verifier with its result, the
  deviations.

⚠ The workers work one at a time. **No subagent**, for anything.

## 3. The stop rules

The only moments when the execution stops and asks the human:

1. **A decision the plan does not cover.** It is asked with options; it is not chosen.
2. **A verifier fails even after two repairs.** One round of
   `superpowers:systematic-debugging`; if it still fails, stop.
3. **What only the human can do:** a login on a house application, someone at a
   house machine, `sudo`.
4. **The closing, before the merge and the push:** the human sees what goes into git
   and the new state file, then says "yes"; the steps are in § 5. The closing goes
   ahead without asking only when the human said beforehand to close without them.

## 4. What requires review

Even with `Closing: Sonnet`, any of these sends the work to review:

- a stop rule was hit, and the human's answer changed the plan;
- a file was modified that the plan does not name;
- a verifier in the plan had to be changed to pass;
- a task fails even after the debugging round.

A bridge failure does **not** require review: the plan expects it.

## 5. The closing

1. **Releasing the machine**, with the command from `## Preparing and releasing` in
   `records/local-workers.md`, if the preparation ran, however the
   execution ended.
2. **`superpowers:verification-before-completion`**: the verifiers of the plan and of
   every repository touched, run now.
3. **The human's "yes".** Show, in the chat: the commits about to leave, with
   `git log --oneline origin/<branch>..HEAD`, where they go (the branch or `main`) and
   the list of what `end-of-session` writes — the state file, the records. Until the
   "yes", nothing is merged, pushed or written by the closing.
4. **Where the work goes:**

   | The plan and the execution | What is done |
   |---|---|
   | `Closing: Sonnet`, nothing from § 4 | `git merge --ff-only` into `main`, push |
   | `Closing: Opus review`, or anything from § 4 | **only the branch** is pushed |

5. **`end-of-session`**, with the report put in the `STATE.md` of the work item's
   repository and the handoff completed.
6. **The last message to the human**, in the chat, not only in `STATE.md`:
   - **what the human has to do now**, in steps: the new session to open, in which
     folder, plus anything only they can do (`sudo`, a login, a decision left open);
   - **the next session's prompt**, attached to its model. The row with the folder
     and the model for each tool sits **immediately above** the block, so that one
     is not read without the other:

     ```text
     New session · folder: projects/<project>
     Claude Code: <model> · effort <effort>
     Antigravity: <identifier>
     ```
     one row per tool that has a module at the root, after the handoff, followed by
     the whole prompt in a block to paste, copied from the handoff.

   ⚠ The human reads the chat, not the state file. A handoff written only in
   `STATE.md` leaves them to look for what comes next by themselves, and a prompt
   without a model leaves them to guess what to run it on.

The review prompt, to put in the handoff:

```text
The review of the execution of the plan <path of the plan>, on the branch <branch>.
Read only the report in STATE.md, the plan and `git diff main...<branch>`,
then run the verifiers again. Decide: merge into main, a repair,
or a small plan sent back for execution.
```

The review runs on the heavy tier, effort `high`, in a **new** session, opened in
the folder of the work item's repository; the exact model, for each tool, is written
in the handoff.
