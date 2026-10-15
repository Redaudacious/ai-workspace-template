@AGENTS.md

## Mistral Vibe only

The shared rules are in `AGENTS.md`, imported on the first line. This file holds only what belongs to Mistral Vibe.

### Vibe gets the rules through its global file

Vibe reads only files named `AGENTS.md` on its own. It reads the global one, from `$VIBE_HOME/AGENTS.md`. It reads the project ones, from the open folder up to the trusted folder. It adds the subfolder files when it reads a file in that folder with the `read_file` tool.

In Vibe, nobody reads the `@AGENTS.md` import above. It is there for `check-docs.py`, which keeps the pair matched.

`bin/vibe.sh` writes the global file. `bin/restore-env.sh` calls `bin/vibe.sh`. The file holds, one after another: this module, the memory index, `using-superpowers` and the ponytail mode. A change to any of them reaches Vibe only after a new run of `bin/vibe.sh`.

The workspace root is a trusted folder in `$VIBE_HOME/trusted_folders.toml`. Without it, Vibe does not read the root `AGENTS.md` in a project.

### Look up outside facts online before comparing options

Look up facts from outside the framework online before comparing options. Do not rely only on the local machine. Examples: what `cron` does, how `systemd` works, which tool exists. Write the facts into the spec with their source. The reader does the research. You make at most two searches or page reads in the whole session. This includes the checks of figures and versions. Ask the reader for a third, with a new question.

Reason: on 10 October 2026, Large 4 broke the rule, though the framework already wrote it. The reminder comes only at the end of the answer. It is too late to correct a search.

### Models by role

All roles run on Mistral Large 4. The reader runs on Mistral Small 4. The bench can change the table. The decision is in the spec of the Mistral Vibe work.

| Tier, in the plan header | Model in Vibe | How to pick it |
|---|---|---|
| large, with the effort written | Mistral Large 4, with thinking | `vibe --agent spec`, `plans`, `orchestration` or `escalation` |
| medium, with the effort written | Mistral Large 4, with thinking | `vibe --agent execute` |
| small, executor only | Mistral Large 4, without thinking | `vibe --agent execute-fast` |
| reader | Mistral Small 4, `mistral-small-2603` | `vibe --agent reader -p "<question>" </dev/null` |

The profiles are in `$VIBE_HOME/agents/`. `bin/vibe.sh` writes them. Each profile sets the model. A profile overrides the `VIBE_ACTIVE_MODEL` variable. Choose the tier with the profile, not with the variable. The profiles for the executor, escalation and reader also carry the instructions of the framework agents, from `agents/`. In a session, `/model` and `/thinking` change them.

Automatic compaction starts at 400,000 tokens on Large 4 and at 200,000 tokens on Small 4. The thresholds are in `config.toml`. `/compact` does it by hand.

`Devstral (local)` in the list is a model that runs on a local machine. It is not a Mistral model. Do not use it until the local workers file has a row for it.

### The framework's effort maps to `thinking`

The Mistral API has only two levels: without thinking and with thinking.

| Framework effort | `thinking` in Vibe | What the model gets |
|---|---|---|
| `medium`, `high`, `xhigh`, `max` | `high` | with thinking |
| a mechanical plan, on the small tier | `low`, in the `execute-fast` profile | without thinking |

`off` sends nothing, and the model chooses on its own. The framework does not use it.

### The quota is a sum per month

Each request reduces the account's monthly sum, at the model's API price. The account blocks spending beyond the sum. When the sum runs out, Vibe stops until the 1st of the month.

A run without a human gets `--max-price`, in dollars. The values are 2 for an execution and 3 for an escalation. A task sent through the bridge gets 1. A question to the reader gets 0.20.

### Commits do not carry Vibe's signature

`include_commit_signature = false` in `$VIBE_HOME/config.toml`, set by `bin/vibe.sh`. Otherwise Vibe adds `Co-Authored-By` on its own, and `AGENTS.md` forbids it.

### Skills, questions and subagents

The framework links its skills, and the skills of the pinned plugins, in `$VIBE_HOME/skills/`. Invoke a skill with the `skill` tool. Ask a question with options using `ask_user_question`.

Announce the skill in the same reply as the call of the `skill` tool, before the call: `Using <skill> to <purpose>`. Announce `end-of-session` the same way.

Reason: on 14 October 2026, Large 4 forgot the announcement in `spec-greeting` and `spec-temperature`. After the hook reminder, it wrote 14 broken messages in a row. The `messages-in-romanian` check failed.

The framework agents are separate Vibe runs. Start them from the terminal, one at a time. Wait for each to finish: `vibe --agent execute`, `vibe --agent escalation`, `vibe --agent reader`. Close their input with `</dev/null`. Without it, the run waits forever. A subagent started with the `task` tool runs on the session model. So it cannot be the reader on Small 4.

The `bash` tool cuts a command after 300 seconds. Its schema refuses a `timeout_seconds` above that. Start a run that lasts longer, such as an executor, with `tools.process.start`. Wait for it with `tools.process.output` (`waitMs: 30000` per call), until it ends.

### Research with more than two web pages goes to the reader

The reader does research that needs more than two web pages, searched or opened: `vibe --agent reader -p "<question>" --max-price 0.20 </dev/null`, on Small 4. The reader returns the answer with the quotes and the source of each.

Check the figures and decisive commands through the reader as well, with a second, targeted question. In total, the session has at most two pages of its own.

Reason: when the session reads a page directly, it rereads that page at every later step. When the reader reads a page, the page stays in its run. In the first test of Vibe, Large 4 made 13 searches and page reads on its own for a single spec.

### The reminder at the end of the answer

After each answer, the `post_agent` hook in `$VIBE_HOME/hooks.toml`, written by `bin/vibe.sh`, calls `bin/reminder.py`.

At the first lapse in the answer, the script sends the model a reminder. The reminder has the form of the required sentence and covers all lapses at once. The lapses are:

- a requested role (spec, plans or orchestration) without its skill loaded
- a skill loaded without an announcement
- writes or a commit without the stated percentage
- a third web page read directly in a session that loaded a skill

At most one reminder comes per answer.

Reason: in the first test, Large 4 forgot the announcement and the percentages in all the runs, though the rules were in its global file.

### The temporary folder

The session temporary folder is `$VIBE_HOME/tmp/`.
