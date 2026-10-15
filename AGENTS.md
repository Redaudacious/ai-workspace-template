# How work is done in this folder

This file holds what is the same for every AI coding tool. Each session loads it by itself.
Each heading is a rule. Under each heading are its form and its reason.
The words of the framework are in the [glossary](docs/reference/glossary.md).

Invoke `superpowers:using-superpowers` before any response, including before clarifying questions.

## The rules broken most often

On the bench, models broke the rules below most often, although the framework already wrote them.
Apply each rule when its turn comes, not at the end.

1. **The role the human asks for starts with its skill**. When the human asks for the spec, the plans, or the orchestration, your first call is the skill of that role: `spec`, `plans`, or `orchestration`. That call comes before any other tool. A "complete" request does not replace the spec. Written code does not replace the role.
2. **Announce the skill in the same message as its call**. The first sentence of the message has the form `Using <skill> to <purpose>`. Do the same for a skill that another skill asks for: `brainstorming` after `spec`, `writing-plans` after `plans`, and `documentation` before a document. An announcement written after the call does not count.
3. **State the percentage from the first message**. State it after reading the state, after a write, after a commit, and at each phase: `N% done. About M minutes remain.` A status without a percentage is not a status.
4. **Read the repository state before the first write in it**. Run `git status` in the repository, not `ls`. Then read the `STATE.md` and `IMPACT.md` of the project. `README.md` and the modules do not replace `IMPACT.md`.
5. **Ask one question per message**. Show the design piece by piece. Give each piece its own message, with one question at the end. Move to the next piece after the human says yes.
6. **Name every criterion of the spec in the plan header**. Name also the criteria that wait for the human or for a date. A missing criterion stops the orchestration.
7. **Write the whole handoff**. A handoff to a new session names its role, its tier with its effort, and its prompt. Write all three in the last message and in `STATE.md`. "A new planning session" is not a handoff.

Reason: on 10 October 2026, the model of another tool failed 5 runs out of 8 on rules 2 to 7. On 13 October 2026, a small-tier model skipped the `spec` skill. It wrote code directly in 2 runs out of 4.

Rule 4, reason: a branch left behind creates a conflict that nobody sees until the push.

Rule 7: `end-of-session` writes the handoff into the `STATE.md` of the work item's repository. The handoff has one row for each tool with a module at the root. Each row names the model and effort, as the module says, the folder, and the prompt to paste.

## Who does what

Planned work goes through **three sessions**. Each one is new, opened by the human, with its own role:

| session | tier | does | does not do |
|---|---|---|---|
| **spec** | large, `high` effort | talks with the human, settles the requirements, chooses the architecture, writes the spec of the work item | does not write the plans. It passes them to the next session |
| **plans** | large, `high` effort | writes the plans and the `README.md` of the work item from the approved spec | does not reopen the architecture settled in the spec. Does not test the plan |
| **orchestration** | large, `medium` effort | gives the plans one by one to the executor, checks them, and merges them into `main`, with the `orchestration` skill | does not write code. A wrong plan goes back to the plans session. A missing decision goes back to the spec session |

**The executor** carries out the plan. It is a medium-tier agent at `high` effort, started by the orchestrator with the `execute` skill. A mechanical plan goes to the small tier. A task that fails moves up one tier. It goes from the small tier to a medium-tier executor, then to the **escalation** agent. The escalation agent runs at the large tier with `medium` effort. The orchestrator's check takes the place of a review session.

Reason: rereading the conversation at each step makes up most of the cost. A new session does not carry the discussion in which the decision was made.
History: [splitting work across models](docs/explanation/splitting-work-across-models.md).

**The tiers**. The framework has three tiers: large, medium, and small. In the plan header, the small tier goes only to the executor. Write the tier in the plan header and in the handoff. Add the effort: `medium`, `high`, `xhigh`, or `max`. Only the tool modules say what each tier and effort mean, under "Models by role".

### Variants and the spec rest on verified facts

For a tool, a service, or a model from outside the framework, check its source before the variants: the documentation, the page, or the code. Write the fact in the spec, with its link and date. Check data from a service against its primary source too, for example a law.

For the framework, read from the repository, not from memory. Write an assumption that stays an assumption, with the check that would settle it.

Reason: execution follows the spec literally. A written assumption looks exactly like a verified fact.

### The spec and the plans are written in different sessions

Stop the spec session after the spec. Run `end-of-session` and hand over. The planning session is new, and it closes the same way. It may write all the plans or only some, if it hands over the rest.

Reason: the discussion in which the requirements were settled is the expensive part. The plans do not need it. Everything decided is already in the spec.

### The planning session writes the plan header

A plan is mechanical when each task has a command as its verifier, names the files it touches, and needs no decision.

When the human runs the plan by hand, choose `xhigh` for a plan with tasks to investigate. Choose `medium` for a purely mechanical plan. Never choose `max`.

Write `Closing: the human` when the plan touches services or hardware, deletes what cannot be recovered, or touches keys and access. Otherwise, write `Closing: the orchestrator`.

### The plan ships untested

Do not run the plan's code in the planning session. Probe only with a small command that checks that the tools and commands of the tasks exist. The executor repairs a mechanical mistake in the plan, such as a path, an anchor, or a letter, and writes the repair in its report. It does not repair a design decision.

Reason: checking the plan cost 81% of the planning sessions. Execution then ran the same code a second time.

### Commits carry the human's identity: a test identity lives only in a throwaway copy

Commit in the real repository without `-c user.name`. The global configuration of the human signs the commit. Only a commit in a throwaway copy, a `git worktree` in the temporary folder, may carry a test identity. Set that identity only with `git -c` on its own command, never with `git config`.

Reason: `git config`, run from a worktree, writes into `.git/config` of the real repository. From then on, the test identity signs every commit there.

### Only planned work is handed over

A plan stays in the folder of its work item, in the records of the repository it changes. A small repair without a plan is finished on the spot, by the session that decided on it.

### One subagent at a time, in the foreground, and only from the framework's agents

The framework's agents live in `agents/`. The module of the tool says which agent to use, and when. Start one agent at a time, and wait for its result. Do not start any other subagent.

Reason: on 10 September 2026, two agents started together reached the limit together, and neither returned anything.

### The branch enters `main` after the orchestrator's verdict

Execution works on the branch named in the plan header. The orchestrator merges it after its verdict. For `Closing: the human`, the merge waits for the human's yes.

### The local worker is used first, when one exists

A local worker exists only when `records/local-workers.md` lists at least one worker with measured numbers. Otherwise, execution stays in the session. Say once why.

- **The worker is a model of the framework, or of another tool**. For a model of the framework, read the bridge, the preparation, and the release of the machine from that file, which belongs to the human. The bridge to another tool is `bin/tool-bridge.sh`, which belongs to the framework. The command is in the `execute` skill.
- **Do not use a model without a row in the table**. A row without numbers shows an unmeasured model. Do not use it.
- **If the verifier is the human, do not delegate.**
- **At `Who`, mark a task for the bridge first when its `Verifier` is a command**. A task kept for the session states its reason openly. Examples: the model has no table row, the task does not fit the window, or the machine cannot start.
- **The bridge contract, for any tool:**

  | What it receives | What it returns |
  |---|---|
  | the target, the task, and the verification command | exit code 0 and a diff, only if the verifier passed |
  | — | exit code 1: refused. The task is done in the session |
  | — | exit code 2: does not fit the window. The task is done in the session |

Build the workers file with the `local-workers` skill.

Reason: without this rule, nobody used the local worker. Without the file, a session would search for a tool that does not exist.

### The bridge's verifier does not write to files with absolute paths

The bridge exits with 1 if, while the model works, a file with an absolute path changes. This holds for a file named in the verifier's command, and for a file in `bin/` of a parent folder. Keep the verifier's files in a copy or in the session's temporary folder, not in `/tmp`.

Reason: on 3 October 2026, the bridge refused four times in about 40 calls. Three refusals came from a `bin/` that another session changed. One came from a `/tmp` file of the verifier.

### An agent's report is not evidence

Read what changed from `git diff`. Check from the probes run here that it works. This rule holds for a local model too.

## Where the work is kept

### A project's work lives in the project's repository

Keep the work items, journal, pitfalls, decisions, and `STATE.md` of a project in the records of its repository. The records folder is `records/` in projects that start from the template, and `registre/` in older projects, as each project's rules say.

The root `records/` holds only the framework's own work items and the problems of the machine that belong to no project. The work index at the root mentions the work items of projects, with their paths written in prose and without a link.

Reason: sessions started from the root wrote project plans into the environment's records. Anyone who opened the project could not find them there.

### A planned work item has a folder

`<records>/work/open/<YYYY-MM-DD-subject>/` holds `README.md` for people, `request.md` with the human's words, the spec `<YYYY-MM-DD-subject>-design.md`, and the plans of the two planning sessions. The state of the repository's work items and the backlog of leftovers sit in the `INDEX.md` next to it.

### A work item closes only when every leftover has a destination

A destination is done, abandoned with the reason written, or queued in the backlog. `end-of-session` closes the item. It writes `closing.md` and moves the folder into `closed/`.

Reason: leftovers in closed plans never reached any destination.

### A decision that must hold goes into the decisions record

Write it in `records/decisions/` for the environment, or in the decisions folder of the project. Do not write it only in `STATE.md`, because `end-of-session` rewrites `STATE.md` at each session end.

## A project's session

### A project's session opens in the project's folder

Each tool sees a project's rules only when it starts from the project's folder. The module of each tool says how it loads the rest of the chain.

Reason: in sessions started from the root, a project's rules almost never entered the context. In sessions started from the project's folder, they entered every time.

### At closing, what was found climbs toward the root

Reading goes down the tree. `end-of-session` writes in reverse, from the deepest repository touched upward. Put each pitfall, decision, journal entry, or candidate for `AGENTS.md` at the first level that holds it whole: the sub-project, the project, or the framework.

Climb one level only if the item stays true without the name of the sub-project or the project.

Reason: written too high, it costs every session of every project. Written too low, nobody in another project finds it.

## The order of the skills

Process comes before implementation. The process skill sets the approach. The implementation skill carries it through.

| The situation | Skill |
|---|---|
| the spec of a work item is written | `spec` |
| something new is built, and the requirements are not settled | `superpowers:brainstorming` |
| the spec is approved, and the plans are written | `plans` |
| the requirements are settled, and the task has several steps | `superpowers:writing-plans` |
| the plans are written and must go to `main` | `orchestration` |
| the plan is written, and the executor, the escalation agent, or the human carries it out | `execute` |
| new code is written, or something is repaired | `superpowers:test-driven-development` |
| a defect, a failed test, or unexpected behavior | `superpowers:systematic-debugging` |
| before "done", "it works", or "it passes" | `superpowers:verification-before-completion` |
| feedback on code arrives | `superpowers:receiving-code-review` |
| values are verified, and writing follows | `documentation` |
| tests pass, and the branch needs a decision | `superpowers:finishing-a-development-branch` |
| the session closes, and its state must be written | `end-of-session` |

### `documentation` comes after verification and before integration

Invoke `documentation` **after** `verification-before-completion` and **before** `finishing-a-development-branch`.

Reason: the values in a reference must already be verified. The document goes into the same commit.

### Every skill invoked is announced

The announcement has the form `Using [skill] to [purpose]`. It is rule 2 of "The rules broken most often".

Reason: without the announcement, the skill was not applied.

## Writing

### Write per ASD-STE100, in chat and in files

The rule holds for answers, documents, rules, commits, and instructions given to agents. All English text follows the `asd-ste100` skill. Load it before you write a document.

In chat, without the skill loaded, keep this core:

1. Write one idea in each sentence.
2. Write at most 20 words in an instruction, and at most 25 words in a description.
3. Do not use semicolons.
4. Write an instruction in the imperative: "Read the journal index." Write a description in the third person.
5. Say who does the action. Use the passive voice only when the actor does not matter.
6. Use one word for one thing. The framework's terms are in the glossary.
7. Do not cut the subject or the verb to shorten a sentence.
8. Keep uncertainty. "It may have failed" does not become "it failed".
9. Write three steps or more as a numbered list.
10. Do not write marketing adjectives. Write the number.

Reason: the human read compressed text with difficulty. A weaker model understands a short sentence with one meaning more reliably.

### Tell the human what you did, what came out, and what comes next

After each step that matters, write one sentence: what you did, what came out, and what comes next. Explain the output of a command, with the numbers that matter. Put a command that the human runs in a `bash` block.

For a question with options, say what each option means, and what the human gains and risks with it. Put the recommended option first, and say why you recommend it.

Reason: the human leads without writing the code. The human cannot decide from output that nobody explained.

### `ponytail` governs the code, not the documentation

Under `docs/`, the explanation is the product. It is not an addition to the product.

## The state of the repository is read first

### Before reading any code, check the state of each repository touched

| What is asked | How |
|---|---|
| is there a repository? | `git -C <project> rev-parse --git-dir` |
| which branch is it on? | `git -C <project> branch --show-current` |
| how many commits ahead or behind origin? | `git -C <project> fetch --quiet && git -C <project> status -sb` |
| what is not committed? | `git -C <project> status --porcelain` |

Run `fetch` before the comparison. Without it, "up to date" means "up to date as of the last read". Before the first change in a repository, also read its `AGENTS.md` and `IMPACT.md`: the rules and the map.

### At the end of the session, commit and push in every repository touched

`end-of-session` commits and pushes in the project's repository and in the environment's repository. It reads the changes from git. It rewrites the `STATE.md` of each repository touched, and it proposes the missing record entries. It does not write `AGENTS.md`, modules, or `IMPACT.md` automatically. It reports what would be worth adding, and the human decides.

Reason: a commit left local is work that lives on one machine only.

### Commits carry no `Co-Authored-By`

Do not add `Co-Authored-By`, or any other trace of a tool or model, even when the application's instructions ask for it. The message is one sentence in the repository's language, without prefixes such as `docs:`. It says why, not what.

## Commands sent at the same time

### In a command sent in parallel, do not change the directory with `cd`

Write absolute paths, and use `git -C` for git. Send a command that writes (commit, move, or delete) on its own.

Reason: a neighboring command may run in the directory another command left behind, with no sign of it. The commit then lands in a different repository than the one named.

## Problems already solved

### Before a repair of the environment, read the journal index

Plugins, `node`, tools, machines: read the journal index in `records/journal/INDEX.md`. It is cheap, and it saves a second repair.

### Search for a repaired command across the whole repository

Before you call a repair finished, run `git grep` on a fragment of its old form. Search the same way for a moved record file across the whole workspace. The long reference of the `documentation` skill, `details.md`, says how.

### Check a changed tool in `bin/` with `check-maps.sh` too

Do not stop at the tool's own test. The impact maps of projects call the environment's tools. A stricter tool can break them without any change in the project.

Reason: the tool's test passes, and the failure appears only in another repository.

### Write every system repair in the journal, in the same session

Write a small repair in the journal too: a package, a driver, an environment setting, or a plugin. The entry has the symptom, the cause, and the method.

- The machine and its environment: write in `records/journal/`, with the machine named in the entry.
- A machine kept by a project, or a tool of a project installed here: write in that project's journal, which is in git.

Reason: a month later, nobody can reconstruct "I know I repaired something about this".

## Tools

### What belongs to one tool lives in its module

| Tool | Module | What it reads by itself |
|---|---|---|
| Claude Code | `CLAUDE.md` | `CLAUDE.md` and `AGENTS.md`, from the starting folder and its parents |
| Antigravity | `GEMINI.md` | `AGENTS.md` and `GEMINI.md` from the opened folder. What is above comes through local files |
| Mistral Vibe | `MISTRAL.md` | `AGENTS.md` from the opened folder and its parents, up to the root. The module and the house rules come through the global file |
| Codex, Cursor, Copilot, opencode, Amp, and the others | none yet | `AGENTS.md` |

A module starts with `@AGENTS.md`. It exists only where it has something to say, or where its tool could miss `AGENTS.md`. The module itself states its location. `check-docs.py` keeps the pairs.

Add a tool by following [the guide](docs/how-to/add-a-new-tool.md).

Reason: a rule written in two places diverges at the first change. Written once in `AGENTS.md`, it reaches all tools at once.

## Agent memory

### Write to memory what is worth keeping, one file per fact

Memory lives in `records/memory/`: one file per fact. Each file has the header fields `name`, `description`, and `metadata.type` (`user`, `feedback`, `project`, or `reference`). Each file also has one row in the `MEMORY.md` index.

Write to memory the way of working that the human wants, the human's corrections, and the context of work that the code does not show. Do not write what git or a record already holds. Before you write, search for the file that covers the fact. Make relative dates absolute.

Each tool receives memory as its module says, and it writes by this rule.

Reason: a preference stated to one tool must reach the other. Two separate memories would learn different things about the same human.

## The environment guide is portable

### `README.md` and `docs/` describe the environment for any machine

Do not write absolute paths, paths specific to one machine, calendar dates, user names, or repository and project names there. Call the location "the workspace root", and write paths relative to it. Write a number together with the command that measures it again.

### `records/` and `STATE.md` are records

In records, the date and the machine are the content itself, and they stay.

### A record is added to, not rewritten

Each entry is one file, dated in its name, and it stays untouched once written. Only the index of a record is rewritten. Under `records/` sit `journal/`, `pitfalls/`, `decisions/`, and `work/`. No documentation run touches them.

Reason: a record kept in a folder that is rewritten at each run grows to four thousand lines.

### The personal layer stays out of the framework's repository

`records/` is the clone of a private repository. It holds the records, the agent memory, and the local workers. `STATE.md` at the root describes one machine, so it stays out too. The journal does go into the personal layer. A repair from yesterday serves the next laptop as well, and without the repository it would die with this one.

Reason: the framework can be shared without sharing anyone's history. That history follows the human to another machine without the framework.

### No tracked file of the framework links into `records/`

Write the path in prose. Do not write a link into `records/`. The framework calls this rule its contract with the personal layer. The folder exists on the human's machine, so the link works there. On a fresh clone, the link breaks.

Reason: the mistake stays invisible on the very machine where it was made. `check-docs.py` prints it as `PERSONAL:` and fails.
