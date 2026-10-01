# How to trigger a skill from a prompt

A skill is a set of instructions brought into the conversation when a situation matches.
This guide applies to superpowers skills, the plugin governing work order: they have no
slash commands and trigger solely by description matching. The underlying mechanism
is explained in [How a plugin comes to apply](../explanation/how-a-plugin-applies.md).

## The situation is described, not the tool

The **situation** is described, not the tool. Skill descriptions are written as
situations ("when there is a written plan to execute"), so the more closely a prompt
resembles a situation, the more reliably it matches.

## The steps of a request that triggers

1. **The stage is named, not the action.** "Add X" contains no stage. "I want us to
   build X, but I have not decided how" provides one.
2. **The unknown is stated.** Declared uncertainty is the strongest trigger for process
   skills. A defect whose cause is unknown leads to `systematic-debugging`; one described
   as "change line 12" does not.
3. **The work is placed in time.** "Before I write code", "I am done, integration is
   next", "I received a review" — each of these three wordings corresponds to a
   different description.
4. **Confirmation is required.** An invoked skill is announced with the formula
   "Using [skill] to [purpose]". If the announcement is missing, the skill was not
   applied.

## Wordings that trigger

The right-hand column contains the situation from the skill's `description` field, not
a paraphrase.

| Wording in the request | Skill reached |
|---|---|
| "I want us to build…", "I am thinking of a feature that…" | `brainstorming` |
| "I have the specification, make a plan before you touch code" | `writing-plans` |
| "execute the plan <path> with the execute skill", in a new session | `execute`, the framework's skill |
| "write the test first" | `test-driven-development` |
| "I do not understand why it fails", "it behaves differently from what I expect" | `systematic-debugging` |
| "I am done, verify before you say it works" | `verification-before-completion` |
| "look over what I did before I integrate" | `requesting-code-review` |
| "I received this feedback, but I am not convinced" | `receiving-code-review` |
| "I want to work isolated from what is in the tree now" | `using-git-worktrees` |
| "the tests pass, what do I do with the branch" | `finishing-a-development-branch` |

`execute` does not come from superpowers; it belongs to the framework (the repository
containing the rules, skills, and tools common to all projects).

`dispatching-parallel-agents` and `subagent-driven-development` are not used here: no
session sends work to subagents (another Claude instance started from a session).
The rule sits under "Who does what" in `AGENTS.md` (the shared rules file loaded by
every session in any tool).

## Wordings that trigger nothing

| Wording | What is missing |
|---|---|
| "fix this" | no stage, no uncertainty |
| "add a button" | an action without a situation |
| "it is broken" | a symptom without stating that the cause is unknown |
| "do my documentation" | covered by another skill, not by superpowers |

## When the name is better than the situation

Direct naming — "use systematic-debugging" — is better suited to two cases:

1. When the correct stage is already known and requires no negotiation.
2. When an earlier request missed the intended skill and is being reworded.

The limitation of direct naming is that it brings only the description into context.
The behavior lives in the body of the skill, and the body is read only if the skill is
genuinely invoked. The verification check remains the same: the announcement
"Using [skill] to […]" must appear.

## Two mistakes that spoil the order

- **Multiple skills are not listed in a single request.** The order is set by the
  plugin — process skills first, implementation skills after — and an externally
  imposed list breaks it.
- **An implementation skill is not requested directly on a large task.** "Write the
  tests" skips `brainstorming`, the exact step that decides what must be tested.
