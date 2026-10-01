# Glossary

The words the workspace uses differently from ordinary speech, or has invented. The
first sentence of each entry is the **gloss**: the short explanation copied, in
parentheses, at the first use of the word in any document. After it comes the nuance,
that is what exactly the word means here.

## The framework and the projects

| The word | What it means |
|---|---|
| the workspace root | the folder into which the environment's repository was cloned. The paths in the documents start from it. |
| the framework | the repository with the rules, skills and tools common to all projects. It is tracked in git at the root; `records/` and `projects/*` sit inside it, but are ignored. |
| the template | the `template/` folder, from which a new project starts. It is copied whole; a project started from it has `records/`. |
| the example | a small project, carried whole through the four sessions and frozen. It sits in `example/`; it is a fabricated record, so the dates and names in it are allowed. |
| the personal layer | `records/`, the clone of a private repository of the human's, with their records. It also holds the agent's memory, the house rules and the local workers; the framework ignores it, so that it can be handed to someone else without somebody's history. |
| the house rules | the rules that describe the human's place, not the framework. The language, the machines and the access to them, the old names of renamed things; they sit in the personal layer, in `records/house-rules.md`, and would be false on another machine. |
| `AGENTS.md` | the file with the common rules, which every session loads in any tool. It is paid for at every launch, so it exists only when it has something to say; next to it sits each tool's module. |
| module | the file for what belongs to a single tool: `CLAUDE.md` for Claude Code, `GEMINI.md` for Antigravity. It begins with `@AGENTS.md`, the import of the common rules, and holds the models by role, rule loading, and the tool's skills and plugins. |
| tier | the name of a model level from the plan header: "Opus", the heavy tier, and "Sonnet", the execution tier. Each module says what model that tier means for it. |
| `CLAUDE.md` | Claude Code's module. Without it, Claude Code would not read the neighbouring `AGENTS.md`, because the root has a `CLAUDE.md`. |
| the chain of `CLAUDE.md` | all the `CLAUDE.md` and `AGENTS.md` files from the root down to the folder being read, with their imports. At launch, those in the starting folder and in its parents load; those in subfolders enter only with the first file read from there with the Read tool. `cat` never brings them. Antigravity instead uses the local files of the open folder. |
| reading goes down, writing climbs | the rules are read from the top down, and what was found is written from the bottom up. At closing, every pitfall, decision or journal entry is written at the first level that contains it whole: the sub-project or the domain, the project, or the framework. |

## The sessions and the handoff

| The word | What it means |
|---|---|
| the spec session | the session that talks with the human and writes the spec. It picks the architecture; it does not write the plans. |
| the plans session | the new session that reads the spec and writes the plans. It also writes the work item's `README.md`; it does not write the code. |
| execution session | the new session that carries a plan to the end. It runs on a cheaper model, with the `execute` skill. |
| review session | the new session that reads what execution did and decides on the merge. It reads the execution report, the plan and the branch diff. |
| the state file | `STATE.md`, the project's state and what comes next, rewritten at every end of session. It has the measured state, what does not work and the handoff. |
| the handoff | the note in `STATE.md` for the next session. It says the model, the effort, the plan, the branch and the prompt to paste. |
| the plan header | the first lines of a plan, with the model and who merges the work. There are three: `Execution` (the model and the effort), `Closing`, `Branch`. |
| the `Who` label | the line that says who does a task in the plan. The session, or the bridge, with the model and the verifier. |
| the closing | the way a plan's work reaches `main`. The execution alone (`Closing: Sonnet`) or a review (`Closing: Opus review`). |
| effort | how much thinking time the model is given. The steps: `medium`, `high`, `xhigh`, `max`. |
| verifier | the command that says by itself whether a task succeeded. It exits with 0 or it does not. |
| the test | a script that calls the code and checks the answer. It is the verifier the suite runs at every push. |

## The local workers

| The word | What it means |
|---|---|
| local worker | a model that takes small tasks, each with a verifier: a house model, on one of the human's machines, or a model of the other tool, through the tool bridge. |
| the worker's bridge | the tool that gives the worker the task and returns the diff only if the verifier passed. For in-house models it lives in the project that keeps the workers; for the other tool's model it is `bin/tool-bridge.sh`. |
| the prepare and release commands | the commands that prepare and release the worker's machine. They are the human's, written in the workers file. |
| subagent | another Claude, started from a session. The workspace does not use subagents. |

## The records

| The word | What it means |
|---|---|
| record | a series of dated entries, which are appended and not rewritten. Only its index is rewritten. |
| work item | a piece of work with a written spec and plan. |
| the work item's folder | the folder with its spec, plan and closing. It sits under `records/work/`, with `README.md`, the spec, the plans and `closing.md`. |
| the work index | one row per work item, with its state. It is the `INDEX.md` next to the folders and also holds the backlog. |
| the spec | the document that decides what is done and how. It also has the why, with the rejected alternatives. |
| the plan | the list of tasks, each with its verifier, that another session executes. Execution follows it without deciding anything; every step has its commands. |
| the backlog | what waits without a folder: leftovers, requests, defects found. It is a section of the work index. |
| leftover | a task not done from a work item. Or what was written under "What is not in this plan". |
| decision | a rule or a choice, dated, with its reason and its history. It sits in `records/decisions/`. |
| pitfall | what cost time, with the method by which it was found. It sits in `records/pitfalls/`. |
| journal | the system problems solved, with the symptom, the cause and the method. The laptop's lives in the personal repository, a project's in the project. |

## The documentation

| The word | What it means |
|---|---|
| the kinds of documentation | tutorial (learning), how-to guide (solving), reference (values), explanation (reasons). It is the Diátaxis model, also called Divio. |
| the documentation map | the table in `README.md` that says where each thing is looked for. It has the columns "If… Then… Where". |
| the impact map | `IMPACT.md`, the table of what breaks at each change, with the command that checks it. One row per thing touched. |
| the landmarks | the block of commands in `README.md` that prints the environment's numbers. The numbers are not written by hand, they are re-measured. |
| failures | what `check-docs.py` reports as wrong. Zero failures is the only pass. |
| the values removed on purpose | the values of a rewritten document that are missing knowingly. Each has a row, with the reason, in the file given to `values.py` with `--removed`. |
| skipped | a test that cannot run on this machine. It exits with 77 and is not counted as failed. |

## The plugins

| The word | What it means |
|---|---|
| skill | a set of instructions that enters the conversation when the situation matches. It is announced with `Using [skill] to [purpose]`. |
| the marketplace | the repository from which a plugin is installed. Each one is pinned, with URL and SHA, in `plugins.lock.json`. |
| superpowers | the plugin that decides the order of the work. It says which skill comes before which. |
| ponytail | the plugin that decides how much code is written. Its ladder first asks whether anything has to be written. |
| caveman | the plugin that compresses the model's answers. It is stopped with `/caveman off` before documentation. |
| `caveman off` | the mode in which the model explains for someone outside the field. More than whole sentences: comparisons, numbers with their meaning, the decisions stated openly. |
| RTK | the tool that shortens the output of commands before it reaches the conversation. |

The reference of each plugin: [superpowers](superpowers.md), [ponytail](ponytail.md),
[caveman](caveman.md), [RTK](rtk.md).
