@AGENTS.md

## Antigravity only

The shared rules are in `AGENTS.md`, which Antigravity reads on its own; the top line
imports it for the Gemini CLI. Verified on 1 October 2026, against application 2.19.1
and the `agy` CLI 1.2.14; re-verify on a new version, following [the Antigravity
reference](docs/reference/antigravity.md).

### Models by role

| Tier in the plan header | Model, with the identifier for `agy --model` |
|---|---|
| Opus, `max` or `high` | Gemini 3.1 Pro, High thinking: `gemini-3.1-pro-high` |
| Sonnet, `xhigh` or `high` | Gemini 3.8 Flash, High thinking: `gemini-3.8-flash-high` |
| Sonnet, `medium` | Gemini 3.8 Flash, Medium thinking: `gemini-3.8-flash-medium` |

On AI Pro, the quota refills every five hours, up to a weekly limit, and all Gemini
models draw from the same quota. The Claude models in Antigravity, Sonnet 4.6 and Opus
4.6, have a quota of their own: once the Gemini quota runs out, the execution tier moves
to `claude-sonnet-4-6`. Measured on 1 October 2026, with the Gemini quota used up.

### Rules above the open folder come from local files

Antigravity reads `AGENTS.md` and `GEMINI.md` in the open folder on its own, but does
not climb higher. Rules from parents, the house rules, and the memory index are
brought in by `.agents/rules/framework-NN.md` files, one per include, written by
`bin/antigravity.sh` in each repository and rule folder and kept out of git.

Its documentation states that touching a file in a subfolder also loads the rules from
there; headless testing did not observe this. The session therefore opens in the folder
named in the handoff, not above it.

Reason: the loading test of 1 October 2026, with canary words in each file; the
24,000-byte limit of a rules file is counted after inclusion.

### Skills, plugins and modes

- House skills and those of superpowers, caveman, and ponytail are symlinked in
  `~/.gemini/config/skills/`, from the same folders as in Claude Code;
  `bin/antigravity.sh` links them.
- Antigravity has no Skill tool: a skill is loaded by reading its `SKILL.md`, or via
  `/<name>`. A skill named in the rules as `superpowers:<name>` is the `<name>` skill.
- Launching superpowers, caveman, and ponytail comes from always-active global rules in
  `~/.gemini/config/rules/`: Antigravity has no startup or message hooks. Caveman is
  stopped with "stop caveman", ponytail with "stop ponytail".
- RTK does not rewrite commands: development commands are written with `rtk` in front.

### Where the rules call for a stop, the session asks with `ask_question` and waits

Antigravity is built to carry a task through on its own, and the "Turbo" permission
preset runs its commands without asking. The stops come from the rules: the
brainstorming questions, one at a time, before the variants; a decision the plan does
not cover; the "yes" at the closing of an execution, before the merge and the push.

Each one is asked with `ask_question`, one question at a time, and the session does not
go on until the answer. In a spec, the first questions are about the purpose, the
constraints and what success looks like; the architecture variants come only after them.
A skipped answer is not a "yes": the session stops and says what it is waiting for.

The facts from outside the house that `AGENTS.md` asks for before the variants are
looked up with `search_web` and read from their page with `read_url_content`; a variant
proposed from memory is not verified.

Reason: on 1 October 2026, two executions in Antigravity wrote the state file, committed
and pushed without the human's "yes", and a spec trial skipped the clarifying questions.

### The output of a background command does not stand in for an answer

Antigravity puts the full output of every command that ran in the background into the
conversation, as a message. After each one, the session writes what it means, by the rule
in `AGENTS.md`, "The session tells the human, in plain words, what it is doing and what
came out".

### The Claude Code worker

On Claude Code's execution tier, Sonnet, a task with a verifier is dispatched through
the tool bridge, from the root of the repository it changes:

```bash
bin/tool-bridge.sh --tool claude --model sonnet --target <file> --task <file> --verify '<command>'
```

It requires `claude` authenticated once from the terminal via `/login`; the command is
added to the terminal's permission list. Without it, Sonnet 4.6 comes from Antigravity
itself, with `--tool agy --model claude-sonnet-4-6`.

From a project, the command starts from the workspace root's `bin/`, not the project's.
The bridge responds according to the contract in `AGENTS.md`.

### The temporary folder and subagents

The session's temporary folder is a new folder under `/tmp`, created by the session
and deleted at the end. A subagent is launched with `invoke_subagent`, which the
subagent rule in `AGENTS.md` forbids. A task list is a "task" artifact, not a tool.
