---
name: execute
description: Use to execute a written plan. This covers the executor that the orchestrator starts. It also covers a session that a human opens when STATE.md hands over the execution of a plan. It also covers a plan in a work item's folder with the Execution and Closing lines in its header.
---

# Executing a plan

The execution **executes**. It does not decide. The decisions are already written in the plan header (`Execution`, `Closing`, `Branch`) and in the `Who` label of each task. Why the work is split this way: `docs/explanation/splitting-work-across-models.md`.

The **executor** does the execution. The orchestrator starts the executor on the small or the medium tier, following the plan header. The `escalation` agent works on the large tier. As a manual variant, a session that a human opens in another tool does it, when the Claude limit is tight. There is one difference. The executor cannot ask the human. So where a session would ask, the executor stops and returns the reason.

⚠ **Read nothing "just in case".** Everything that the execution reads stays in context. It is paid for at every step after that. Read the plan, the spec from the same folder, and the files that a task touches. The folder's `README.md` is for people.

## 1. Before the first task

1. **The repository's rules.** The work item's folder is in the records of the repository that the plan changes. Read the repository's `IMPACT.md` now, always. The map never loads by itself. Read `AGENTS.md` only if the execution did not start in the folder of that repository.
2. **The state of every repository that the plan touches.** Run `fetch`, `status -sb` and `status --porcelain`, by the rule in `AGENTS.md`. What is uncommitted and does not belong to the plan stays uncommitted. Commit only the paths that the tasks name.
3. **The branch in the plan header.** Create it from an up-to-date `main`: `git switch -c <branch>`. If the branch already exists, continue on it. Start from the first task that has no commit, or from the task that the orchestrator names.
4. **The worker.** Prepare it only if the plan has a `Who: bridge` task:

   For a house model, the commands are not here. Read them from `records/local-workers.md`, in the sections `## Preparing and releasing` and `## Access`. The model of the other tool needs no preparation. If the file is missing, or `## The workers` has no row with numbers, **do the `bridge` tasks here**. Write the reason once in the report.

## 2. Each task

Do the tasks in the order of the plan, **without stopping between them**.

- **The start of each task:** write one sentence in the chat that names the task you start.
- **`Who: session`** — do the task here. For new code or a repair, use `superpowers:test-driven-development`. For documentation, use the `documentation` skill.
- Write the test first, also for **a repair found on the way**, even when the plan does not ask for it.
- Repair on the spot **a mechanical mistake in the plan**: a wrong path, anchor or letter. Write the form in the plan and the form used in the report. A design decision is not mechanical. For a design decision, stop the execution as § 3 says.
- **`Who: bridge`** — write the task text to a file in the temporary folder. Then run the bridge **in the background**, from the root of the repository. For a house model, use the bridge from `## The bridge` in `records/local-workers.md`. For the model of the other tool, use `bin/tool-bridge.sh`. The target, the task text and the verifier come from the task's label.

  | Bridge code | What is done |
  |---|---|
  | 0 | apply the diff, **run the verifier again here**, commit |
  | 1 | **read the reason for the refusal in the bridge's output**, then do the task here. In the report, write the reason read, never "not read" |
  | 2 | do the task here. In the report, write "does not fit the window" |

  ⚠ Do not print any access token. The bridge's report is not evidence. The evidence is the verifier, run here.
- Compare **a failed verifier** first with the state before the change. An old failure is not the task's. Write in the report that it is old.
- Delete on the spot **a wrong write**, for example a file put on a wrong path.
- Read **a finished document** again before the commit. Repair what you find.
- **The end of the task:** finish in this order: the report row, `git add` on its files, the verifiers, commit. Write the report before the verifiers, so that they also check it.
- **The report** is in the work item's folder, in `report-<plan name>.md`. It grows by one row per task. A row has the task, who did it (the execution or the bridge's model), the verifier with its result, the deviations and the mechanical repairs. The report goes into the commit of the task.

⚠ The workers work one at a time. The execution starts the reader, at most, one at a time. The executor and the escalation start no agent.

### The Antigravity worker

On Antigravity's execution tier, Gemini 3.8 Flash, a task with a verifier goes through the tool bridge. Run this command from the root of the repository that you change:

```bash
bin/tool-bridge.sh --tool agy --model gemini-3.8-flash-high --target <file> --task <file> --verify '<command>'
```

When the Gemini quota is exhausted, the same route leads to Claude Sonnet 4.6, with `--model claude-sonnet-4-6`. Antigravity draws it from a different quota than the Gemini models do. The bridge names the exhausted quota and does not retry.

From a project, call the script in the root's `bin/`, two folders up. The script requires `agy` to be authenticated.

### The Vibe worker

The same route leads to Mistral Large 4, with `--tool vibe` and the profile in place of the model. Use `--model execute-fast` for a mechanical task. Use `--model execute` for a task that needs reasoning. Each call has a cap, set by `BRIDGE_CAP`, one dollar by default. The bridge names the cap that was reached and does not retry. The script requires `vibe` to be authenticated. Run `bin/vibe.sh` first.

## 3. The stop rules

The execution stops only at these moments:

1. **A decision that the plan does not cover.** The session asks the human, with options. The executor stops and returns the question with its options. It does not choose.
2. **A verifier fails even after two repairs.** Run one round of `superpowers:systematic-debugging`. If the verifier still fails, stop. Return the task, the output of the verifier and what you tried.
3. **What only the human can do:** a login on a house application, someone at a house machine, `sudo`.

A stopped executor returns the summary from § 5, with the reason for the stop on the first line.

## 4. What is said openly

The report and the summary put these items first, so that the orchestrator checks them first:

- a stop rule that was hit, with the human's answer, if there was one
- a file that was changed and that the plan does not name
- a verifier from the plan that was changed so that it passes
- each mechanical repair of the plan

A bridge failure is **not** a deviation. The plan expects it.

## 5. The closing

1. **Releasing the machine.** If the preparation ran, release the machine, however the execution ended. Use the command from `## Preparing and releasing` in `records/local-workers.md`.
2. **`superpowers:verification-before-completion`**: now run the verifiers of the plan, the verifiers of every repository that was touched, and `bin/documents.py`. Run them after the last file is written, the report included.
3. **The executor** does not merge, does not push and does not run `end-of-session`. The merge belongs to the orchestrator. The executor returns a summary of at most 2,000 tokens. The summary has one row per task, with the verifier passed, or the point where it stopped and the reason. Then come the mechanical repairs, the path of the report and the last commit.
4. **A session that a human opens:** show the human, in the chat, the commits that are about to be pushed, with `git log --oneline origin/<branch>..HEAD`. When the human says yes, push **only the branch** and run `end-of-session`. The handoff goes to orchestration, which checks the plan and merges it:

```text
Orchestrate the work item <work item folder> with the orchestration skill.
```
