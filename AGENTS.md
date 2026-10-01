# How work is done in this folder

This file holds what is common across all AI coding tools and loads automatically in
every session: Antigravity and other tools read it directly, Claude Code does as well
with the setting configured by `bin/restore-env.sh`, and `CLAUDE.md` imports it for
sessions running without that setting.

Tool-specific details — models, skills, plugins, and rule-loading mechanisms — live
in that tool's module alongside this file; the list is under "Tools". Every heading
is a rule; below it sit its exact form, its reason, and where its history is kept.
The house words are in the [glossary](docs/reference/glossary.md).

`superpowers:using-superpowers` is invoked before any response, including before
clarifying questions.

## Who does what

Planned work goes through **four sessions**, each one new, each with its own role:

| session | tier | does | does not do |
|---|---|---|---|
| **the spec** | heavy, `max` | talks with the human, settles requirements, picks the architecture, writes the work item's spec | does not write the plans: hands them over to the next session |
| **the plans** | heavy, `max` | reads the spec and writes the plans and the work item's `README.md`, with the plan header and each task's `Who` label | does not reopen the architecture settled in the spec; does not write the code |
| **execution** | the one in the plan header, execution tier by default, `high` | carries out the plan to the end with the `execute` skill, without stopping between tasks | does not make decisions the plan does not cover: asks the human |
| **review** | heavy, `high`, new session | reads the report, the plan, and the branch diff; merges or sends back | does not reopen planning chats |

Reason: most of the cost comes from re-reading the conversation at every step, and a
new session no longer carries the discussion in which decisions were made.
History: [splitting the work across models](docs/explanation/splitting-work-across-models.md).

**The tiers.** The plan header and the handoff record the tier using the house names:
"Opus" is the heavy tier, "Sonnet" is the execution tier, and effort is `medium`, `high`,
`xhigh`, or `max`. Which model corresponds to each tier is defined in the tool's module,
under "Models by role".

### Variants and the spec rest on verified facts, not on what seems true

Anything about a tool, a service or a model from outside the house is looked up in its
source — the documentation, the page, the code — before the variants, and goes into the
spec with the link and the date. Anything about the house is read from the repository.

An assumption that remains is written as an assumption, with the check that would settle
it.

Reason: execution follows the spec literally, and a written assumption looks exactly like
a verified fact. On 1 October 2026, a spec trial in Antigravity went straight to the
variants without looking anything up outside.

### The spec and the plans are written in different sessions

The session that talked with the human stops after the spec: it runs `end-of-session`
and hands over. The next session, a fresh one, reads the spec and writes the plans. A
planning session may write all the plans for a work item, or only some, provided it
hands over the rest.

Reason: the discussion that settled the requirements is the expensive part, and it adds
nothing to writing the plans: everything decided is already in the spec.

### The plan header is written by the planning session

Execution effort is `high` by default, `xhigh` when the plan contains tasks that need
investigating, `medium` for a purely mechanical plan, and never `max` on the execution
tier.

`Closing: Opus review` is written when the plan changes rules, touches services or
hardware, deletes what cannot be recovered, or touches keys and access credentials.
Otherwise, `Closing: Sonnet` is written.

### The code written in a plan is run before the handoff

The planning session applies the code exactly as written in the plan inside a throwaway
copy of the repository — a detached `git worktree` in the session's temporary folder —
and runs the plan's tests: each must fail before the change and pass after it, exactly as
the plan specifies. The copy is deleted at the end; nothing from it enters the branch.

The copy sits in the temporary folder at the same relative path as the repository from
the workspace root, with each parent's `bin/` directory symlinked to the real one:
otherwise tools invoked via relative paths are missing, and a guarded test skips without
having run. A skipped test is checked on its own line, not merely in the total.

Reason: execution follows the plan literally, and a test failing through the plan's
fault halts it. On its first use, the copy caught an old defect in the mutation tool that
read "30 failed" as zero, along with two invalid anchors in the plan itself.
History: the decision of 26 September 2026, "The throwaway copy sits at the depth of the repository".

### In the throwaway copy, a test identity is given with `git -c`, not `git config`

`git -c user.name=test -c user.email=test@local commit …` keeps the identity to that one
command. `git config`, run from a worktree, writes it into the shared configuration of
the real repository, and every later commit there picks it up.

Reason: on 1 October 2026, 208 commits in one project's repository, from 22 September on,
carried a test's author, because the identity sat in that repository's `.git/config`.
History: the pitfall of 1 October 2026, "A repository's commits carry a test's author".

### Only planned work is handed over

The plan sits in a work item's folder within the records of the repository it modifies.
A minor fix without a plan is completed on the spot by the session that decided on it.

### The model and the tool are changed by opening a new session

The model, effort, folder in which the session is opened, and prompt to paste are
written by `end-of-session` in the handoff inside the `STATE.md` of the work item's
repository. The handoff contains a row for each tool with a module at the root.

Reason: inside the same session the long conversation would remain, and that is the
expensive part.

### No session sends work to subagents

Not a task from a plan, not a broad search, not a diff review. Execution works alone,
alongside local workers, one at a time.

Reason: execution has its own dedicated session and handles alone the work subagents
used to perform; moreover, agents started simultaneously share the same allowance and
all stop at once, returning nothing.

### Execution works on the branch in the plan header

It enters `main` after review, or directly only when the plan specifies
`Closing: Sonnet` and nothing has requested a review.

### The local worker is used first, when one exists

One exists only when `records/local-workers.md` has at least one worker with numbers.
If the file is missing, or has no row with numbers: execution stays in the session,
and states once why.

- **The worker is a house model or a model of the other tool.** For a house
  model, the bridge, machine preparation, and release commands are read from that file,
  which belongs to the human and their machines. For the other tool, the bridge is
  `bin/tool-bridge.sh`, part of the framework; the command is in the delegating tool's
  module.
- **No model without a row in the table is used.** A row without numbers means
  "not measured, so not used".
- **If the verifier is the human, nothing is delegated.**
- **A task whose verifier is a command is marked in the plan for the bridge first.**
  If marked for the session, it states its reason openly: the model is not in the table,
  the task does not fit the context window, or the machine cannot be started.
- **The bridge contract**, valid for any tool that honours it:

  | What it receives | What it returns |
  |---|---|
  | the target, the task file, the verification command | exit code 0 and a diff, only if the verifier passed |
  | — | exit code 1: refusal; the task is done in the session |
  | — | exit code 2: does not fit the window; the task is done in the session |

How the workers file is built: the `local-workers` skill.

Reason: without this rule, the local worker is not used at all. Without the file, the
framework would describe a capability that does not exist on this machine — and a session
would look for a tool that is nowhere.

### An agent's report is not evidence

What changed is read from `git diff`, and that it works is proven by checks run here.
The rule holds for a local model as well.

## Where the work is kept

### A project's work lives in the project's repository

The work item, journal, pitfalls, decisions, and `STATE.md` concerning a project sit
in the records of that project's repository: `records/`, unless the project's own rules
name another folder.

In `records/` at the root sit only the framework's own work items and laptop issues
that belong to no project. The work index at the root mentions projects' work items with
the path written in prose, without a link.

Reason: sessions started from the root wrote project plans into the environment's
records, so anyone opening the project could not find them there.
History: the decision of 23 September 2026, "A project's work lives in its repository".

### A planned work item has a folder

`<records>/work/open/<YYYY-MM-DD-subject>/`, containing `README.md` for human readers,
the spec, and the plans written by the two planning sessions. The repository's work item
states and the backlog of leftovers sit in the adjacent `INDEX.md`.

### A work item is closed only when every leftover has a destination

Done, abandoned with the reason recorded, or queued in the backlog. Closing is handled
by `end-of-session`, creating `closing.md` and moving the folder into `closed/`.

Reason: leftovers abandoned inside closed plans never reached any destination.

### A decision that has to hold is written in the decisions record

Under `records/decisions/` for the environment, or the project's own directory for a
project. Not merely in `STATE.md`, which is rewritten at the end of every session.

## A project's session

### A session for a project is opened in the project's folder

Each tool sees a project's rules only when started from its folder: Claude Code loads
rules at startup from the launch folder and its parents, while Antigravity does not climb
above the opened folder. How each tool retrieves the rest of the chain is explained in
its module.

Reason: in sessions started from the root, a project's rules almost never entered the
context; in those started from its folder, they loaded every time.
History: the decision of 23 September 2026, "A project's work lives in its repository".

### At the closing, what was found climbs from the project towards the root

Reading walked down the tree; `end-of-session` writes in reverse, from the deepest
repository touched upward. Every pitfall, decision, journal entry, or candidate for
`AGENTS.md` stops at the first level that encompasses it whole: the sub-project's, the
project's, or the framework's.

It ascends a level only if it remains true without mentioning the sub-project or
project name. A candidate that concerns a single tool goes into that tool's module.

Reason: written too high, it is paid for in every session of every project; written too
low, no one from another project will find it.
History: the decision of 23 September 2026, "Reading goes down the tree, writing climbs".

## The order of the skills

Process before implementation: the process skill fixes the approach, the
implementation skill carries it out.

| The situation | Skill |
|---|---|
| something new is being built, requirements not settled | `superpowers:brainstorming` |
| requirements settled, multi-step task | `superpowers:writing-plans` |
| the plan is written, and this session executes it | `execute` |
| writing new code or repairing something | `superpowers:test-driven-development` |
| defect, failing test, unexpected behaviour | `superpowers:systematic-debugging` |
| before "done", "it works", "it passes" | `superpowers:verification-before-completion` |
| before integration | `superpowers:requesting-code-review` |
| code feedback has arrived | `superpowers:receiving-code-review` |
| values are verified, writing follows | `documentation` |
| tests pass, deciding what happens to the branch | `superpowers:finishing-a-development-branch` |
| session is closing, state must be written | `end-of-session` |
| creating or updating the local workers file | `local-workers` |

### `documentation` comes after verification and before integration

`documentation` comes **after** `verification-before-completion` and **before**
`finishing-a-development-branch`.

Reason: the values in a reference must already be verified, and the document goes into
the same commit.

### Every skill invoked is announced

With `Using [skill] to [purpose]`. Without the announcement, the skill was not
applied.

## Modes

### Caveman is turned off before writing documentation

The command that turns it off is in the tool's module.

Reason: its rules drop articles and forbid tables, which is exactly what documentation
requires, and turning it off afterward does not rewrite what has already been written.

### `ponytail` governs the code, not the documentation

Under `docs/`, the explanation is the product, not an addition to it.

### The session tells the human, in plain words, what it is doing and what came out

While working, after every step that matters, one full sentence: what was done, what came
out and what comes next. At each phase, how much is done, as a percentage, and how long
is left, in minutes. The final report is for someone outside the field, by the rule
below; a command the human runs sits in a `bash` block.

The output of a command is never left on its own in the conversation: say what it means,
with the numbers that matter, for example "all 401 tests passed; one is skipped because
it is slow".

Reason: the human leads without writing the code. On 1 October 2026, an Antigravity
session showed the human the whole test output three times, without a sentence about it,
and the human could not tell what had happened.

### Caveman off means an explanation for someone outside the field

Not merely whole sentences: what was being attempted, what happened, and why it
matters.

| do | do not |
|---|---|
| start with what was being pursued, not with what broke | start with the name of the defect |
| a concrete comparison — "like a record that skips" | a definition — "a token repetition loop" |
| translate retained terms on first use | untranslated jargon |
| keep numbers, each with the sentence explaining why it matters | numbers strung together without meaning |
| state debatable decisions openly, with argument and risk | a decision slipped in among others |

Reason: the human leads and makes decisions, but does not write code. A correct report
they cannot read is not a report; it is merely proof that work was done.

## The state of the repository is read first

### Before any reading of code, the state of every repository touched

| what is asked | how |
|---|---|
| is there a repository? | `git -C <project> rev-parse --git-dir` |
| which branch it is on | `git -C <project> branch --show-current` |
| how many commits ahead of or behind origin | `git -C <project> fetch --quiet && git -C <project> status -sb` |
| what is uncommitted | `git -C <project> status --porcelain` |

`fetch` comes before the comparison: without it, "up to date" means "up to date with
what was last known". Before making the first change in a repository, its `AGENTS.md`
and `IMPACT.md` are also read: the rules and the map.

Reason: a session that writes over a branch left behind creates a conflict that no one
sees until the push.

### At the end of the session everything is committed and pushed, in every repository touched

Both the project's and the environment's. Handled by `end-of-session`: it reads from
git what changed, rewrites the `STATE.md` of each touched repository, and proposes any
missing record entries. `AGENTS.md`, modules, and `IMPACT.md` are not written
automatically: candidates worth adding are reported, and the decision remains the human's.

Reason: a commit left local is work that exists on only one machine.

### Commits carry no `Co-Authored-By`

Nor any other trace of a tool or model, even if the application's default instructions
request otherwise. The message explains why, not what.

## Commands sent at the same time

### In a command sent in parallel, the directory is not changed with `cd`

Paths are written absolute, and git commands use `git -C`. Any command that writes —
commit, move, delete — is dispatched on its own.

Reason: a neighbouring command can run silently in the directory left behind by another;
when writing, the commit lands in a different repository than the one intended.

## Problems already solved

### Before repairing the environment, the journal index is read

Plugins, `node`, tools, machines: the journal index at `records/journal/INDEX.md` is
cheap to consult and avoids repeating a repair.

### A repaired command is searched for across the whole repository

Before calling a repair complete, run `git grep` on a fragment of its old form. A moved
record file is searched for in the same way across the entire workspace; how to do this
is covered in the long reference of the `documentation` skill, `details.md`.

### A changed tool from `bin/` is also checked with `check-maps.sh`

Not merely with its own test. Projects' impact maps invoke environment tools, and a
stricter tool can break them without the project having changed.

Reason: the tool's test passes, and the failure surfaces only in another repository.

### Every system repair is written in the journal, in the same session

Not just major ones: a package, driver, environment setting, or plugin. The entry
records the symptom, the cause, and the method.

- The laptop and the environment: `records/journal/` here, in the personal repository,
  with the machine noted in the entry.
- A machine maintained by a project, or a project-specific tool, even when installed on
  the laptop: the project's journal, tracked in git. Which machine belongs to which
  project is read from `records/house-rules.md`.

Reason: a month later, "I know I fixed something about this" can no longer be
reconstructed.

## Tools

### What belongs to a single tool lives in its module

| Tool | Module | What it reads on its own |
|---|---|---|
| Claude Code | `CLAUDE.md` | `CLAUDE.md` and, with the setting configured by restore, `AGENTS.md`, from the starting folder and its parents |
| Antigravity | `GEMINI.md` | `AGENTS.md` and `GEMINI.md` from the opened folder; anything above, via local files |
| Codex, Cursor, Copilot, opencode, Amp, and others | none yet | `AGENTS.md` |

A module starts with `@AGENTS.md` and exists only where it has something specific to
say, or where its tool might otherwise miss `AGENTS.md`. That is why `CLAUDE.md` sits
next to every `AGENTS.md`: its import works even where the setting is absent.
`GEMINI.md` sits only at the root. `check-docs.py` enforces these pairs.

How to add a tool: [the guide](docs/how-to/add-a-new-tool.md).

Reason: a rule written in two places diverges at the first change; written once in
`AGENTS.md`, it reaches all tools at once.
History: the "modular agents" work item, 1 October 2026.

## Agent memory

### What is worth remembering is written to memory, one file per fact

Memory lives in `records/memory/`: one file per fact, with the header fields `name`,
`description`, and `metadata.type` (`user`, `feedback`, `project`, or `reference`),
plus a row in the `MEMORY.md` index.

This includes user working preferences, human corrections, and work context not visible
from the code; it excludes anything already tracked by git or by a record. Before
writing, search for any file already covering the topic, and make relative dates
absolute.

Claude Code loads and writes it automatically via the symlink created by
`bin/restore-env.sh`. Other tools receive the index as detailed in their module and
write according to this rule.

Reason: a preference stated to one tool must reach the other; two disconnected memories
would learn different things about the same person.

## The environment guide is portable

### `README.md` and `docs/` describe the environment for any machine

No absolute or machine-specific paths belong there, nor calendar dates, user names, or
repository and project names. The location is called "the workspace root", paths are
relative to it, and numbers are accompanied by the command that re-measures them.

### `records/` and `STATE.md` are records

There the date and the machine represent the content itself, and they remain.

### A record is appended to, not rewritten

One file per entry, dated in its name, untouched once written; only its index is
rewritten. Under `records/` sit `journal/`, `pitfalls/`, `decisions/`, and `work/`,
and no documentation run touches them.

Reason: a record kept in a folder that gets rewritten reaches four thousand lines; the
folder's rule mandates rewriting, while the file's nature dictates only growth.

### The personal layer does not go into the framework's repository

`records/` is the clone of a private repository: the records, agent memory, house
rules, and local workers. `STATE.md` at the root does not go there either — it describes
a single machine, today. The journal does: a repair from yesterday is useful on the
next laptop too, and without a repository it would perish with this one.

Reason: the framework can be handed to someone else without transferring personal
history, and that history follows the human to another machine without carrying along the
framework.
History: the decision of 23 September 2026, "The laptop's journal goes into the personal repository".

### No tracked file of the framework links into `records/`

A path written in prose is allowed: that is how the framework names its contract with
the personal layer. A link is not: on the user's machine the folder exists and the
link works, but on a fresh clone it breaks.

Reason: the mistake would remain invisible on the very machine where it was made.
`check-docs.py` prints it as `PERSONAL:` and fails.
