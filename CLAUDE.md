@AGENTS.md

## Claude Code only

The shared rules are in `AGENTS.md`, imported on the first line. Only what is specific
to Claude Code belongs here.

### Models by role

| Tier in the plan header | Model |
|---|---|
| Opus, with the stated effort | Opus, selected from the application menu, with the same effort |
| Sonnet, with the stated effort | Sonnet, with the same effort; never `max` |

Why two tiers and what each costs: [splitting the work across models](docs/explanation/splitting-work-across-models.md).

### Rules load from the starting folder and its parents

At launch, Claude Code reads `CLAUDE.md` and `AGENTS.md` from the starting folder and
its parents; subfolder rules load only once a file there is read with the Read tool.
Using `cat` in the shell never brings them in. `AGENTS.md` loads automatically only when
"Project instructions" is set to `claude-md-and-agents-md`, set by `bin/restore-env.sh`.

An `@path` import whose target lies outside the starting folder needs Claude Code's
approval, and without it the import does not expand. The shared rules therefore do not
depend on an import, and the house rules are a user rule, symlinked by the restore script.

`~/.claude/rules/house-rules.md` points to `records/house-rules.md`; memory comes in
through a symlink made by the same script.

Reason: measured on 1 October 2026 in session logs: in sessions opened inside a
project, the house rules import in `CLAUDE.local.md` remained plain text, and the house
rules never loaded.

### From the root, the first file of a project is read with Read

Reading the first file in a directory with the Read tool automatically pulls in the
entire `CLAUDE.md` hierarchy from the root down to that folder: first the project's,
then the sub-project's or domain's below it. Running `cat` brings nothing. Once read, `cat` is
fine.

Before making the first edit in a repository, inspect its `CLAUDE.md` and `IMPACT.md`
using Read to load both the rule chain and the impact map together.

Reason: measured on 23 September 2026 in a session launched from the root: a single Read
call on a file in a sub-project's folder loaded both the parent project's and the
sub-project's `CLAUDE.md` files unprompted.

### Skills, plugins and modes

House skills are symlinked under `~/.claude/skills/`, and plugins pinned in
`plugins.lock.json` reside under `~/.claude/plugins/`; `bin/restore-env.sh` rebuilds
both. A skill is invoked using the Skill tool.

The superpowers, caveman, ponytail, and rtk plugins run through hooks: on session
startup, with each message, and before any command. Caveman turns off with
`/caveman off`.

### The Antigravity worker

On Antigravity's execution tier, Gemini 3.8 Flash, a task with a verifier runs
through the tool bridge, dispatched from the root of the repository it modifies:

```bash
bin/tool-bridge.sh --tool agy --model gemini-3.8-flash-high --target <file> --task <file> --verify '<command>'
```

When the Gemini quota runs out, the same route leads to Claude Sonnet 4.6, with `--model
claude-sonnet-4-6`: Antigravity serves it from a different quota than the Gemini models.
The bridge reports an exhausted quota by name and does not retry.

From a project, the script is called from the root's `bin/`, two folders up. It requires
an authenticated `agy`. The bridge responds according to the contract in `AGENTS.md`.

### The temporary folder and subagents

The session's temporary folder is the scratchpad provided by the application. Subagents
are launched with the Agent tool, which the subagent rule in `AGENTS.md` forbids.
