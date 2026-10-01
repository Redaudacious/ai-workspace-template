# Splitting the work across models

Not all parts of a work item require the same thinking power or the same
conversation. The document explains why a planned work item goes through four sessions
across different models, where the line between them falls, and where local workers
(models that run on one of the human's machines and take small tasks) fit in.

## The cost comes from the conversation re-read at every step

A session is not billed by human messages, but by **steps**: every file read, every
command, and every sentence from the model is a step, and a single message can trigger
dozens of steps.

At every step, the model receives **the entire conversation up to that point**. The part
already seen costs little because the server caches it briefly, but it costs at every
step. It is like a notebook re-read before every question: re-reading a single page is
cheap, but the notebook grows, and it is re-read hundreds of times.

The measurement behind the split below found that re-reading accounts for almost **three
quarters** of the cost, while everything the model writes — thinking, text, commands —
makes up less than a fifth. It can be re-measured at any time from machine logs:

```bash
python3 bin/usage.py
```

**What costs the most is therefore the thickness of the notebook, not the model that
writes.** An execution run that starts in a new session no longer re-reads the
discussion where the decisions were made.

## A work item goes through four sessions, each on its own model

```mermaid
flowchart LR
    spec["the spec · the most capable, much thinking"] -- "the handoff" --> plans["the plans · the same model"]
    plans -- "the handoff" --> execution["execution · the model in the plan header"]
    execution -- "the handoff" --> review["the review · the most capable, a new session"]
    execution -. "tasks with a verifier" .-> workers["the local workers, one at a time"]
```

The spec and the plans are written on the most capable model, each in its own session.
Execution runs on the model specified in the plan, usually a cheaper one, and can send
the local workers the tasks a machine can verify.

The review goes back to the most capable model, in a new session. Between every two
sessions passes a handoff.

| The session | The model | What it does |
|---|---|---|
| **the spec** | the most capable, with much thinking | talks with the human, settles the requirements, picks the architecture, writes the spec — does not write the plans |
| **the plans** | the same | reads the spec and writes the plans and the work item's `README.md` — does not write the plan's code |
| **execution** | the one in the plan header, usually a cheaper one | carries the plan to the end, without stopping between tasks, and sends to the local workers what a machine can verify |
| **review** | the most capable, in a new session | reads the execution report, the plan and the branch diff; decides what goes in |

The spec is the document that decides what is done and how; the plan is the list of
tasks, each with its verifier, that another session executes.

From one session to the next goes the **handoff** (the note in `STATE.md` for the next
session): the state file (`STATE.md`, the project's state and what comes next, rewritten at every
end of session) says which model, which effort and which prompt the next session asks
for. The human opens the new session in the chosen tool and selects the model there.

The model is not changed in the middle of a session. The long conversation would stay
behind it, and it is the expensive part.

## The expensive model sits where a mistake is expensive

Three reasons, in order of weight.

**1. A wrong decision costs more than a wrong line of code.** An architectural choice
is paid for in every subsequent session; a poorly written function is caught on the
first test run. The most capable model sits where a mistake is expensive and hard to
spot.

**2. Executing a good plan leaves nothing left to decide.** The plan specifies the
files, the code, the verifier, and who handles each task. What remains is careful work
rather than judgment, and a cheaper model is sufficient in a session unburdened by the
prior discussion.

**3. Review is cheap only in a new session.** Reopened after a pause, the planning
conversation would be rewritten whole into the server's cache, because that cache is
short-lived. A new session reads only the report, the plan, and the diff.

## The execution's decisions are written in the plan header

The plan header consists of the first lines of a plan, specifying the model and who
merges the work. Decisions for execution are written there, not left to execution
itself:

- **`Execution`** — the model and the effort (how much thinking time the model is given);
- **`Closing`** — who closes: the execution alone, or a review;
- **`Branch`** — where the execution works, keeping `main` untouched until the end;
- **`Who`**, on each task — the session, or the local worker with its model and its
  verifier (the command that says by itself whether a task succeeded).

Choosing a worker requires judgment, so it is decided during planning with the table
of models in front. Execution simply follows the label. Its procedure is the `execute`
skill.

## What goes to execution and what stays

Sent to an execution session:

- the work of a written plan, entirely.

Kept in the session where it was decided:

- the discussion with the human;
- picking the architecture and writing the plan;
- a small repair, without a plan — a new session would cost more than it saves;
- any answer that the human is waiting for now.

⚠ **The execution does not make decisions that the plan does not cover.** It stops and
asks the human. An improvised decision enters the code without deliberate sign-off and is
paid for in redone work, wiping out the very savings for which the split was made.

## How many at once: just one

No session sends work to subagents (another Claude, started from a session), and the
local workers work one at a time.

**Agents started at the same time stop at the same time.** They share the same session
allowance and hit it at the same moment; when they hit it, they do not come back with
half-done work, but with nothing. That is how it went the one time it happened.

The local workers have another reason for the same answer: a single video card. A second
model loaded pushes out the first.

## The local workers get only what a machine can verify

Small tasks, with a verifier, can go to a model that runs on one of the human's
machines, not to one paid per token.

When the project that keeps the workers is present in the workspace, it has three
things: the bridge (the tool that gives the worker the task and returns the diff only if
the verifier passed), the command that prepares the machine, and the table that says
which model can receive which kind of work.

What has to be true for the delegation to be worth it:

- **a machine can say that the task succeeded.** If the verifier is the human,
  nothing is delegated: the verification would cost more than was saved;
- **the model is measured on that kind of work.** A row without numbers in the table
  means "not used";
- **an unvalidated result does not leave the bridge.** The change reaches the repository
  only if the verifier passed;
- **the gain is mostly in "reads a lot, returns little".** What the session reads stays
  in the notebook to the end; what the worker reads does not.

## An agent's report is not evidence

A worker that says "done, it works" has reported what it believes. What changed is read
from the diff in git, and that it works is seen from the verifier run again in the
session.

The rule is the same as everywhere — **evidence before the claim** — but here it is
easier to break, because the report sounds like a verification.

## The plan sets the tier, the human chooses the tool

The plan specifies a tier rather than a tool: "Opus", the heavy tier, or "Sonnet", the
execution tier. Each tool's module says which model that tier maps to, and the handoff
writes a prompt line for each tool. The human chooses the tool at startup.

The reason is quota. Each tool is paid from its own subscription with its own limit, so
a long execution run can be directed to whichever tool has remaining capacity, while the
spec and the review remain on the model the human trusts most. The rules, skills, and
records are identical, so switching tools does not change how work is done.

The price is an extra check for each new tool: that it loads all its rules, finds its
skills, and that its module translates the tiers correctly. The steps are in
[Add a new tool](../how-to/add-a-new-tool.md).

## What is not a reason to split

**A work item is not handed over to look more organized.** Every new session starts with
the rules, the skills and the tools already loaded — tens of thousands of tokens before
the first word. A repair of a few steps is finished more cheaply on the spot.

**What the human is waiting for as an answer is not delegated.** If the question is "what
do you think", the answer belongs to the session they are talking to.
