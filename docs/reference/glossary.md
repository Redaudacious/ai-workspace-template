# Glossary

The words that the workspace uses in a different way from everyday speech, or that the workspace invented. The first sentence of each entry is the **gloss**. The gloss is a short explanation. It is copied, in parentheses, at the first use of the word in any document. The rest of the entry gives the nuance. It says what the word means in this workspace.

## The framework and the projects

| The word | What it means |
|---|---|
| the workspace root | the folder into which the environment's repository was cloned. Paths in the documents start from it. |
| the framework | the repository with the rules, skills and tools that all projects share. Git tracks it at the root. `records/` and `projects/*` sit inside it, but git ignores them. |
| the template | the `template/` folder, from which a new project starts. It is copied whole. A project started from it has `records/`. An older project has `registre/` instead. |
| the example | a small project, carried whole from the request to `main`, then frozen. It sits in `example/`. It is a fabricated record, so its dates and names are allowed. |
| the personal layer | `records/`, the clone of a private repository of the human's, with the human's records. It also holds the agent's memory, the house rules and the local workers. The framework ignores it. So the framework can be shared without anybody's history. |
| the house rules | the rules that describe the human's place, not the framework. They cover the language, the machines and access to them, and the old names of renamed things. They sit in the personal layer. They would be false on another machine. |
| `AGENTS.md` | the file with the common rules. Every session loads it, in any tool. Loading it at the start costs tokens. So the file exists only when it has something to say. The module of each tool sits next to it. |
| module | the file with what belongs to a single tool. It is `CLAUDE.md` for Claude Code, `GEMINI.md` for Antigravity and `MISTRAL.md` for Mistral Vibe. It starts with `@AGENTS.md`, which imports the common rules. It holds the models by role, the loading of rules, and the skills and plugins of the tool. |
| tier | a level of model that the framework uses. Its name is neutral: large, medium or small. The small tier serves the executor on a mechanical plan, and the reader. The sessions that write the plan header and the handoff also write the tier, together with the effort. Each module says which model the tier means for its tool. |
| `CLAUDE.md` | the module of Claude Code. Without it, Claude Code would not read the neighboring `AGENTS.md`, because the root has a `CLAUDE.md`. |
| the chain of `CLAUDE.md` | all the `CLAUDE.md` and `AGENTS.md` files from the root down to the folder being read, with their imports. At startup, a session loads the files in its starting folder and in that folder's parents. Files in subfolders enter only with the first file read from there with the Read tool. `cat` never loads them. Antigravity uses the local files of the open folder instead. |
| reading goes down, writing climbs | the rules are read from the top down. Findings are written from the bottom up. At closing, each pitfall, decision or journal entry goes to the first level that contains it whole. That level is the game or domain, the project, or the framework. |

## The sessions and the handoff

| The word | What it means |
|---|---|
| the spec session | the session that talks with the human and writes the spec. It chooses the architecture. It does not write the plans. |
| the plans session | the new session that reads the spec and writes the plans. It also writes the `README.md` of the work item. It does not write the code. |
| the orchestration | the new session that takes the plans of a work item to `main`. It runs at the large tier with medium effort, using the `orchestration` skill. It gives each plan to the executor, checks it and merges it. It takes the place of a review. |
| the executor | the agent that carries a plan to the end. It runs at the medium tier with high effort, or at the small tier for a mechanical plan. The orchestrator starts it with the `execute` skill. It merges nothing into `main`. |
| the escalation | the agent that resumes a plan at the task that the executor did not pass. It runs at the large tier with medium effort. The orchestrator starts it. |
| manual execution | a plan that the human runs by hand, in a session the human opens. For example, in Antigravity, when the Claude limit is tight. The orchestrator checks it afterwards. |
| the verdict | the file in which the orchestrator writes what it checked in a plan and what it decided. It sits in the work item's folder, as `verdict-<plan>.md`. |
| the state file | `STATE.md`. It holds the state of the project and what comes next. It is rewritten at the end of each session. It holds the measured state, what does not work, and the handoff. |
| the handoff | the note in `STATE.md` for the next session. It names the tier, the effort, the plan, the branch and the prompt to paste. |
| the plan header | the first lines of a plan. They give the tier and who merges the work. There are four lines: `Execution` (the tier and the effort), `Closing`, `Branch` and `Criteria` (the criteria of the spec that the plan closes). |
| the `Who` label | the line that says who does a task in the plan. It names the session or the bridge, with the model and the verifier. |
| the closing | how the work of a plan reaches `main`. The orchestrator merges it after the verdict (`Closing: orchestrator`). Or it merges it after the verdict and the human's "yes" (`Closing: human`). |
| effort | how much thinking time the model gets. The levels are `medium`, `high`, `xhigh` and `max`. |
| verifier | the command that decides by itself whether a task succeeded. It exits with 0 if the task succeeded. It exits with any other code if it did not. |
| the test | a script that calls the code and checks the answer. The suite runs it at every push, as a verifier. |

## The local workers

| The word | What it means |
|---|---|
| local worker | a model that takes small tasks, each with a verifier. It runs on one of the human's machines. Or it is a model of the other tool, reached through the bridge between tools. |
| the worker's bridge | the tool that gives the task to the worker. It returns the diff only if the verifier passed. For in-house models it lives in the project that keeps the workers. For a model of the other tool it is `bin/tool-bridge.sh`. |
| `worker up`, `worker down` | the commands that prepare and release the worker's machine. They belong to the human, who writes them in the workers file. |
| subagent | another Claude, started from a session. The framework uses only its own agents, from `agents/`. It starts one at a time, in the foreground. |
| reader | the agent that reads long material. It returns only what was asked, with the source of each quote. It runs at the small tier with medium effort. It starts without the house rules. |
| compaction | the automatic summary of the old conversation. The summary takes the place of the conversation in the session. It starts at 400,000 tokens. The restore step sets that threshold. |

## The probe bench

| The word | What it means |
|---|---|
| the bench | the probe bench in `bin/bench/`. It gives the same task to any AI programming tool. It reads the tool's journal to check whether the tool worked by the house rules. It measures the tools and does not change them. The reference is Claude Code. |
| the miniature house | the copy of the workspace in which a bench probe runs, in a temporary folder. It holds the house rules, the records and the project of the task. It is removed when the run ends. |
| the simulated human | the model that answers in place of the human in a bench run. It is a model of the medium tier, with the task's `brief.md`. It chooses the recommended option, approves, and writes `DONE` when the tool finishes. |
| the adapter | the class through which the bench starts a tool, answers it and reads its steps. It is the only part that a new tool brings to the bench. |
| the threshold | the result of a run. A run passes when no required check failed. An informational check is reported, but it does not change the result. |
| the slip | the hook of Antigravity that slips Gemini a reminder after some tools. For example, it announces the skill just read. It sits in `bin/antigravity-memento.py`. |

## The records

| The word | What it means |
|---|---|
| record | a series of dated entries. Entries are appended, not rewritten. Only the index of a record is rewritten. |
| work item | a piece of work with a written spec and plan. |
| the work item's folder | the folder with the spec, the plans and the closing of the work item. It sits under `records/work/`. It holds `README.md`, the spec, the plans and `closing.md`. |
| the work index | one row per work item, with its state. It is the `INDEX.md` next to the folders. It also holds the backlog. |
| the spec | the document that decides what is done and how. It also gives the reasons, with the rejected alternatives. |
| the plan | the list of tasks. Each task has its own verifier. The executor runs the plan. Execution follows the plan and decides nothing. Each step has its own commands. |
| the backlog | what waits without a folder: leftovers, requests and defects found. It is a section of the work index. |
| leftover | a task not done in a work item. Or what the work item wrote under "What is not in this plan". |
| decision | a rule or a choice, dated. It has its reason and its history. It sits in `records/decisions/`. |
| pitfall | what cost time, with the method by which it was found. It sits in `records/pitfalls/`. |
| journal | the system problems solved, with the symptom, the cause and the method. The journal of the environment lives in the personal repository. The journal of a project lives in the project. |

## The documentation

| The word | What it means |
|---|---|
| the kinds of documentation | tutorial (learning), how-to guide (solving), reference (values) and explanation (reasons). It is the Diátaxis model, also called Divio. |
| the documentation map | the table in `README.md` that says where each thing is looked for. It has the columns "If… Then… Where". |
| the documents map | the `## Documents` section of `IMPACT.md`. It links each document to the code that it describes. |
| the impact map | `IMPACT.md`, the table of what breaks at each change, with the command that checks it. It has one row per thing touched. |
| the landmarks | the block of commands in `README.md` that prints the environment's numbers. The numbers are not written by hand. They are measured again. |
| failures | what `check-docs.py` reports as wrong. Zero failures is the only pass. |
| the values removed on purpose | the values of a rewritten document that are left out knowingly. Each one has a row, with the reason, in the file given to `values.py` with `--removed`. |
| skipped | a test that cannot run on this machine. It exits with 77. It is not counted as failed. |

## The plugins

| The word | What it means |
|---|---|
| skill | a set of instructions. It enters the conversation when the situation matches. It is announced with `Using [skill] to [purpose]`. |
| the marketplace | the repository from which a plugin is installed. Each plugin is pinned, with its URL and SHA, in `plugins.lock.json`. |
| superpowers | the plugin that decides the order of the work. It says which skill comes before which. |
| ponytail | the plugin that decides how much code is written. Its ladder first asks whether anything has to be written. |
| RTK | the tool that shortens the output of commands before it reaches the conversation. |

The reference for each plugin: [superpowers](superpowers.md), [ponytail](ponytail.md), [RTK](rtk.md).
