# How to trigger a skill from a prompt

A skill is a set of instructions. It enters the conversation when a situation matches.

This guide applies to the superpowers skills. Superpowers is the plugin that decides the order of work. Its skills have no slash commands. They trigger only by matching their description. [How a plugin comes to apply](../explanation/how-a-plugin-applies.md) explains the mechanism behind this.

## Situations, not tools

Describe the **situation**, not the tool. Skill descriptions name situations ("when there is a written plan to execute"). So the more a request resembles a situation, the more reliably it matches.

## The steps of a request that triggers

1. **Name the stage, not the action.** "Add X" names no stage. "I want us to build X, but I have not decided how" names one.
2. **State what is unknown.** Declared uncertainty is the strongest trigger for process skills. A defect whose cause is unknown leads to `systematic-debugging`. A defect described as "change line 12" does not.
3. **Say where the work stands in time.** Each phrase matches a different description. Examples: "Before I write code", "I am done, integration is next", "I received a review".
4. **Require confirmation.** An invoked skill announces itself with the formula "Using [skill] to [purpose]". If the announcement is missing, the skill did not apply.

## Wordings that trigger

The right-hand column contains the situation from the skill's `description` field, not a paraphrase.

| Wording in the request | Skill reached |
|---|---|
| "I want us to build…", "I am thinking of a feature that…" | `brainstorming` |
| "I have the specification, make a plan before you touch code" | `writing-plans` |
| "execute the plan <path> with the execute skill", in a new session | `execute`, the framework's skill |
| "write the test first" | `test-driven-development` |
| "I do not understand why it fails", "it behaves differently from what I expect" | `systematic-debugging` |
| "I am done, verify before you say it works" | `verification-before-completion` |
| "review what I did before I integrate" | `requesting-code-review` |
| "I received this feedback, but I am not convinced" | `receiving-code-review` |
| "I want to work isolated from what is in the working tree now" | `using-git-worktrees` |
| "the tests pass, what do I do with the branch" | `finishing-a-development-branch` |

`execute` does not come from superpowers. It comes from the framework: the repository with the rules, skills, and tools shared by all projects.

`dispatching-parallel-agents` and `subagent-driven-development` are not used here. A session starts only one subagent at a time, and only from the house agents. The subagent is another Claude, started from a session. The rule sits under "One subagent at a time" in `AGENTS.md`, the shared rules file that every session loads in any tool.

## Wordings that trigger nothing

| Wording | What is missing |
|---|---|
| "fix this" | no stage, no uncertainty |
| "add a button" | an action without a situation |
| "it is broken" | a symptom without a statement that the cause is unknown |
| "write my documentation" | covered by another skill, not by superpowers |

## When the name is better than the situation

Direct naming, such as "use systematic-debugging", is better suited to two cases:

1. When the stage is already known, and the user wants no negotiation.
2. When an earlier request missed the intended skill, and the user rewords it.

The limit of direct naming is that it brings only the description into the conversation. The behavior lives in the body of the skill. The session reads the body only if the skill is really invoked. The rule stays the same. Expect the announcement "Using [skill] to […]".

## Two mistakes that spoil the order

- **Do not list several skills in one request.** The plugin sets the order: process skills first, implementation skills after. A list imposed from outside breaks that order.
- **Do not request an implementation skill directly on a large task.** "Write the tests" skips `brainstorming`. That step decides what must be tested.
