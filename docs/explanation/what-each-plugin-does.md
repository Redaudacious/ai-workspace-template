# What each plugin does and when it is worth it

The four installed plugins appear to do similar things at first glance: each promises
"less." In reality, they operate on four distinct layers of the same conversation,
allowing them to coexist without interfering with one another.

## Each plugin touches a different layer of the conversation

| Layer | Plugin | What it controls |
|---|---|---|
| Order of work | superpowers | what happens before what |
| Written code | ponytail | how much code gets written |
| Displayed response | caveman | how output text is phrased |
| Terminal output | RTK | how much command output enters the conversation |

Only one plugin out of the four touches the code. Only one touches what comes from the
terminal. The only genuine overlap occurs between superpowers and caveman, which is
covered in [Conflicts and pitfalls](conflicts-and-pitfalls.md).

## superpowers makes a step impossible to skip

The 14 skills (a skill is a set of instructions that enters the conversation when the
situation matches) do not add knowledge. They enforce a **mandatory sequence**:
discuss before planning, plan before writing, write the test before the code, and
verify before saying "done."

The value does not lie in any single step in isolation — everyone knows tests are
useful. It lies in ensuring that the step cannot be skipped under pressure.

The `using-superpowers` skill contains a table of twelve rationalizations, each
with its counter-argument: "This is just a simple question", "I need more context
first", "The skill is overkill". Those twelve sentences are the exact excuses an
agent generates when attempting to bypass discipline.

**Best case:** a task large enough that sequence matters — a new feature, a bug of
unknown origin, or a branch that needs to be integrated.

**Worst case:** a one-line question. Invoking the `brainstorming` skill costs ~3,800
tokens; a question whose answer is simply "yes" does not warrant that overhead.

## ponytail catches the extra construction

The seven-rung ladder, stopping at the first rung that holds, shifts the question from
"how do I write this" to "does this need to be written at all." The first rung is not
about code: *does it need to exist?*

The author's benchmark on a real repository across twelve tasks yielded -54% lines of
code and -22% tokens compared to the same session without the skill.

Just as telling as the numbers is **where** the reduction occurs: it is substantial
where over-engineering traps exist (a 404-line calendar drops to 23 lines by using
native `<input type="date">` instead of a third-party library) and practically zero on
code that is already minimal.

Ponytail does not simply make code smaller in general. It catches a specific class of
mistake: building a custom mechanism instead of using an existing one.

**Best case:** whenever the primary risk is over-building — adding a new feature,
choosing a library, or starting a refactor that threatens to become a rewrite.

**Worst case:** an algorithm where edge-case correctness matters more than brevity. The
skill provides its own explicit exception: "Two stdlib options, same size? Take the one
that's correct on edge cases."

## caveman compresses the small part of the conversation

Caveman compresses the displayed answer: no articles, no filler words, and fragments
are accepted.

The counterintuitive part is that its rules forbid almost everything one would do
by instinct to sound compressed. Invented abbreviations (`cfg`, `impl`) are banned
because the tokenizer splits them into subwords just like the full term — yielding zero
savings while adding decoding effort.

Arrows are forbidden because each constitutes a separate token. Inserting words to
sound primitive is also disallowed. The explicit rule states: if compressed phrasing is
not shorter than plain phrasing, use plain phrasing.

Before counting it as a net saving, consider the data: in the agentic benchmark from
ponytail's documentation, caveman recorded **+7% tokens, +3% cost, +2% time** against
the baseline, while reducing lines of code by only 20%. The measurement comes from a
competing plugin, so it is not neutral — but the underlying mechanism is verifiable.

In a real work session, most tokens come from what the agent reads — files, command
outputs, search results — rather than what it writes. Compressing the final response
touches only the smaller share. Meanwhile, the plugin's permanent overhead of ~1,244
tokens is paid in every session, whether the mode is active or not.

**Best case:** a reader seeking high information density — concise answers free of
pleasantries and restatements.

**Worst case:** writing documentation and conceptual explanations, where the complete
sentence is the product itself.

## RTK cuts from what enters the model

RTK is the only plugin working in the opposite direction: filtering what enters the
model from the system rather than what leaves it.

It sits in front of each shell command and, if the program is among the 43 on its list,
runs it through its own binary to compress the output. A verbose `git status`, a test
suite, or a package installation accounts for thousands of unseen tokens.

Its permanent cost is ~12 tokens. Of the four plugins, it is the only one where asking
whether it is worth it practically never arises.

**Best case:** long sessions running numerous commands that produce large terminal
output.

**Worst case:** a workflow relying on commands chained through pipelines. Piped
commands pass through uncompressed by design so scripts do not break; anyone working
primarily with patterns like `grep ... | head` will not see the promised savings.

## The plugin that promises savings costs the most at startup

The four plugin descriptions load in every session, whether their features are used or
not:

| Plugin | Permanent tokens |
|---|--:|
| caveman | ~1,244 |
| ponytail | ~676 |
| superpowers | ~584 |
| RTK | ~12 |
| **Total** | **~2,516** |

The order runs counter to intuition. The plugin that promises token savings is the
most expensive at startup, while the one that actually reduces input volume is the
cheapest. The reason is simple: caveman declares 21 skills and 3 agents, whereas RTK
has only one.

## Understand-Anything: a plugin evaluated and rejected

[Egonex-AI/Understand-Anything](https://github.com/Egonex-AI/Understand-Anything),
v2.9.7, MIT, evaluated and rejected. It builds a project knowledge graph, but
spawns up to five parallel Claude analyzers alongside four additional agents.

That is what disqualifies it: the framework rule (the framework is the repository
containing the rules, skills, and tools common to all projects) permits no subagents
(another Claude instance started from a session).

Its auto-update hook explicitly instructs the session not to ask the human. It requires
`pnpm` ≥ 10 and compiles on its first run.

**Reopened if** the plugin gains a mode without subagents, if the subagent rule changes,
or if an external repository appears that is too large to read by hand.
