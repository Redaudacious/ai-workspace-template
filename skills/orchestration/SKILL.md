---
name: orchestration
description: Use in the session that takes a work item's plans to main, when STATE.md passes orchestration or plans are written but not merged.
effort: medium
---

# Orchestrating a work item

This session **takes the work item's plans to `main`**. It passes them one at a time to an executor, checks them, and merges them. It does not write code and does not repair plans. The executor writes the code. The person makes the decisions. A faulty plan goes back to the plans session.

This session runs on the large tier at `medium` effort. The person chooses it when the session opens. Its agents are framework definitions in `agents/`:

| agent | tier | what it does |
|---|---|---|
| `executor` | medium tier at `high` effort, or small tier, depending on the plan's header | runs one whole plan with the `execute` skill |
| `escalation` | large tier at `medium` effort | resumes the plan at the task the executor did not pass |
| `reader` | small tier at `medium` effort | reads long output and returns only what was asked |

⚠ **One agent at a time, in the foreground** (`run_in_background: false`). Wait for the agent's result. The reason is in `AGENTS.md`.

## 1. State

Before each read, write one sentence in the chat: what you read and why.

1. **Repository state**: read it by the rule in `AGENTS.md`, "Read the repository state first."
2. **The work folder's `README.md`**: read it. The plans are listed there in order.
3. **The state file**, `orchestration.md` in the work folder. It is missing in the first session. Create it then, with one row per plan, in the order of `README.md`:

   | plan | branch | state | verdict | escalations |
   |---|---|---|---|---|
   | `<plan file>` | `<branch named in its header>` | to do | — | 0 |

   The states are `to do`, `with executor`, `with escalation`, `to verify`, `merged`, and `returned`. Rewrite the state file after each step in section 2, before the next step. Commit it together with the verdict. A new session, opened after the five-hour limit ended partway through the work, reads the state file. It continues from the first plan that is not merged.
4. **Criteria coverage**, before the first plan: `python3 bin/check-docs.py --criteria <work folder>`. If it exits with code 1, do not start the orchestration. Write the uncovered criteria in `return.md`, as in step 7 of section 2. The handoff needs a new plans session.

## 2. One plan

1. **The executor.** Send the first plan that is not `merged` to the `executor` agent, with a one-line prompt: `Execute the plan <plan path> with the execute skill.` Add nothing else, because the plan says everything. If the plan's header contains `Execution: small`, start the executor on the small tier's model, as the tool module says. Otherwise, the executor runs on the tier in its definition, which is the medium tier.
2. **Its summary**, at most 2,000 tokens, says how far it got.
   - The plan is done: go to step 3.
   - It stopped at a task it could not pass: go to step 4.
   - It stopped at a decision the plan does not cover: ask the person the question, with options. Send the answer to a new executor, with the task to resume from.
3. **Verification.** The starting assumption is that the plan did not meet its criteria. The executor's report is a claim to disprove, not proof. A check can go soft in four ways. Avoid them:
   - Do not trust the report without reading the code.
   - Do not treat a file that exists as proof that it works.
   - Do not choose "unsure" when the missing part is visible.
   - Do not let several passed tasks tilt the judgment toward "good."

   The steps of verification:
   - Read the plan, the executor's report in the work folder, and `git diff main...<branch>`.
   - Run each task's verifier again, and the repository checks in `IMPACT.md`. Have the reader read long output.
   - Run `python3 bin/documents.py <repository>` and `--complete` in each repository touched. Exit code 1 is an execution mistake, step 5. Exit code 2 says that the repository has no map yet.
   - If `main` has moved since the branch left, run the checks on the merge result too, in a copy, before the merge.
   - Judge each criterion in the plan's header, `**Criteria:**`, by the kind written beside it in the spec:

     | kind | what the orchestrator does | result |
     |---|---|---|
     | command | runs the command from the spec | Exit code 0 gives **verified**. Otherwise, **failed**. |
     | person | asks the person a question in a message: what to do and what they should see | "yes" gives **verified**. "no" gives **failed**. "don't know" gives **unsure**. |
     | later | judges nothing now | **later**, with the date |

     A **failed** criterion is an execution error, step 5. An **unsure** criterion goes to the person as a decision, with options.
   - Write the verdict in the work folder, as `verdict-<plan name>.md`. Include what was run with its result, the deviations in the report, and the decision. Add a "Criteria" section: a table with the criterion, its kind, what was run or asked, and the result. For a plan on the small tier, add the escalations and the cost of each agent. Get the cost from `python3 bin/usage.py --agent <id>`, where the id comes from the Agent tool result. The command also prints the price of the same tokens on Sonnet.
4. **Escalation.** When the verifier of a task fails and the executor could not repair it, escalate the task one tier. Give the plan path, the task number, and the executor's summary. After the small tier, start a new executor with no `model` override, so it runs on the medium tier. After the medium tier, start the `escalation` agent, which runs on the large tier. The new tier resumes there and runs to the end of the plan. Then go to step 3.
5. **An execution error** is a verifier that fails here, a failed criterion, a skipped task, or a file the plan does not name. Return it **once** to a new executor, on the medium tier, with what needs repair. A second time is a plan error: step 7.
6. **Merge.** When the verdict is good, with no failed or unsure criterion, merge the branch into `main` with `git merge --ff-only`. If `main` has moved, use the merge verified in step 3. Then push. A **later** criterion does not stop the merge. Put it among the work's leftovers, with its date. `end-of-session` puts it in the work queue.

   ⚠ A plan with `Closing: person` waits for the person's "yes" after the verdict and before the merge. Such a plan touches services, machines, or keys, or deletes what cannot be recovered. There, a mistake can no longer be reversed.

7. **A plan error** is a plan that fails at escalation too, or a plan that asks for something that cannot be done. Stop the orchestration. Write what is missing in the work folder, in `return.md`: the plan, the task, what was tried, and what the plan should have said. The handoff needs a new plans session. If a decision is missing from the spec, the handoff needs a new spec session. The person opens both.

The person can run a plan in another tool, for example in Antigravity when the Claude limit is tight. The plan already has its branch and report. Its orchestration starts with verification, step 3.

## 3. Between plans

After each merged plan, write one sentence in the chat. It names the plan, the verdict, the number of escalations, and how much of the work is finished, in percent. If more plans remain, suggest that the person run `/compact`, with what to keep: the skill, the work folder, and the next plan.

## 4. Orchestration in Vibe

When the session runs in Mistral Vibe, the framework's agents are separate Vibe runs. They use the profiles in `MISTRAL.md`, and they start from the repository root with `tools.process.start`. Wait for them with `tools.process.output` (`waitMs: 30000` per call) until they end. The rule stays the same: one at a time, waited on to the end. The `bash` tool stops at 300 seconds and refuses longer waits.

| agent | command |
|---|---|
| `executor` | `vibe --agent execute -p "Execute the plan <plan path> with the execute skill." --auto-approve --trust --max-price 2 </dev/null` |
| `executor`, with `Execution: small` | the same, with `--agent execute-fast` |
| `escalation` | `vibe --agent escalation -p "Resume the plan <plan path> from task <n>. The executor: <its summary>" --auto-approve --trust --max-price 3 </dev/null` |
| `reader` | `vibe --agent reader -p "<question>" --trust --max-price 0.20 </dev/null` |

The agent's summary is the text at the end of its output. `Price limit exceeded` in the output means the run stopped at the price limit. Read what it did from `git log` and the report. Send the plan to a new executor one time only, starting from the first task without a commit. A second stop at the price limit is a plan error, step 7 in section 2.

## 5. Closing

When all plans are merged, `end-of-session` closes the work: `closing.md`, the folder moved to `closed/`, and the leftovers, each with its destination. Write a last message for the person. Tell them, in plain words, what entered `main`, what escalated to the large tier, and what returned to the plans or to the spec.
