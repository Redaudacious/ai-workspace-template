# The documentation of the working environment

This documentation covers two things: **the workspace** — the folders, tools, and flows
used to start a project or fix an issue — and **the four plugins** pinned in
`plugins.lock.json`: superpowers, ponytail, caveman, and RTK.

The plugins do not do the same thing, though all promise "less". They touch four
distinct layers of the conversation: superpowers sets **the order of the work**,
ponytail **how much code is written**, caveman **how the answer is worded**, and RTK
**how much command output enters the conversation**. None cancels out another.

What the repository itself is and how to restore it on a new machine is described in the
root [README.md](../README.md).

The documentation is split into four kinds of text, each serving a distinct purpose. A
document that tries to serve all four succeeds at none.

| Kind | What is looked for | Folder |
|---|---|---|
| Tutorial | learning the flow from scratch | `tutorial/` |
| How-to guide | solving a specific problem | `how-to/` |
| Reference | an exact value, a command, a cost | `reference/` |
| Explanation | the reason behind a decision | `explanation/` |

## Tutorial

Read once, in order, with hands on the keyboard.

- [The first work item, through the four sessions](tutorial/first-work-item.md) — a small work item, from request to closing: the spec (the document that decides what is done and how), the plans, execution, and review

## How-to guides

Each answers a single question.

- [How to write a task for someone else to execute](how-to/write-a-task-for-someone-else.md) — the five parts of the instruction and verification on return, for a plan or for the bridge (the tool that gives the worker the task and returns the diff only if the verifier passed)
- [How to start a new project](how-to/start-a-new-project.md) — from an empty folder to a repository on GitHub, with startup prompts
- [How to solve an environment problem](how-to/fix-an-environment-problem.md) — from symptom to cause, and how it enters the journal (the system problems solved, with the symptom, the cause and the method)
- [How to load skills at the start of a session](how-to/load-skills-at-startup.md) — through `AGENTS.md` (the shared rules file loaded by every session in any tool), through a file reference, or through a reference to `AGENTS.md` from outside the folder
- [How to trigger a skill from a prompt](how-to/trigger-a-skill-from-a-prompt.md) — the wordings that invoke each superpowers skill, and those that bring nothing
- [How to switch modes](how-to/switch-modes.md) — the ponytail and caveman levels, in a session and permanently
- [How to check that a plugin really works](how-to/check-a-plugin-works.md) — six checks, ordered from cheapest to slowest
- [How to add a new tool](how-to/add-a-new-tool.md) — the five questions for an AI coding tool, and what changes after each answer

## Reference

Exact values read directly from the system, not written from memory. None are dated:
plugin values match the versions pinned in `plugins.lock.json`, while environment
landmarks are re-measured with the command block in [README.md](../README.md).

⚠ When updating a plugin, re-read the values in the four references from disk.
The exact path is shown by `ls ~/.claude/plugins/cache/`.

- [The structure of the workspace](reference/structure.md) — every folder and every file: what it is, who reads it, and what breaks without it
- [Glossary](reference/glossary.md) — the words the workspace uses differently, each with its gloss
- [superpowers](reference/superpowers.md) — 14 skills, no slash commands, and the token cost of each
- [ponytail](reference/ponytail.md) — the seven-rung ladder, the 6 commands, and the declared measurements
- [caveman](reference/caveman.md) — the levels, counterintuitive rules, and the 21 skills
- [RTK](reference/rtk.md) — the 43 compressed programs and the list of exclusions
- [Antigravity](reference/antigravity.md) — what gets installed, where it keeps its files, how it is updated, and what was tested

## Explanation

Read away from the computer.

- [What each plugin does and when it is worth it](explanation/what-each-plugin-does.md) — the four layers, and the best and worst case for each
- [How a plugin comes to apply](explanation/how-a-plugin-applies.md) — the three mechanisms, and why the descriptions do not say what the skill does
- [Splitting the work across models](explanation/splitting-work-across-models.md) — why a work item with a plan goes through four sessions, on different models, and where the line falls
- [Conflicts and pitfalls](explanation/conflicts-and-pitfalls.md) — seven pitfalls, each with the method by which it was caught

## Where to start

There is only one starting path: see "The documentation map" in
[README.md](../README.md).

## The plugins' numbers and paths

| Landmark | Value |
|---|---|
| Installed plugins | 4, all in the `user` scope |
| The configuration | `~/.claude/settings.json` |
| The plugins' files | `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` |
| The binary that manages them | `claude` from `PATH`; otherwise the one in the application, `~/.config/Claude/claude-code/<version>/claude`, at the newest version |
| Permanent cost, total | ~2,516 tokens in every session |
| Slash commands available | 12 (ponytail 6, caveman 5, RTK 1; superpowers none) |
| Skills available | 42 (caveman 21, superpowers 14, ponytail 6, RTK 1) |

Everything required to run the environment, along with the command used to check each
version, sits in a single list: [Quick start](../README.md#what-it-needs), in the README.

## What is not here

This documentation describes the plugins as read from disk. It omits features promised
in upstream repositories for other tools — Codex, Gemini, Copilot — that do not apply
here, and excludes unverified measurements. Where a figure comes from an author's
documentation rather than the system, the source is explicitly named.
