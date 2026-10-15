# What each plugin does and when it is worth it

The three installed plugins appear to do similar things. Each promises "less." In reality, they touch three different layers of the same conversation. That is why they can coexist without cancelling each other out.

## Each plugin touches a different layer of the conversation

| Layer | Plugin | What it controls |
|---|---|---|
| Order of work | superpowers | what happens before what |
| Written code | ponytail | how much code gets written |
| Terminal output | RTK | how much of a command's result enters the conversation |

Only one plugin out of the three touches the code. Only one touches what comes from the terminal. Pitfalls met during installation are in [Conflicts and pitfalls](conflicts-and-pitfalls.md).

## superpowers makes a step impossible to skip

The 14 skills do not add knowledge. Each skill is a block of instructions that loads only in its own situation. They enforce a **mandatory sequence**: discuss before planning, plan before writing, write the test before the code, and verify before saying "done."

The value does not lie in any single step in isolation. Everyone knows tests are useful. It lies in making the step impossible to skip under pressure.

The `using-superpowers` skill contains a table of twelve rationalizations, each with its own reply. Examples: "This is just a simple question", "I need more context first", "The skill is overkill". Those twelve sentences are the exact excuses an agent generates when it tries to bypass discipline.

**Best case:** a task large enough that sequence matters: a new feature, a bug of unknown origin, or a branch that needs integrating.

**Worst case:** a one-line question. Invoking the `brainstorming` skill costs ~3,800 tokens. A question whose answer is simply "yes" does not warrant that overhead.

## ponytail catches the extra construction

The seven-rung ladder stops at the first rung that holds. The first rung is not about code. It asks: *does it need to exist?* The ladder moves the question. It goes from "how do I write this" to "does this need to be written at all."

The author's benchmark ran twelve tasks on a real repository. It yielded -54% lines of code and -22% tokens, compared to the same session without the skill.

Just as telling as the numbers is **where** the reduction occurs. The reduction is substantial where over-engineering traps exist. A 404-line calendar drops to 23 lines when it uses native `<input type="date">` instead of a third-party library. The reduction is practically zero on code that is already minimal.

Ponytail does not simply make code smaller in general. It catches a specific class of mistake: building a custom mechanism instead of using an existing one.

**Best case:** any moment when the primary risk is over-building. Examples: a new feature, a library choice, or a refactor that could become a rewrite.

**Worst case:** an algorithm where edge-case correctness matters more than brevity. The skill provides its own explicit exception: "Two stdlib options, same size? Take the one that's correct on edge cases."

## RTK cuts from what enters the model

RTK is the only plugin working in the opposite direction: it filters what enters the model from the system, not what leaves it.

It sits in front of each shell command. If the program is among the 43 on its list, it runs the command through its own binary, which compresses the output. A verbose `git status`, a test suite, or a package installation accounts for thousands of tokens that nobody sees.

Its permanent cost is ~12 tokens. Of the three plugins, it is the only one where asking whether it is worth it practically never arises.

**Best case:** long sessions running numerous commands that produce large terminal output.

**Worst case:** a workflow that chains commands through pipelines. Piped commands pass through uncompressed by design, so scripts do not break. Anyone who works mainly with patterns like `grep ... | head` will not see the promised savings.

## What each plugin costs at startup

The three plugin descriptions load in every session. They load whether anyone uses their features or not:

| Plugin | Permanent tokens |
|---|--:|
| ponytail | ~676 |
| superpowers | ~584 |
| RTK | ~12 |
| **Total** | **~1,272** |

RTK, the plugin that actually reduces input, is the cheapest at startup. The reason is simple: superpowers declares 14 skills, ponytail 6, and RTK only one.

## Understand-Anything: a plugin evaluated and rejected

[Egonex-AI/Understand-Anything](https://github.com/Egonex-AI/Understand-Anything), v2.9.7, MIT, evaluated on 19 September 2026. It builds a project knowledge graph, but spawns up to five parallel Claude analyzers alongside four additional agents.

That is what disqualifies it. The framework rule allows one subagent at a time, and only from the framework's own agents. (The framework is the repository containing the rules, skills, and tools common to all projects. A subagent is another Claude instance started from a session.)

Its auto-update hook explicitly instructs the session not to ask the human. It requires `pnpm` ≥ 10 and compiles on its first run.

**Reopened if:**

- the plugin gains a mode without subagents.
- the subagent rule changes.
- an external repository appears that is too large to read by hand.
