# The documentation of the working environment

This documentation covers two things. The first is **the workspace**: the folders, the tools, and the flows used to start a project or fix a problem. The second is **the three plugins** pinned in `plugins.lock.json`: superpowers, ponytail, and RTK.

The plugins do not do the same thing, although all of them promise "less". They touch three different layers of the same conversation. Superpowers sets **the order of the work**. Ponytail sets **how much code gets written**. RTK sets **how much command output reaches the conversation**. Because they work on different layers, you can use them together and none of them cancels another.

The root [README.md](../README.md) describes what the repository is, and how to restore it on a new machine.

The documentation is split into four kinds of text, each with a different purpose. A document that tries to serve all four is good at none of them.

| Kind | What the reader looks for | Folder |
|---|---|---|
| Tutorial | learning the flow from scratch | `tutorial/` |
| How-to guide | solving one specific problem | `how-to/` |
| Reference | an exact value, a command, a cost | `reference/` |
| Explanation | the reason behind a decision | `explanation/` |

## Tutorial

Read it once, in order, with your hands on the keyboard.

- [The first work item, through the three sessions](tutorial/first-work-item.md) — a small work item, from request to closing. It covers the spec (the document that decides what gets done and how), the plans, and the orchestration, with the executor.

## How-to guides

Each one answers a single question.

- [How to write a task for someone else to execute](how-to/write-a-task-for-someone-else.md) — the five parts of an instruction, and the check on return. It covers a plan and the bridge, the tool that gives the task to the worker. The bridge returns the diff only if the verifier passed.
- [How to start a new project](how-to/start-a-new-project.md) — from an empty folder to a repository on GitHub, with startup prompts.
- [How to solve an environment problem](how-to/fix-an-environment-problem.md) — from symptom to cause, and how the problem enters the journal. The journal lists the solved system problems, with their symptom, cause, and method.
- [How to load the skills at the start of a session](how-to/load-skills-at-startup.md) — through `AGENTS.md`. That file holds the shared rules, and every session loads it in any tool. Or load the skills through a file reference, or through a reference to `AGENTS.md` from outside the folder.
- [How to trigger a skill from a prompt](how-to/trigger-a-skill-from-a-prompt.md) — the wordings that load each superpowers skill, and the wordings that load nothing.
- [How to switch modes](how-to/switch-modes.md) — the ponytail levels, within a session and permanently.
- [How to check that a plugin really works](how-to/check-a-plugin-works.md) — seven checks, from the cheapest to the slowest.
- [How to add a new tool](how-to/add-a-new-tool.md) — the five questions for an AI coding tool, and what changes after each answer.
- [How to keep the documentation current](how-to/keep-documentation-current.md) — how to write a row of the documents map, and what to do when `documents.py` lists a document.

## Reference

Exact values, read from the system and not from memory. None carries a date. The plugin values belong to the versions pinned in `plugins.lock.json`, and the block in [README.md](../README.md) measures the environment values again.

⚠ When you update a plugin, re-read the values in the three references from disk. The command `ls ~/.claude/plugins/cache/` shows the exact path.

- [The structure of the workspace](reference/structure.md) — every folder and every file: what it is, who reads it, and what breaks without it.
- [Glossary](reference/glossary.md) — the words that the workspace uses in a different sense, each with its gloss.
- [superpowers](reference/superpowers.md) — 14 skills, no slash commands, and the cost of each.
- [ponytail](reference/ponytail.md) — the seven-rung ladder, the 6 commands, and the declared measurements.
- [RTK](reference/rtk.md) — the 43 compressed programs and the list of exclusions.
- [Antigravity](reference/antigravity.md) — what gets installed, where it keeps its files, how to update it, and what was tested.
- [Mistral Vibe](reference/vibe.md) — what gets installed, where it keeps its files, how to update it, what was tested, and the limits that matter.
- [Bench](reference/bench.md) — the commands, exit codes, tasks, checks, and the adapter of a tool.

## Explanation

Read these away from the computer.

- [What each plugin does and when it is worth it](explanation/what-each-plugin-does.md) — the three layers, and the best and the worst case for each.
- [How a plugin starts to apply](explanation/how-a-plugin-applies.md) — the three mechanisms, and why the descriptions do not say what the skill does.
- [Splitting the work across models](explanation/splitting-work-across-models.md) — why a work item with a plan uses three sessions and an executor, on different models. It also shows where the line falls.
- [Conflicts and pitfalls](explanation/conflicts-and-pitfalls.md) — five pitfalls, each with the method that caught it.

## Where to start

There is only one starting path. See "The documentation map" in [README.md](../README.md).

## The plugins' numbers and paths

| Landmark | Value |
|---|---|
| Installed plugins | 3, all in the `user` scope |
| The configuration | `~/.claude/settings.json` |
| The plugins' files | `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` |
| The binary that manages them | `claude` from `PATH`. Otherwise, use the one in the app, `~/.config/Claude/claude-code/<version>/claude`, at the newest version |
| Permanent cost, total | ~1,272 tokens in every session |
| Slash commands available | 7 (ponytail 6, RTK 1, superpowers none) |
| Skills available | 21 (superpowers 14, ponytail 6, RTK 1) |

The list of what must be installed, with each version and the command that reads it, is in one place: [Quick start](../README.md#what-to-install), in the README.

## What is not here

This documentation describes the plugins as read from disk. It does not describe the features that their repositories promise for other tools, such as Codex, Gemini, and Copilot. Those features do not apply here. It also does not reproduce measurements that it cannot check. Where a figure comes from an author's documentation and not from the system, this documentation names the source.
