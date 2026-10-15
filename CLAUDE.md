@AGENTS.md

## Claude Code only

The shared rules are in `AGENTS.md`. Claude Code imports it on the first line. This file holds only what is specific to Claude Code.

### Models by role

| Tier in the plan header | Model |
|---|---|
| Large, with the stated effort | Opus, selected from the application menu |
| Medium, with the stated effort | Sonnet. Never `max`. |
| Small, executor only | Haiku 5.5. The orchestrator starts the executor with `model: haiku`. |

The effort is the Claude Code setting of the same name: `medium`, `high`, `xhigh` or `max`. A plan written before 14 October 2026 names the tiers Opus, Sonnet and Haiku. Those are the large, medium and small tiers.

The house agents keep their model and effort in their definition, under "House agents". The session that starts them chooses nothing. One exception applies. The orchestrator starts the executor with `model: haiku` when the plan header asks for the small tier. The effort stays as the definition sets it. Verification on 8 October 2026: the journal of an agent started this way writes `claude-haiku-5-5`.

For why the tiers exist and what each costs, see [splitting work across models](docs/explanation/splitting-work-across-models.md).

### In ultracode, each step of a team chooses its own model

With ultracode on, the session works on its own, with teams of agents (the Workflow tool). It chooses its way of working by itself. Set only the model of each step, given in `agent()` with `model:`. Without it, the agent takes the session's Opus.

| Step | Model |
|---|---|
| Reading and summarizing: code, documents, journals, long outputs | Haiku |
| Running tests, probes, builds | Haiku, or a session command, with no agent |
| Refuting a finding | Haiku, with no limit on skeptics or findings |
| Implementation and repairs | Sonnet, `high` |
| Review, design proposals, judgment | Opus, `high` |
| Design synthesis | Opus, `high` |
| A task that Sonnet did not pass | Opus |

Reason: on 12 October 2026, a team kept Opus for each step, with two skeptics for each of 55 findings. The team exhausted the account limit. Most of the cost comes from the number of agents.

### Compaction summarizes the conversation at 400,000 tokens

The threshold is the `autoCompactWindow` key in `~/.claude/settings.json`, set by `bin/merge-claude-config.py`. After compaction, Claude Code reloads `CLAUDE.md`, the house rules, memory and the skills in progress from disk. The rest of the conversation becomes a summary.

The summary keeps the skill and step in progress, and the work folder. It keeps the question that waits for an answer, and the decisions not yet written to files. At the end of a phase, it suggests `/compact` to the person, with what to keep.

Reason: with the default threshold, specs and plans reread their long conversation at each step.

### Rules load from the starting folder and its parents

When Claude Code starts, it loads `CLAUDE.md` and `AGENTS.md` from the starting folder and its parents. It loads the files of subfolders only when the session reads a file there with the Read tool. Shell `cat` never loads them. `AGENTS.md` loads on its own only with the "Project instructions" setting on `claude-md-and-agents-md`, which `bin/restore-env.sh` sets.

An `@path` import whose target lies outside the starting folder needs approval from Claude Code. Without approval, the import does not expand. Memory loads through a link that `bin/restore-env.sh` also makes. Claude Code loads it and writes it itself.

A `CLAUDE.md` sits beside each `AGENTS.md`. Its import, `@AGENTS.md`, also works where the setting is missing.

### From the root, open the first file of a project with Read

The first file that the Read tool opens in a folder loads the whole `CLAUDE.md` chain, from the root down to that folder. The chain holds the project's `CLAUDE.md`, then that of the game or domain below it. `cat` brings nothing. After the first Read, `cat` is fine.

Before the first change in a repository, read its `CLAUDE.md` and `IMPACT.md` with the Read tool. They load the chain and the map together.

Reason: one Read on a file in a game folder loads the `CLAUDE.md` of the parent project and of the game.

### Skills, plugins and modules

`bin/restore-env.sh` links the house skills under `~/.claude/skills/`. Plugins, pinned in `plugins.lock.json`, sit under `~/.claude/plugins/`. The same script rebuilds both. Invoke a skill with the Skill tool.

The superpowers, ponytail and rtk hooks run at session start, with each message, and before each command.

### The Antigravity worker

The Antigravity bridge command and the quota reserve are in the `execute` skill, under "Who: bridge".

### House agents

Agents live in `agents/`. `bin/restore-env.sh` links them into `~/.claude/agents/`. Start them with the Agent tool, with `run_in_background: false`, one at a time:

| Agent | Model | Who starts it |
|---|---|---|
| `executor` | Sonnet, `high`. Haiku when the plan header asks for the small tier. | the orchestrator, with the plan path |
| `escalation` | Opus, `medium` | the orchestrator, after a task the Sonnet executor did not pass |
| `reader` | Haiku 5.5, `medium`, without the house rules | any session |

The reader compacts at 100,000 tokens and the executor at 200,000, through `autoCompactWindow`.

The reader reads what the session would otherwise reread at each step. That means documentation and web pages, broad code searches, long files on disk, journals and long test outputs. The reader does not read the spec for the plans session, the plan for the executor, or the files the session will change next.

The rule also holds in discussions without a plan. Send to the reader any research with more than two web pages, searched or opened in the browser.

The reader returns at most 2,000 tokens, with the quote and the source of each one. The session checks the figures and the decisive commands itself, with a targeted search in the source.

Reason: the session rereads a page it reads itself, at each later step. The reader keeps that page in its own conversation.

### The work-env-live panel shows usage in every session

The module, a plugin with hooks that draws inside the application, sits in `mods/work-env-live/`. It loads by itself in every session, including those the application starts, through `CLAUDE_CODE_PLUGIN_DIRS`. `bin/merge-claude-config.py` sets that variable when it rebuilds.

Above the box are two colored rows. The row "This chat" shows the API cost, the model and effort, and the context against the compaction threshold. It also shows the share of the week and how long the cache stays warm.

The row "Account" shows the 5-hour and 7-day limits, each with its reset time. After them comes the month's total for Vibe. Vibe chats appear in the views next to the Claude chats, without a share of the Claude week.

The panel opens when the session starts, and `/sessions` reopens it. The **Now** view shows, from any chat, the chats that are working and those with a warm cache. A click on a name opens that chat.

The **Week** view shows the chats in the 7-day limit window, with their agents and the totals per model and per role. From the third web page read directly in chat, the module reminds the model of the reader rule. The person sees a notification.

The share of each chat in the 7-day limit is an estimate. The estimate divides the percentage of the limit by the cost of each chat in the window. Once a minute, the module saves the window to a local file. The end-of-session skill writes the proof for each chat in its work folder.

Everything runs locally, every 10 seconds, with no tokens. The data comes from `usage.py --state`, which reads the logs and application files in `~/.config/Claude/claude-code-sessions/`. A change in `mods/` reloads in open chats too, through `CLAUDE_CODE_PLUGIN_DIR_WATCH`.

Reason: a pause of more than an hour cost 6% of usage. A long discussion on `max` cost 44%. No sign in the application showed either in time.

### The reminder at the end of the response

`bin/merge-claude-config.py` sets the `Stop` hook in the settings. The hook calls `bin/reminder.py` at the end of each response. After the first slip, the session continues with one reminder sentence. A slip is a role requested without its skill, a skill loaded without an announcement, or writes and commits without the stated percentage.

The panel gives the reminder for the third web page, not the hook. At most one reminder comes per response.

Reason: in Vibe's first test, Claude forgot the announcement in 5 of 7 benchmark runs. It also forgot the percentages in 5 of 7, although the rules clearly say so.

### The temporary folder

The temporary folder of the session is the scratchpad the application provides.
