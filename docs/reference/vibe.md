# Mistral Vibe

Mistral Vibe is the terminal coding agent from Mistral. The workspace uses it alongside Claude Code and Antigravity. It uses the same rules, skills and memory, plus its own module, `MISTRAL.md`. This page explains how to install Vibe, where it keeps its files, how to update it, what was tested and which limits matter.

## What is installed

| What | How | Version, read with |
|---|---|---|
| The `vibe` CLI | `uv tool install mistral-vibe` | `vibe --version` |

The user logs in once, at the first run of `vibe`, with the Mistral account. Vibe keeps the login in the system keyring, under `ai.mistral.vibe`, not in a file. That is why a new `VIBE_HOME`, such as the one the bench makes for its tests, finds the login without another login.

Run `bin/restore-env.sh` again. It calls `bin/vibe.sh` unless `vibe` is missing. The script also runs by itself after a change to `MISTRAL.md`, to the house rules or to the memory. The global file is a copy, not a pointer.

## Update

Run `uv tool upgrade mistral-vibe`. After a new version, repeat the tests in "What was tested". The journal format and the tool names are not documented. They can change.

## Where Vibe keeps its files

Vibe keeps its files in `$VIBE_HOME`. The default is `~/.vibe/`.

| Path, under `$VIBE_HOME` | What it holds |
|---|---|
| `AGENTS.md` | The global rules, written by `bin/vibe.sh`: `MISTRAL.md` without its first line, the house rules, the memory index, `using-superpowers` and ponytail. |
| `config.toml` | The settings. `bin/vibe.sh` writes only its own keys: `include_commit_signature`, `active_model`, and the models `large-4`, `large-4-low` and `small-4`, with their prices and compaction thresholds. It keeps the rest. |
| `trusted_folders.toml` | The trusted folders. The root of the workspace is one of them. |
| `hooks.toml` | The hooks. `bin/vibe.sh` writes only `reminder`, a `post_agent` hook that runs `bin/reminder.py`. It keeps the user's own hooks. |
| `logs/session/unified/<session>/journal/*.jsonl` | The session journal, written while the session works. The answer that a `post_agent` hook judges is kept there only in the request sent to the hook. `bin/reminder.py` reads it. |
| `agents/<role>.toml` | The role profiles: `spec`, `plans`, `orchestration`, `execute`, `execute-fast`, `escalation` and `reader`. Each has its own model. Also `helper`, which uses Large 4 with read-only tools (`enabled_tools`). The profiles of the house agents also carry the instructions from the framework's `agents/` folder. A profile without the script's header belongs to the user. The script does not overwrite it. |
| `skills/` | The skills, linked: the house skills, and the skills of the plugins pinned in `plugins.lock.json`. |
| `logs/session/unified/<id>/` | The journal of each session, with the cumulative tokens. |
| `tmp/` | The temporary folder of the sessions. |

A model that is not declared in `config.toml` cannot be chosen. Vibe silently switches to the default model. The warning appears only in `vibe.log`.

## What was tested

The loading tests put one unique word in each rules file. They asked Vibe, with `vibe -p`, which words it sees. The behavior tests gave Vibe the bench's execution task and the start of a spec, in a throwaway workspace.

| What | The result |
|---|---|
| The rules files | All of them: `MISTRAL.md`, the house rules, the memory, and the root and project `AGENTS.md`. |
| The skills | All linked skills. Vibe follows the links. |
| Execution, on Large 4 | The `execute` skill, followed step by step: state, map, branch, the test left to fail first, one commit per task, and the final check. |
| The start of a spec, on Large 4 | The steps of the `spec` skill, with the announcement `Using brainstorming to …` and one question. |
| The reader, on Small 4 | Answers with a quote and a source. One figure was wrong, but the quote made it visible. |
| The compaction | It starts at the threshold set for the model in `config.toml`. |
| The thinking level | `low` sends the model "no thinking". `medium`, `high` and `max` give the same thinking. |

The runs of the bench, for spec, plans and execution, are in the folder of the work item that brought in Vibe.

## Limits that matter

- **If the input is not closed, `vibe -p` waits forever.** Every unattended run uses `</dev/null`.
- **The `bash` tool stops a command after 300 seconds.** Its schema rejects a larger `timeout_seconds` ("3600 is greater than the maximum of 300"). Start a run of the executor with `tools.process.start`. Wait for it with `tools.process.output`.
- **The profile overrides the variable `VIBE_ACTIVE_MODEL`.** Choose the model with `--agent`.
- **The quota is a sum per month.** It is not a limit per hour. An unattended run receives `--max-price`.
- **Vibe computes the sum in euros.** It is the dollars × 0.85, the rate on the pricing page. `bin/usage.py --vibe-sessions` gives the estimate for the month, based on the tokens. The amount that Mistral deducted is visible only in the account console. The Admin API, the only programmatic path, is for Enterprise accounts only.
- **Hooks run only at `pre_tool`, `post_tool` and `post_agent`.** Nothing runs when the user sends a message. That is why ponytail is in the global file, not in a hook.

## Models

The table of models by role, with the profile of each tier, is in [MISTRAL.md](../../MISTRAL.md). The prices in `config.toml` come from the [Mistral pricing page](https://docs.mistral.ai/inference/pricing). `grep price ~/.vibe/config.toml` shows the ones that are set.

Models that are not Mistral models come from the user's `config.toml`. The script copies their providers and the models with thinking disabled. Then it makes one alias per thinking level, `<alias>-<level>`, with a profile of the same name. A setup with another `VIBE_HOME`, such as the bench's, finds them the same way. Choose the level with `--agent qwen-agent-low`. Set the source file with `VIBE_SOURCE`.

Each house alias has four profiles. The alias itself is the first. Its executor (`<model>-execute[-<level>]`) uses the instructions from `agents/executor.md`. The lead profile of the GVS5H method (`<model>-gvs5h[-<level>]`) is the third. Its worker (`<model>-worker[-<level>]`) is the fourth.

All of them carry the instructions for house models, from `INSTR_HOUSE` in the script. They cover the reader for large searches and the helper for blockages. They also cover the executor of the same level and the instruction to write to the human in English. That text is the place to tune a house model, not `MISTRAL.md`.
