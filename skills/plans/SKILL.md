---
name: plans
description: Use to write a work item's plans from the approved spec, when STATE.md hands over the plans or the folder has no plans.
---

# Plans for a work item

This session **reads the approved spec and writes the plans** of the work item, together with the folder's `README.md`. It does not reopen the architecture settled in the spec. It does not execute the plans. Orchestration carries them to the end: a new session, with the `orchestration` skill. That session gives each plan to an executor and checks it. The method is that of `superpowers:writing-plans`. The form, the language and the names belong to the house.

Where `writing-plans` says otherwise, this skill takes precedence. The plan does not go in `docs/superpowers/plans/`. It goes in the work item's folder. Its header belongs to the house, not to the note "For agentic workers". At the end, do not offer execution, either with subagents or in the session. Stop after section 5.

## 1. Before the first plan

Before each read, write one sentence in the chat: what you read and why.

1. **The repository state:** read it by the rule in `AGENTS.md`, "The state of the repository is read first".
2. **What the previous session handed over:** read the repository's `STATE.md`. Then read the whole spec and `request.md` from the work item's folder.
3. **The rules and the map:** read the repository's `AGENTS.md` and `IMPACT.md`. Then read the house's existing plans, as a model of form.
4. **The form:** read the long reference of the `documentation` skill, `references/details.md`, the sections "A work item's folder", "The plan" and "The folder's `README.md`". Read them before the first plan. `writing-plans` gives the method, not the form.
5. **The method:** read all of `superpowers:writing-plans`. Then announce it in the chat with `Using writing-plans to …`, in the same reply as the next step.
6. **What the machine can run:** before writing, probe with a small command the tools and commands that the tasks will need. Do not assume them.
7. **What to search for the tasks:** the reader agent reads the wide code and web searches. It also reads the long documentation that the tool's module provides. In the session, read the whole spec, `request.md` and the files that the tasks will change.

## 2. The plan

1. **The file:** `<YYYY-MM-DD-subject>.md`, in the work item's folder. When the work item has several plans, each plan carries its own subject.
2. **The header:** `Execution`, `Closing` and `Branch`.
   - `Execution` belongs to the executor. It is the medium tier, effort `high`, with escalation to the large tier, effort `medium`. Write `Execution: small` only for a mechanical plan.
   - In a mechanical plan, each task has a command as its verifier. The task names the files it touches and asks for no decision.
   - The header also carries the effort of a hands-on execution. See "The plan header is written by the planning session" in `AGENTS.md`.
   - Write `Closing: orchestrator` when the orchestrator merges the plan, after the verdict.
   - Write `Closing: human` when the plan touches services, machines or keys, or deletes anything that cannot be restored. Then the merge waits for the human's "yes".
   - Below the `Branch` line, write `**Criteria:** C1, C3`, with the criteria of the spec that the plan closes. Or write `**Criteria:** none — <why>`.
3. **The tasks:** each task has `Who` and `Verifier`, by the rule "The local worker is used first, when one exists" in `AGENTS.md`. Mark for the bridge first any task whose verifier is a command. A task marked for the session states its reason.
   Each document in the `## Documents` section of the spec gets a task, with the `documentation` skill. That task also adds the document's row to the map in `IMPACT.md`.
4. **The whole code, not a description:** write the test before the code. State what it prints when it fails and when it passes.
5. **Nothing deferred:** no blank to fill in later, and no reference such as "as in task N".

The plan goes out unverified. Its code runs for the first time at execution. The executor repairs a mechanical mistake, such as a path or an anchor, and writes the repair in the report. A design decision is not the executor's to make. That is why the plan states clearly everything that is still to decide.

## 3. The folder's `README.md`

Write it for the human, with the sections of `details.md`, in their order. Draw a Mermaid diagram with no error. `python3 bin/check-docs.py <repository root>` exits with 0.

## 4. Review and commit

1. Each requirement of the spec has a task that does it. The names used in a task are the same in every task. `python3 bin/check-docs.py --criteria <work item folder>` exits with 0. If you wrote only some of the plans, the command fails on the criteria left over. Write them in the handoff, with the plans that will close them.
2. The commit, in the work item's repository: one sentence in the repository's language that says why. No prefixes and no `Co-Authored-By`.

## 5. Stopping

Do not execute the plans here. Close the session with `end-of-session`. Its handoff calls for the orchestration session: the large tier, effort `medium`, with the one-line prompt `Orchestrate the work item <work item folder> with the orchestration skill.`
