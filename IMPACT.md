# Impact and dependency map

Measured by reading the tools in `bin/`, `.gitignore`, and the links that `bin/restore-env.sh` makes. The "what breaks" column comes from what the code does. It does not come from what might be assumed.

## Verifiable

The fourth column is a command. The command must exit with 0 as long as the row remains true. `bin/check-maps.sh` runs all of them.

| what changes | what breaks | what it depends on | verification |
|---|---|---|---|
| `bin/check-docs.py` | the line threshold and the paragraph threshold, the exemption of records, the way sentences are split, reading `example/`, the size caps of `AGENTS.md` and `CLAUDE.md`, in `SIZE_CAP` | `tests/test-check-docs.py` fixes them all | `python3 tests/test-check-docs.py >/dev/null` |
| `bin/check-docs.py --criteria` and the form of the criteria in the `spec` skill | the coverage of the criteria by the `plans` and `orchestration` skills. A spec written in another form would be skipped without any failure | the patterns `CRITERIA_SECTION`, `CRITERION` and `CRITERIA_HEAD` in `check-docs.py`, fixed by its test, and the example in `skills/spec/SKILL.md` | `python3 tests/test-check-docs.py >/dev/null && grep -q -- '- \*\*C1\*\* (command:' skills/spec/SKILL.md` |
| `bin/values.py` | the "no value lost" verifier of every documentation rewrite, here and in projects | `tests/test-values.py`, on fabricated documents in a git repository | `python3 tests/test-values.py >/dev/null` |
| `bin/documents.py` | the documents gate, here and in projects: a stale document would pass, or a current one would be asked for again and again | `tests/test-documents.py`, on fabricated git repositories with fixed times | `python3 tests/test-documents.py >/dev/null` |
| `bin/diagrams.html` and the `diagrams` configuration in `.claude/launch.json` | the check that every Mermaid diagram renders. `check-docs.py` skips code blocks, so nothing else catches it | the page requests the document from the server that the configuration runs | `grep -q '"diagrams"' .claude/launch.json && test -f bin/diagrams.html` |
| the name of the `example/` folder | `check-docs.py` would skip it without a word. It reads the folder by name | the constant `EXAMPLE_FOLDER` in `bin/check-docs.py` | `grep -q '^EXAMPLE_FOLDER = "example"$' bin/check-docs.py && test -f example/README.md` |
| the forms in the skills that the example follows: the plan header, the state file, the handoff, the closing and a folder's README | the example would fall behind them without anyone seeing it | `tests/test-example.py` reads them from the skills on every run | `python3 tests/test-example.py >/dev/null` |
| the prices and fields that `bin/usage.py` reads, the state of the chats, and the window files | the figures used to judge the architecture: the cost by role, model and effort, with the session's agents. The panel, the weekly file and the evidence in the work folders. The cost of Vibe sessions, in estimated euros | the format of the Claude Code logs and of the Vibe sessions, undocumented. Deduplication on `message.id`. The format of the desktop application's session files in `~/.config/Claude/claude-code-sessions/`, undocumented | `python3 tests/test-usage.py >/dev/null` |
| `bin/move-md.py` | the links after a record moves or a work item closes | `tests/test-move-md.py`, on a fabricated repository | `python3 tests/test-move-md.py >/dev/null` |
| `plugins.lock.json` | restoring the environment on a new machine | the pinned SHAs of the plugins | `./bin/check-lock.sh >/dev/null` |
| the map in `README.md` or the structure of `docs/` | the clickable reachability of the documents | `check-docs.py` starts from `README.md` | `python3 bin/check-docs.py . >/dev/null` |
| the name of the documentation skill's folder | the symlink in `~/.claude/skills/` | `restore-env.sh` links it by name, from its list | `grep -qw 'documentation' bin/restore-env.sh` |
| the name of the closing skill's folder | the same symlink, plus the invocation `/end-of-session` | `restore-env.sh` links it by name | `grep -qw 'end-of-session' bin/restore-env.sh` |
| the length of the documentation skill | the cost of each invocation | the threshold is under 150 lines | `test "$(wc -l < skills/documentation/SKILL.md)" -lt 150` |
| the length of the closing skill | the same cost at each invocation | the same threshold | `test "$(wc -l < skills/end-of-session/SKILL.md)" -lt 150` |
| the name of the execution skill's folder | the symlink in `~/.claude/skills/`, plus the invocation `/execute` | `restore-env.sh` links it by name | `grep -qw 'execute' bin/restore-env.sh` |
| the length of the execution skill | the cost of each invocation | the same threshold | `test "$(wc -l < skills/execute/SKILL.md)" -lt 150` |
| the name of the spec skill's folder | the symlink in `~/.claude/skills/`, plus the invocation `/spec` | `restore-env.sh` links it by name | `grep -qw 'spec' bin/restore-env.sh` |
| the length of the spec skill | the cost of each invocation | the threshold is under 150 lines | `test "$(wc -l < skills/spec/SKILL.md)" -lt 150` |
| the name of the plans skill's folder | the symlink in `~/.claude/skills/`, plus the invocation `/plans` | `restore-env.sh` links it by name | `grep -qw 'plans' bin/restore-env.sh` |
| the length of the plans skill | the cost of each invocation | the threshold is under 150 lines | `test "$(wc -l < skills/plans/SKILL.md)" -lt 150` |
| the name of the orchestration skill's folder | the symlink in `~/.claude/skills/`, plus the invocation `/orchestration` from the handoff | `restore-env.sh` links it by name | `grep -qw 'orchestration' bin/restore-env.sh` |
| the length of the orchestration skill | the cost of each invocation, paid at each step of a long session | the threshold is under 150 lines | `test "$(wc -l < skills/orchestration/SKILL.md)" -lt 150` |
| the names of the framework's agents, `agents/` | the orchestrator and `CLAUDE.md` call them by name. The `framework-subagents` check of the bench admits them by name | the files in `agents/`, linked by `restore-env.sh` | `ls agents/reader.md agents/executor.md agents/escalation.md >/dev/null && grep -q '"reader", "executor", "escalation"' bin/bench/checks.py` |
| the model and effort in the head of an agent | the role would run on another model than `CLAUDE.md` says, with no sign | the `model` and `effort` fields of the definition | `grep -q '^effort: high$' agents/executor.md && grep -q '^model: opus$' agents/escalation.md && grep -q '^omitClaudeMd: true$' agents/reader.md && grep -q '^model: claude-haiku-5-5$' agents/reader.md` |
| the personal layer, `records/` | what leaves tracking. Without the leading slash, the pattern would also swallow `template/records/` | `.gitignore` names it, anchored at the root | `grep -q '^/records/' .gitignore && ! git check-ignore -q template/records/INDEX.md` |
| the links made by `bin/restore-env.sh` | a real skill folder would receive the link inside it. A project's memory would stay unlinked | `tests/test-restore-links.sh`, in a fabricated HOME | `bash tests/test-restore-links.sh >/dev/null` |
| exit code 77 in `bin/check-maps.sh` | a check that cannot run on this machine would keep the map red | `tests/test-check-maps.sh` | `bash tests/test-check-maps.sh >/dev/null` |
| a copy of the template, `projects/ai-workspace-template/` | `check-maps.sh` at the root also runs its map. The source mark measures how far the copy drifted from its source | `.source-commit` | `test ! -d projects/ai-workspace-template \|\| test -f projects/ai-workspace-template/.source-commit` |
| the name of the journal index | references from rules and guides to the index | all of them name it `INDEX.md` | `grep -q 'records/journal/INDEX.md' AGENTS.md && ! /usr/bin/grep -rq 'records/journal/README.md' AGENTS.md CLAUDE.md README.md docs skills` |
| the name of the state file | exemptions in `check-docs.py` and the row in `.gitignore` | both name it `STATE.md` | `grep -q 'STATE.md' .gitignore` |
| the version of the Claude application, at its automatic update | commands in the guides that call the `claude` binary | the guides look for the binary. They do not write it on a path with a version number | `! /usr/bin/grep -rqE 'claude-code/[0-9]' README.md docs` |
| the place of the work items, `work/open/` in the records of the repository | paths in `AGENTS.md`, in the reference of the state file and in the template | the folder name, written in all three | `grep -q 'work/open' AGENTS.md && grep -q 'records/work/open' skills/end-of-session/references/state-and-records.md && test -f template/records/work/INDEX.md` |
| the old names of the records and of the documentation: `registre/` with `planuri/` and `specuri/`, `documentatie/`, `ghiduri/` | an old path in a skill or in `AGENTS.md` would send a session into a folder that no longer exists | the paths written in prose, which `check-docs.py` does not see in skills. `tests/` and `bin/check-docs.py` are exempt. The move tool's test makes up old records on purpose. The tool that refuses old names must name them | `! git grep -q -e 'registre/planuri' -e 'registre/specuri' -e 'documentatie/' -e 'ghiduri/' -- ':!records' ':!IMPACT.md' ':!tests' ':!bin/check-docs.py'` |
| the rule that stops the framework's links to `records/` | the template would ship with links to someone else's history, broken on any other machine | `tests/test-check-docs.py` fixes it, in both kinds of repository | `python3 tests/test-check-docs.py >/dev/null` |
| the `AGENTS.md`–module pairs | without the setting that restore puts in place, Claude Code would not read an `AGENTS.md` without a `CLAUDE.md` beside it. An unimported module would keep rules outside the shared source | the `MODULE:` rule in `bin/check-docs.py`, fixed by its test | `python3 tests/test-check-docs.py >/dev/null` |
| the size of `AGENTS.md` | above 24,000 bytes, Antigravity truncates the file without saying so | the limit in its documentation | `test "$(wc -c < AGENTS.md)" -lt 23800` |
| `bin/antigravity.sh` and `bin/antigravity-memento.py` | the skills, the loading of superpowers, the modes, the memento note and each folder's local files, in Antigravity | `tests/test-antigravity.sh`, in a fabricated HOME | `bash tests/test-antigravity.sh >/dev/null` |
| the project skeleton, `template/` | a new project would fail documentation verification right at step 5 of its guide | `check-docs.py`, run on a copy of the skeleton made into a repository | `( T=$(mktemp -d) && cp -r template/. "$T" && git -C "$T" init -q && python3 bin/check-docs.py "$T" >/dev/null; r=$?; rm -rf "$T"; exit $r )` |
| `bin/tool-bridge.sh` | It hands tasks to the other tool, `agy`, `claude` or `vibe`. It deletes the working copy on any exit. It produces the diff only after the verifier passes. It keeps the contract's exit codes and Vibe's money cap | `tests/test-tool-bridge.sh`, with dummy agents | `bash tests/test-tool-bridge.sh >/dev/null` |
| `bin/bench/` | The bench runs the miniature house and its variant, with the adapters `agy`, `claude` and `vibe`. It runs the simulated human and the checks. It makes the manners checks mandatory with `--manners`. It checks the language of the messages. The `search` stage uses the called helper and the tested answer. The journeys cover one house model. They also cover the Claude journey on one model, with `--same-model`, and the full journey with the handoff. They check the acceptance and the manners of each session. The bench estimates Vibe's cost in euros. The `blind` comparison and the exit codes 0, 1, 3 and 4 complete it | `tests/test-bench.py`, with dummy tools in a fabricated HOME and workspace | `python3 tests/test-bench.py >/dev/null` |
| calling Antigravity from restore | a new machine with Antigravity would stay unlinked | `restore-env.sh` calls the script by name | `grep -q 'bin/antigravity.sh' bin/restore-env.sh` |
| `bin/vibe.sh` and the definitions in `agents/` | In Vibe, these break. The global rules. The models, with their prices and thresholds. The trusted root. The role profiles, with the framework agents' instructions. The read-only helper. The profiles of the house models, with their instructions. The skills and the reminder hook. The human's keys in `config.toml`. Their hooks in `hooks.toml` | `tests/test-vibe.sh`, in a fabricated HOME | `bash tests/test-vibe.sh >/dev/null` |
| the profile names of the house models, `<model>-executie`, `-gvs5h`, `-muncitor`, with `-<level>` | `framework_agent` in `bin/bench/tools.py` would no longer recognize the executor and the worker. So `framework-subagents` would fail on a valid session | `bin/bench/tools.py` and `bin/bench/bench.py journey` | `bash tests/test-vibe.sh >/dev/null && python3 tests/test-bench.py >/dev/null` |
| calling Vibe from restore | a machine with Vibe would keep old rules or have none | `restore-env.sh` calls the script by name | `grep -q 'bin/vibe.sh' bin/restore-env.sh` |
| `MISTRAL.md` | Vibe's global file comes from this file, without its first line. Any other first line would enter Vibe's rules | `bin/vibe.sh` cuts the first line, and `check-docs.py` requires the import there | `head -1 MISTRAL.md \| grep -qx '@AGENTS.md'` |
| `bin/merge-claude-config.py` | the settings and plugins of a machine where Claude Code is already in use | `tests/test-merge-claude-config.py` fixes the merge, the empty `HOME` and the refusal of broken JSON. It fixes the mod folders, the panel and the guard in `CLAUDE_CODE_PLUGIN_DIRS`. It fixes the reminder's `Stop` hook, once, beside the user's own | `python3 tests/test-merge-claude-config.py >/dev/null` |
| `bin/reminder.py` | the reminder at the end of each answer, in any Claude or Vibe session. A wrong reminder costs a paid step. A broken one could make the session loop | `tests/test-reminder.py`, on fabricated answers, called as a hook. It reads the steps with the parsers in `bin/bench/tools.py` and judges with `bin/bench/checks.py`, so a change there affects it. In Vibe it reads the session log, whose format any new version of Vibe changes | `python3 tests/test-reminder.py >/dev/null` |
| the `mods/work-env-live` panel | The lines above the box, in any session. The `/sessions` command, with its Now and Week views. The click through to the chat, and the research note. It reads the fields of `usage.py --state`, which reads the desktop application's files in `~/.config/Claude/claude-code-sessions/` and the Vibe session logs in `~/.vibe/logs/session/unified/`. It finds its root from the folder name that `merge-claude-config.py` sets | `claude plugin validate mods/work-env-live >/dev/null && claude plugin test mods/work-env-live >/dev/null && python3 tests/test-usage.py >/dev/null` |
| the `mods/records-guard` guard | A full write that leaves a records `INDEX.md` or a `MEMORY.md` under half would pass. A wrong judgment would refuse a good write in any session | `classic.PreToolUse` and `$.fs.stat` with `resolve`, from the Claude Code types. The folder that `merge-claude-config.py` sets | `claude plugin validate mods/records-guard >/dev/null && claude plugin test mods/records-guard >/dev/null` |
| the `RECORDS` rule in `bin/check-docs.py` | a journal entry, pitfall or decision rewritten after its commit would pass unnoticed. Without the ignored links, every move with `move-md.py` would fail | the git history of the records, read in one pass, fixed by `tests/test-check-docs.py` | `python3 tests/test-check-docs.py >/dev/null` |
| the name of the local workers skill's folder | the symlink in `~/.claude/skills/`, plus the invocation `/local-workers` | `restore-env.sh` links it by name | `grep -qw 'local-workers' bin/restore-env.sh` |
| the length of the local workers skill | the cost of each invocation | the threshold is under 150 lines | `test "$(wc -l < skills/local-workers/SKILL.md)" -lt 150` |
| the name of the writing skill's folder, `asd-ste100` | the symlink in `~/.claude/skills/`, and the references in `AGENTS.md`. `restore-env.sh` links it by name | Antigravity and Vibe link the whole `skills/` folder | `grep -qw 'asd-ste100' bin/restore-env.sh && grep -q 'asd-ste100' AGENTS.md` |
| the copy of the English skill, `skills/asd-ste100/` | copying a new version over it loses a hand-made change | `SOURCE` names the repository and the commit. The copy came from it. | `test -f skills/asd-ste100/SOURCE && python3 -I skills/asd-ste100/scripts/ste-lint.py --selftest >/dev/null` |
| the documents map, `## Documents` | a document left behind its code, or one with no row in the map | `bin/documents.py` of the workspace | `python3 bin/documents.py . >/dev/null && python3 bin/documents.py . --complete >/dev/null` |

## Unverifiable

⚠ The rows below are **not** covered by `check-maps.sh`. They are conceptual dependencies, which do not fit into a command. They are re-read by hand when something big changes.

- If the model of the five kinds of document changes, these break at once. They are the documentation skill, `template/`, and the map in every `README.md` written after it.
- If git stops ignoring the state file, the safety net would exist. Then the reason for the closing skill's confirmation before it rewrites the file breaks.
- If `projects/` leaves `.gitignore`, `check-docs.py` starts reading the projects' documents too, and "the environment is clean" ends up being about another tree.

## Documents

Each document sits next to the code that it describes. `bin/documents.py` of the workspace asks for a reread of the document when its code changes after it. `—` says that the document describes no code.

| document | the code that it describes |
|---|---|
| `README.md` | `bin/restore-env.sh`, `bin/check-docs.py`, `bin/check-maps.sh`, `bin/check-lock.sh`, `bin/values.py`, `bin/diagrams.html`, `bin/make-lock.py`, `plugins.lock.json`, `agents/*.md`, `test`, `.claude/launch.json` |
| `.claude/skills/welcome/SKILL.md` | `bin/restore-env.sh`, `template` |
| `docs/README.md` | `plugins.lock.json` |
| `docs/explanation/what-each-plugin-does.md` | `plugins.lock.json` |
| `docs/explanation/conflicts-and-pitfalls.md` | `plugins.lock.json` |
| `docs/explanation/how-a-plugin-applies.md` | `plugins.lock.json` |
| `docs/explanation/splitting-work-across-models.md` | `agents/*.md`, `bin/usage.py`, `bin/merge-claude-config.py`, `bin/bench/bench.py`, `skills/execute/SKILL.md`, `skills/orchestration/SKILL.md` |
| `docs/how-to/add-a-new-tool.md` | `bin/check-docs.py`, `bin/antigravity.sh`, `bin/vibe.sh`, `bin/restore-env.sh`, `bin/bench/tools.py`, `bin/bench/bench.py`, `skills/end-of-session/references/state-and-records.md`, `tests/test-bench.py` |
| `docs/how-to/switch-modes.md` | `plugins.lock.json` |
| `docs/how-to/trigger-a-skill-from-a-prompt.md` | `plugins.lock.json`, `skills/execute/SKILL.md` |
| `docs/how-to/load-skills-at-startup.md` | `bin/antigravity.sh`, `bin/merge-claude-config.py` |
| `docs/how-to/start-a-new-project.md` | `template/README.md`, `template/AGENTS.md`, `template/CLAUDE.md`, `template/IMPACT.md`, `template/STATE.md`, `template/.gitignore`, `template/records`, `bin/antigravity.sh`, `bin/check-maps.sh` |
| `docs/how-to/fix-an-environment-problem.md` | `bin/check-docs.py` |
| `docs/how-to/write-a-task-for-someone-else.md` | `bin/tool-bridge.sh`, `skills/execute/SKILL.md` |
| `docs/how-to/keep-documentation-current.md` | `bin/documents.py` |
| `docs/how-to/check-a-plugin-works.md` | `plugins.lock.json`, `bin/documents.py`, `bin/merge-claude-config.py` |
| `docs/reference/antigravity.md` | `bin/antigravity.sh`, `bin/antigravity-memento.py`, `bin/tool-bridge.sh` |
| `docs/reference/bench.md` | `bin/bench`, `tests/test-bench.py`, `bin/usage.py`, `bin/antigravity.sh` |
| `docs/reference/glossary.md` | — |
| `docs/reference/ponytail.md` | `plugins.lock.json` |
| `docs/reference/rtk.md` | `plugins.lock.json` |
| `docs/reference/structure.md` | `.gitignore`, `plugins.lock.json`, `.claude/launch.json`, `agents/*.md`, `bin/reminder.py`, `bin/antigravity-memento.py`, `bin/antigravity.sh`, `bin/check-docs.py`, `bin/check-lock.sh`, `bin/check-maps.sh`, `bin/usage.py`, `bin/diagrams.html`, `bin/documents.py`, `bin/make-lock.py`, `bin/merge-claude-config.py`, `bin/move-md.py`, `bin/tool-bridge.sh`, `bin/restore-env.sh`, `bin/values.py`, `bin/vibe.sh`, `bin/bench`, `skills/*/SKILL.md`, `template`, `test`, `tests` |
| `docs/reference/superpowers.md` | `plugins.lock.json` |
| `docs/reference/vibe.md` | `bin/vibe.sh`, `bin/reminder.py`, `bin/usage.py`, `MISTRAL.md`, `agents/*.md` |
| `docs/tutorial/first-work-item.md` | `skills/spec/SKILL.md`, `skills/plans/SKILL.md`, `skills/orchestration/SKILL.md`, `skills/end-of-session/SKILL.md` |
