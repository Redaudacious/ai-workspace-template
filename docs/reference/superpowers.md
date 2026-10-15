# Reference — superpowers

Superpowers governs the workflow sequence by setting skill precedence. The values
come from `~/.claude/plugins/cache/superpowers-marketplace/superpowers/6.3.0/`, the
version pinned in `plugins.lock.json`.

## Identification

| Field | Value |
|---|---|
| Full name | `superpowers@superpowers-marketplace` |
| Version | 6.3.0 |
| Source | `obra/superpowers-marketplace` |
| Installation scope | user (`~/.claude/settings.json`) |
| Permanent cost | ~584 tokens in every session |

## Slash commands

None. The plugin contains no `commands/` folder.

All 14 components are skills. A skill is a set of instructions that enters the
conversation when the situation matches. Skills are triggered by matching the
description against a natural language request. The practical consequence is covered in
[How to trigger a skill from a prompt](../how-to/trigger-a-skill-from-a-prompt.md).

## Skills

The trigger column repeats the condition from each skill's `description` field. That is
the exact text used for prompt matching.

| Skill | Trigger | Cost at invocation |
|---|---|---|
| `brainstorming` | before any creative work: a new feature, a new component, changed behavior | ~3,800 |
| `writing-plans` | there is a specification for a task with several steps, before touching code | ~1,700 |
| `executing-plans` | there is a written plan, to be executed in a separate session, with checkpoints | ~540 |
| `subagent-driven-development` | the execution of a plan with independent tasks, in the current session | ~8,000 |
| `dispatching-parallel-agents` | 2 or more independent tasks, with no shared state | ~1,500 |
| `test-driven-development` | any feature or repair, before the implementation code | ~2,200 |
| `systematic-debugging` | any defect, failing test or unexpected behavior, before proposing repairs | ~2,300 |
| `requesting-code-review` | a task finished, a major feature, before integration | ~700 |
| `receiving-code-review` | feedback was received, before implementing it | ~1,500 |
| `verification-before-completion` | before declaring something finished, repaired or passing | ~830 |
| `using-git-worktrees` | work that requires isolation from the current space | ~1,600 |
| `finishing-a-development-branch` | the implementation is complete, the tests pass, integration follows | ~1,900 |
| `writing-skills` | creating, editing or checking skills | ~6,500 |
| `using-superpowers` | at the start of any conversation | ~720 |

**Three of these skills are not used in the workspace.** A written plan is executed with
`execute`, the framework's skill (the repository with the rules, skills and tools common
to all projects), rather than `executing-plans`.

`subagent-driven-development` and `dispatching-parallel-agents` send work to more
subagents (another Claude, started from a session). Here, only one subagent starts at a
time, and only from the framework's own agents:
[Splitting the work across models](../explanation/splitting-work-across-models.md#how-many-at-once-only-one).

## Hooks

| Moment | Command | Interpreter |
|---|---|---|
| `SessionStart` (`startup`, `clear`, `compact`) | `hooks/run-hook.cmd session-start` | bash |

A single hook, written in bash. Unlike the other two installed plugins, it does not
require `node`. The topic is covered in
[Conflicts and pitfalls](../explanation/conflicts-and-pitfalls.md).

## The central rule

The text from `using-superpowers/SKILL.md`, under the section "The Rule":

> Invoke relevant or requested skills BEFORE any response or action — including
> clarifying questions, exploring the codebase, or checking files.

When several skills match, the declared priority order applies. Process skills come first
and set the approach. Implementation skills come after them.

## Notable auxiliary files

| Path | Size | Content |
|---|---|---|
| `skills/writing-skills/anthropic-best-practices.md` | 46,197 bytes | the official guide to writing skills |
| `skills/writing-skills/persuasion-principles.md` | 5,901 bytes | the seven Cialdini principles applied to skills |
| `skills/writing-skills/testing-skills-with-subagents.md` | 12,558 bytes | the method of testing a skill on subagents |
