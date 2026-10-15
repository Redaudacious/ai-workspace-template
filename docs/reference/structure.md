# The structure of the workspace

This page describes each folder and file in the workspace root. The root is the folder into which the environment's repository was cloned. For each item, it says who reads it and what breaks without it.

Words with a meaning of their own here are glossed at first use. All of them are in the [glossary](glossary.md).

The numbers in this document are not dated. They can be measured again. The block in [README.md](../../README.md) prints all of them.

```
<workspace root>                ← the clone of the ai-workspace repository
├── AGENTS.md                   common rules for any tool, loaded automatically
├── CLAUDE.md                   Claude Code module: the import, then what is only its own
├── GEMINI.md                   Antigravity module: the import, then what is only its own
├── MISTRAL.md                  Mistral Vibe module: the import, then what is only its own
├── README.md                   the entry page
├── IMPACT.md                   what breaks if something is touched, with checkable commands
├── STATE.md                    the environment's state plus the next session's prompt — IGNORED
├── plugins.lock.json           the pinned versions of the plugins
├── .gitignore                  what stays out: projects/, records/, /STATE.md, local files
├── .claude/launch.json         the local server from which the diagrams are drawn
├── .claude/skills/welcome/     the welcome skill: Claude Code loads it before the restore
├── agents/                     the house agents: the executor, the escalation agent, the reader
├── bin/                        the tools: checking, restore, move, usage, diagrams
├── docs/                       the environment's documentation, after the Divio model
├── example/                    a whole work item, frozen after merge into main
├── mods/                       the application's modes, loaded in every session: the panel and the records guard
├── records/                    the personal layer: records, memory, house rules — IGNORED
├── skills/                     skills written here, not taken from plugins
├── template/                   what a new project starts from
├── tests/, test                the probes of the tools in bin/, and their runner
└── projects/                   one folder per project — IGNORED by git
```

The tracked repository is the framework. It holds the rules, skills, and tools that all projects share. `records/` and `projects/` sit in its folder. They are separate repositories, and the framework ignores them.

## The files at the root

| File | What it is | Who reads it |
|---|---|---|
| `AGENTS.md` | the common rules that every session loads, in any tool: the three sessions, the skill order, the modes, memory, and the routing to the journal | any tool, automatically: Claude Code through the setting that restore applies, Antigravity directly or through local files |
| `CLAUDE.md` | the Claude Code module: `@AGENTS.md` on the first line, then the role models, rule loading, skills, and plugins | Claude Code, automatically, in every session |
| `GEMINI.md` | the Antigravity module: `@AGENTS.md`, then its role models, rule loading, skills, and global mode rules | Antigravity, automatically, in every session |
| `MISTRAL.md` | the Mistral Vibe module: `@AGENTS.md`, then the role models with their profiles, thinking, the monthly quota, skills, and the house agents as separate runs | Vibe, through its global file, written by `bin/vibe.sh` |
| `README.md` | what the repository is, the map, and how to restore it on a new machine | a human who arrives here for the first time |
| `IMPACT.md` | the impact map. It is the table of what breaks at each change, with the command that checks it. Each row names a tool, a folder name, or the lockfile. The fourth column of each row is a command that exits with 0 while the row is true | `bin/check-maps.sh`, and anyone about to touch something |
| `STATE.md` | the state file: the project's state and what comes next, rewritten at the end of every session. It holds the measured state of the environment, what does not work, and the work of the next session. **Ignored by git**, local to each machine | the human and the agent, at the start of every session |
| `plugins.lock.json` | the marketplaces (the repositories from which plugins are installed) and the pinned plugins, each with a URL and a SHA | `bin/restore-env.sh` and `bin/check-lock.sh` |
| `.gitignore` | what stays out of the repository: `projects/`, `records/`, `/STATE.md`, `/CLAUDE.local.md`, and `/.agents/rules/framework-[0-9][0-9].md` | git |
| `.claude/launch.json` | the "diagrams" configuration: the local server on port 8766, from which `bin/diagrams.html` opens | the Claude application, when a preview starts |

`AGENTS.md` and the modules load by themselves. `README.md` does not. What must reach every session without anyone asking goes into `AGENTS.md`. It goes into a tool's module when it belongs to that tool only. That is why these files stay short. Every line in them costs at every session start.

`STATE.md` does not come with the clone. It is ignored, because it describes what was measured on **one** machine, today. It also describes what **one** human must do tomorrow. On a new machine, it is written at the end of the first session.

The rule belongs to the **environment**. A project's `STATE.md` goes into the project's own repository. `template/STATE.md` stays too, because it is a template.

⚠ **`STATE.md` is not allowed to grow.** What closes **leaves** it. System problems move to `records/journal/`. Decisions that need explaining move to `docs/explanation/`. Delete the rest, because git keeps it anyway. A state file that only grows is no longer read. Then it is no longer true, either.

## `bin/` — the tools

Fifteen scripts, a page, and the bench, `bench/`, described in [Bench](bench.md). The check and restore tools exit with 0 when the checked thing is in order. They exit with a non-zero code when it is not. So they can be chained with `&&`. `usage.py` measures, and `move-md.py` moves. Neither checks. `merge-claude-config.py` is not called by hand. Restore calls it.

| Tool | What it does | When it is run |
|---|---|---|
| `check-docs.py` | It checks the documentation of a tree: links, anchors, paths written in prose, the kind of each document, and the shape of the tree. It also checks the `AGENTS.md`–module pairs, and it reads `example/`, with its records. With `--criteria <folder>`, it only checks that each criterion of a work item's spec appears in a plan header. | after any writing in the documentation, or any move of a folder. With `--criteria`, when plans are reread and before orchestration |
| `values.py` | reports which command, path, or number disappeared from a set of documents, compared with a git revision. A value moved into another document is not a loss. | at every documentation rewrite, before the commit |
| `documents.py` | says which documents lag behind their code, after the `## Documents` map in `IMPACT.md`. With `--complete`, it checks the map itself. | after any code change. The guide: [How to keep the documentation current](../how-to/keep-documentation-current.md) |
| `diagrams.html` | draws every Mermaid diagram in a document, and reports which ones do not draw. It is a page, not a script. | after a diagram is written or changed, opened in the application's browser |
| `check-maps.sh` | runs the commands in the fourth column of every `IMPACT.md` under the root. A command that exits with 77 is skipped, not failed. | after any code change that could invalidate a map |
| `check-lock.sh` | checks, **without network access**, that every SHA in the lockfile exists in the repository the lockfile names. | at the start of a session, and after any plugin update |
| `make-lock.py` | regenerates `plugins.lock.json` from the current installation. | after a plugin is installed or updated |
| `restore-env.sh` | restores the environment on a new machine from the lockfile. It **merges** the three files in `~/.claude/` and does not rewrite them. It builds the skeleton of the personal layer when `records/` is missing. It links agent memory for the root and for each project. | once, on a clean machine, and after every new project |
| `antigravity.sh` | links Antigravity to the workspace: the skills into `~/.gemini/config/skills/`, the global mode rules, and the local files of each repository and rule folder. With `update`, it downloads the latest application version. | from `restore-env.sh`, and by itself after a new project. `update`, whenever the human wants it |
| `vibe.sh` | links Mistral Vibe to the workspace, in `~/.vibe/`: the global rules file, the models from `config.toml`, the trusted root, the role profiles, and the skills. | from `restore-env.sh`, and by itself after a change in `MISTRAL.md`, in the house rules, or in memory |
| `tool-bridge.sh` | gives a task with a checker to a model of the other tool (`agy`, `claude`, or `vibe`), in a separate working copy. It returns the diff only if the checker passes. Its exit codes are 0, 1, and 2. | during execution, for a task marked `Who: bridge`, with the worker in the other tool |
| `merge-claude-config.py` | merges `settings.json`, `known_marketplaces.json`, and `installed_plugins.json` in `~/.claude/` with what the lockfile requires. It changes only the keys the lockfile requires. It also puts the modes from `mods/` into `CLAUDE_CODE_PLUGIN_DIRS`, so they load in every session. | from `restore-env.sh`, at every restore |
| `usage.py` | counts each session from the local Claude Code logs at the API price. It shows where the tokens went: the conversation re-read, the cache writing, and the output. With `--vibe-sessions`, it counts the Mistral Vibe sessions of a month, at the prices in `~/.vibe/config.toml`. With `--state`, it gives the application panel the state of each chat: working, warm, or cold. It also writes the 7-day window file. With `--proof`, it shows the proof of one chat. With `--work`, it shows the cost of a work item. With `--windows`, it shows the windows side by side. With `--agent`, it shows the cost of an agent. | after a handoff between models, to see whether it paid off. `--state` runs from the panel every 10 seconds |
| `reminder.py` | writes the reminder at the end of each response, in Claude Code and in Vibe. It catches three slips: a role without its skill, a skill without an announcement, and a write or commit without a percentage. | the `Stop` hook of Claude Code and the `post_agent` hook of Vibe, set by restore |
| `antigravity-memento.py` | the memento: the Antigravity hook that slips Gemini a reminder after some tools | the `PreInvocation` hook, linked by `antigravity.sh` |
| `move-md.py` | moves a file or a folder with `git mv`, and rewrites the markdown links that leave it or point to it. | when a record is moved, and when a work item is closed |

"Skipped" is a test that cannot run on this machine. It exits with 77, and it is not counted as failed. "The handoff", in the row of `usage.py`, is the note in `STATE.md` for the next session.

⚠ **`check-docs.py` receives a root, not a pattern.** Given a project root, it reads the top-level documents, plus everything under **its** `docs/`. Given a `docs/` tree itself, it has a third term reserved for that case.

Without that third term, the check would have passed after reading **a single** file in the whole tree. This happened.

It reads its own `docs/`, not the `docs/` of the projects inside. Otherwise, "the environment is clean" would be a claim about another tree. Each project is checked with its own root.

`STATE.md` is not checked for reachability. Git ignores it. A link to it would break on a fresh clone. A `README.md` that links to it would be wrong. The map names it without linking to it, on purpose.

The links **from** it are still checked. They form the prompt for the next session. A broken link there costs a session.

`check-maps.sh` uses `eval`. That fits here, because the commands come from files in the repository. It would not fit if the source came from outside. A literal `|` in a command is written `\|`, as the markdown table requires anyway. The tool hides it before it splits the columns.

⚠ **`make-lock.py` must find out in which repository each plugin lives.** The answer is not uniform. In `marketplace.json`, `source: "./"` means that the plugin **is** the marketplace repository. `source: {"source": "url", …}` means a separate repository.

Both forms appear in the current installation. So a script that searches for the SHA only in the marketplace repository succeeds for some plugins, and it seems to work.

`restore-env.sh` clones over HTTPS, not SSH. Remotes configured locally may use SSH. On a machine without a key in `ssh-agent`, those remotes fail. The authentication error looks nothing like the real cause.

## `tests/` — the tests

A test is a script that calls the code and checks the answer. The form of the tests is a convention of the **framework**, not of the human. It lived only in the agent's memory, on one machine, until it was brought in here.

- The tests sit in a tree: `tests/` at the root, and `<domain>/tests/` in a project with domains.
- The collector is `./test`. There is exactly one per repository, with no list of skipped tests.
- Discovery uses the executable bit, not the extension. Each test's shebang says how it runs.
- A test that cannot run on this machine defends itself. It exits with code **77**, and it is counted as skipped, not failed. Both `./test` and `check-maps.sh` count it this way. This applies when the test is the command of a row in `IMPACT.md`.
- The verdict is the exit code, not the last line printed.

## `docs/` — the environment's documentation

The environment's documentation follows the Divio model. The table of contents, and the difference between the four kinds, are in [docs/README.md](../README.md).

| Folder | What it contains |
|---|---|
| `tutorial/` | a single document: the complete cycle of a project, with all the plugins |
| `how-to/` | one guide per question, each answering only one question |
| `reference/` | this structure, the glossary, the bench, one reference per tool (Antigravity, Mistral Vibe), and one per installed plugin |
| `explanation/` | why it is made this way: what each plugin does, how it triggers, and what breaks when two overlap |

## `example/` — a work item carried to the end

The example is the tutorial's project, `greeting.sh`. It is carried from request to `main` and then frozen. It holds every file of the work item, in the exact form that the sessions and agents leave it. The story, with each handoff quoted, is in [example/README.md](../../example/README.md).

It may carry dates, although git tracks it. It is a fabricated record, not documentation. The `records/` folder under it belongs to the example, not to the personal layer.

Who checks it: `check-docs.py` reads it whole. `./test` runs its test. `check-maps.sh` runs its map. `tests/test-example.py` reads its forms from the skills.

## `records/` — the personal layer

The personal layer is `records/`. It is a clone of the human's private repository, with their records. The framework repository ignores it. It holds the human's records, the agent's memory, and the house rules. The house rules describe the human's place, not the framework. They describe a human and their machines, not the framework.

| Record | What it holds | The index |
|---|---|---|
| `journal/` | the problems of the laptop and of the environment, with the machine written in each entry | `INDEX.md`, in the personal repository |
| `pitfalls/` | the code pitfalls, with the method by which each was caught | `INDEX.md`, in the personal repository |
| `decisions/` | the decisions, with the reason, the history, and the rejected alternatives | `INDEX.md`, in the personal repository |
| `work/` | the work items with a plan, each in a folder | `INDEX.md`, in the personal repository: the state of all, and the backlog |
| `usage/` | the 7-day windows, one file per reset day, in `usage/weeks/`. `bin/usage.py --state` writes them | — |
| `memory/` | the agent's memory, linked from `~/.claude/projects/.../memory` | — |
| `house-rules.md` | the language, the machines of the house, access to them, and the map of template names. It loads as a user rule, `~/.claude/rules/house-rules.md`, in Claude Code, and through local files in Antigravity | — |
| `template-names.md` | the map of names in the template: what the files, commands, and words are called here, and what they are called in `ai-workspace-template`. Read it when the template is synchronized | — |
| `local-workers.md` | the machines, the access, the bridge, and the table of measured workers | — |

A record is a series of dated entries. Entries are appended, not rewritten: one file per entry, dated in its name, and untouched after it is written. Only the index is rewritten. The index is the map. The entries are the facts.

In `local-workers.md`, a local worker is a model that runs on one of the human's machines and receives small tasks. The bridge is the tool that gives the worker its task. It returns the diff only if the checker passed.

`journal/` goes into the personal repository, with the machine written in each entry. A fix from yesterday is useful on the next laptop too. Kept only locally, it would die with this one. Only `STATE.md` stays local.

A project in `projects/` keeps its records in its own repository, tracked by git. The records belong to the project, not to one particular human. They are `records/` for projects started from the template, and `registre/` for the older ones. A project's work item, journal, pitfalls, and `STATE.md` sit there, not here. Only the framework's files sit here.

No tracked file of the framework links into `records/`. A path written in prose is how the framework names its contract with the personal layer. A link would resolve on today's machine, but it would break on a fresh clone, where the folder is missing. `bin/check-docs.py` catches it and prints `PERSONAL:`.

`bin/check-docs.py` enters `records/` only for links and for the history of entries. It checks the file and the anchor of every link there. It does not check repetition, size, kind, or reachability. A journal entry, pitfall, or decision fails if its text changes after the commit that created it. The links are ignored. The tool prints `RECORD:`.

An entry may be long, and it may repeat a phrase from an older entry. That is what a record does. But a broken link in an entry costs a session, because that is where someone looks up what has already been hit.

### `records/journal/` — the system problems

These are problems of the **environment** and of the laptop: plugins, `node`, and tools. They are not problems of one project. A machine kept by a project has its history in the project's journal, which is in git. The code pitfalls sit in `records/pitfalls/`.

File names have the form `YYYY-MM-DD-subject.md`, with the date first. Alphabetical order is then also chronological. No one has to keep a date field up to date by hand.

Read the index first. It is `records/journal/INDEX.md`. Without it, finding an already solved problem means a `grep` through the whole folder.

How to write an entry: [How to solve an environment problem](../how-to/fix-an-environment-problem.md).

### `records/work/` — the work items

A work item with a plan has one folder. The folder holds its spec, its plan, and its closing. It is not two files in two folders. The folder is `open/<YYYY-MM-DD-subject>/` while the item is open, and `closed/` after it is closed. The file formats are in the `documentation` skill.

| The file | What it answers |
|---|---|
| `README.md` | what is pursued and why, in plain terms, for humans |
| the spec, `<folder>-design.md` | **what** is done and **why**, with the rejected alternatives |
| the plan, one or more | **in what order**, with a check command at each step |
| `closing.md` | what came out, and where each leftover went |

`INDEX.md`, the work index, keeps the state of all work items. It lists the items in progress, the items not started, the backlog, and the closed items. The backlog holds what waits without a folder: leftovers, requests, and defects found.

⚠ **A plan without a spec is a list of intentions.** The spec is where the rejected alternatives are written. Without it, the first session that hits a decision thinks it found a loophole, and it "fixes" the decision back.

A plan step closes with a command that exits with 0, not with a claim.

⚠ **A work item is closed only when every leftover has a destination.** A leftover is a task not done from a work item. Without a destination, it stays in a plan that nobody opens anymore.

### `records/decisions/` — the decisions

Each decision has its own file. The file holds the rule or the choice, who asked for it, why, the history, and the rejected alternatives. The rule itself sits in `AGENTS.md`, in a module, or in its skill. The decision record explains why the rule is that way. A changed decision gets a new entry.

## `skills/` — the skills written here

The skills here are written in the framework, not taken from plugins. Each one loads when its situation comes up. These skills live in the repository. They are symlinked into `~/.claude/skills/`, where Claude Code looks for them. `bin/restore-env.sh` makes the link, so the skills appear on a new machine by themselves.

| Skill | What it does | When it is invoked |
|---|---|---|
| `documentation` | the five kinds of document, the rule for when documentation already exists, and what is never written | before writing or rewriting documentation |
| `end-of-session` | reads from git what changed, rewrites `STATE.md`, and proposes the record entries that are missing | at the close of a session, or by typing `/end-of-session` |
| `spec` | talks with the human and writes the spec of a work item, with the rejected alternatives | in the spec session, or by typing `/spec` |
| `plans` | reads the spec, and writes the plans and the `README.md` of the folder, without checking them | in the plans session, or by typing `/plans` |
| `orchestration` | hands plans one by one to the executor, checks them, and merges them into `main` | in the orchestration session, or by typing `/orchestration` |
| `execute` | carries a written plan to the end: the plan header, the local worker, the mechanical fixes, and the stop rules | loaded by the executor and the escalation agent. In a manual run, by typing `/execute` |
| `asd-ste100` | writing per ASD-STE100, in English, with `skills/asd-ste100/scripts/ste-lint.py`. It is a copy of the upstream skill, and `SOURCE` names the repository and the commit copied | before any English text of the framework |
| `local-workers` | how `records/local-workers.md` is built and kept up to date: which machines, which numbers, and the bridge contract | when the human has models or tools on their machines, or by typing `/local-workers` |

The seven skills written here have a length threshold: under 150 lines. A `SKILL.md` is read at every invocation, so every line costs every time. What is read only once goes into `references/`. Seven rows in `IMPACT.md` check the threshold, so it cannot break silently. The `asd-ste100` copy has no threshold: it is copied again from its source.

⚠ **The source is a single one, and it is the one in the repository.** A second copy once existed in a project. It fell 70 lines behind, and it told nobody. A copy of a skill never says that it is old.

The skill loader follows symlinks. This was checked, not assumed: the linked skill appears in the session's list. So the link holds, and there is no need for a copy plus a `diff` to compare them.

## `agents/` — the house agents

The house agents are other Claude sessions. Each one is started by a session, and it runs on its own model. They are `executor`, `escalation`, and `reader`, and `CLAUDE.md` describes them. `bin/restore-env.sh` links them into `~/.claude/agents/`.

## `template/` — what a new project starts from

The template is the `template/` folder, from which a new project starts. It is copied over the folder of a new project, and the placeholders in it are filled in.

```
template/
├── AGENTS.md               the rules specific to the project, if it has any
├── CLAUDE.md               only their import, @AGENTS.md
├── README.md               the entry page, with the documentation map
├── IMPACT.md               the impact map, with checkable commands
├── STATE.md                the state plus the next session's prompt
├── .gitignore
├── docs/
│   ├── README.md           the table of contents, with the difference between the kinds
│   └── tutorial/ how-to/ reference/ explanation/    (with .gitkeep)
└── records/
    └── pitfalls/ journal/ decisions/ work/    one INDEX.md each, with no entries
```

Who reads each top-level file, and what they look for in it:

| Document | For whom | What it answers |
|---|---|---|
| `README.md` | a human who decides whether the project interests them | what it is, what it does, and where to start |
| `AGENTS.md` | the session that has just started, in any tool | what breaks the project if not known: its commands, what is source and what is a copy, and the order in which code is read |
| `IMPACT.md` | whoever is about to touch something | what breaks if you change X, with a command that can prove it |
| `STATE.md` | the next session | the measured state, what does not work, and what is done next |
| `records/` | whoever runs into a problem that seems familiar | what happened before, with the date next to it |

The `AGENTS.md` and `CLAUDE.md` pair is the only optional one. That is a rule, not an oversight. Both load at every session start. A file with empty sections costs at every session start, and it gives nothing in return.

The template ships these files as a list of questions. That way, the answer "none applies here" leads to a deleted file, not to an empty one.

The rows that point to `IMPACT.md` and `STATE.md` stay in the map of `README.md`. A project that deletes them leaves its agent files unmentioned on the first page. Whoever opens the project then searches the folder for them. That is exactly the case the rule came out of.

How it is used: [How to start a new project](../how-to/start-a-new-project.md).

## `projects/` — the projects

Each project has one folder, and each folder has its own repository. This folder is the only entry in `.gitignore`, so nothing in it reaches the environment's repository.

How to make a new one: [How to start a new project](../how-to/start-a-new-project.md).

A repository's name is not necessarily the name of its folder. A project renamed locally may push to a repository with the old name. Renaming the repository breaks existing clones. Read which repository each project has from the source, not from a list kept by hand:

```bash
for p in projects/*/; do
  if [ "$(git -C "$p" rev-parse --show-toplevel 2>/dev/null)" = "$(cd "$p" && pwd -P)" ]; then
    printf '%-26s %s\n' "$(basename "$p")" "$(git -C "$p" remote get-url origin 2>/dev/null || echo 'no remote')"
  else
    printf '%-26s %s\n' "$(basename "$p")" 'NOT A REPOSITORY'
  fi
done
```

⚠ **A folder without its own repository gives no error. It gives the environment's remote instead.** `git -C` climbs from parent to parent until it finds a repository. `projects/` sits inside the environment's clone. That is why the loop first compares the root that git found with the folder itself.

The comparison uses `pwd -P`. Git returns the path without symlinks. With a plain `pwd`, a real project opened through a link would appear as "NOT A REPOSITORY".

⚠ **`projects/` is ignored, so `grep` in a session skips it.** The shell function respects `.gitignore`. A search that must cover the projects too uses `/usr/bin/grep`.

⚠ **A session for a project is opened in its folder.** At start, Claude Code loads the `CLAUDE.md` and `AGENTS.md` of the starting folder. It also loads those of its parents.

It loads the ones in subfolders at the first file read from there, with the Read tool. The whole chain of rules comes in, from the root down to the folder being read. `cat` brings nothing.

Antigravity does not look above the opened folder. Parent rules, house rules, and the memory index reach it through `.agents/rules/framework-NN.md` files. `bin/antigravity.sh` writes these files into each repository and rule folder, and git keeps them out.

The agent's memory is also kept per starting folder. That is why restore links it for each project from the same `records/memory`.

## What is not in the repository

Keys, tokens, databases, and `.env` files are not ignored. They are not in the folder at all. They live next to the services that use them, on those services' machines.

The plugins are not here either. They are tens of megabytes of foreign code. The lockfile does the same job with a few kilobytes. Restoring from an empty `HOME` exits with 0.
