# The impact and dependency map

Measured by inspecting the tools in `bin/`, `.gitignore`, and the symlinks
established by `bin/restore-env.sh`. The "what breaks" column reflects what the code
actually does, rather than assumptions.

## Verifiable

The fourth column contains a command that must exit with 0 as long as the row remains
true. `bin/check-maps.sh` runs them all.

| what changes | what breaks | what it depends on | verification |
|---|---|---|---|
| `bin/check-docs.py` | the line threshold and the paragraph one, the exemption of records, the way sentences are split, reading `example/` | `tests/test-check-docs.py` fixes them all | `python3 tests/test-check-docs.py >/dev/null` |
| `bin/values.py` | the "no value lost" verifier of every documentation rewrite, here and across projects | `tests/test-values.py`, on documents fabricated in a git repository | `python3 tests/test-values.py >/dev/null` |
| `bin/diagrams.html` and the "diagrams" configuration in `.claude/launch.json` | the check that every Mermaid diagram renders; `check-docs.py` skips code blocks, so nothing else catches it | the page requests the document from the server started by the configuration | `grep -q '"diagrams"' .claude/launch.json && test -f bin/diagrams.html` |
| the name of the `example/` folder | `check-docs.py` would skip it without a word: it reads it by name | the constant `EXAMPLE_FOLDER` in `bin/check-docs.py` | `grep -q '^EXAMPLE_FOLDER = "example"$' bin/check-docs.py && test -f example/README.md` |
| the forms in skills that the example follows: the plan header, the state file, the handoff, the closing, a folder's README | the example would fall behind them without it showing | `tests/test-example.py` reads them from the skills on every run | `python3 tests/test-example.py >/dev/null` |
| the prices and fields read by `bin/usage.py` | the figures by which it is judged whether a handoff between models was worth it | the format of Claude Code logs, deduplication on `message.id` | `python3 tests/test-usage.py >/dev/null` |
| `bin/move-md.py` | links after moving a record or closing a work item | `tests/test-move-md.py`, on a fabricated repository | `python3 tests/test-move-md.py >/dev/null` |
| `plugins.lock.json` | restoring the environment on a new machine | the pinned SHAs of the plugins | `./bin/check-lock.sh >/dev/null` |
| the map in `README.md` or the structure of `docs/` | clickable reachability of the documents | `check-docs.py` starts from `README.md` | `python3 bin/check-docs.py . >/dev/null` |
| the name of the documentation skill's folder | the symlink in `~/.claude/skills/` | `restore-env.sh` links it by name, from its list | `grep -qw 'documentation' bin/restore-env.sh` |
| the name of the closing skill's folder | the same symlink, plus the invocation `/end-of-session` | `restore-env.sh` links it by name | `grep -qw 'end-of-session' bin/restore-env.sh` |
| the length of the documentation skill | the cost of each invocation | the threshold is under 150 lines | `test "$(wc -l < skills/documentation/SKILL.md)" -lt 150` |
| the length of the closing skill | the same cost at each invocation | the same threshold | `test "$(wc -l < skills/end-of-session/SKILL.md)" -lt 150` |
| the name of the execution skill's folder | the symlink in `~/.claude/skills/`, plus the invocation `/execute` | `restore-env.sh` links it by name | `grep -qw 'execute' bin/restore-env.sh` |
| the length of the execution skill | the cost of each invocation | the same threshold | `test "$(wc -l < skills/execute/SKILL.md)" -lt 150` |
| the personal layer, `records/` | what leaves tracking; without the leading slash the pattern would swallow `template/records/` too | `.gitignore` names it by name, anchored at the root | `grep -q '^/records/' .gitignore && ! git check-ignore -q template/records/INDEX.md` |
| the symlinks made by `bin/restore-env.sh` | a real skill folder would receive the symlink inside it; a project's memory would remain unlinked | `tests/test-restore-links.sh`, in a fabricated HOME | `bash tests/test-restore-links.sh >/dev/null` |
| exit code 77 in `bin/check-maps.sh` | a check that cannot run on this machine would keep the map red | `tests/test-check-maps.sh` | `bash tests/test-check-maps.sh >/dev/null` |
| the template's copy, `projects/ai-workspace-template/` | `check-maps.sh` at the root runs its map too; the source marker measures how far it drifted | `.source-commit` | `test ! -d projects/ai-workspace-template \|\| test -f projects/ai-workspace-template/.source-commit` |
| the name of the journal index | references from rules and guides to the index | all of them name it `INDEX.md` | `grep -q 'records/journal/INDEX.md' AGENTS.md && ! /usr/bin/grep -rq 'records/journal/README.md' AGENTS.md CLAUDE.md README.md docs skills` |
| the name of the state file | exemptions in `check-docs.py` and the row in `.gitignore` | both name it `STATE.md` | `grep -q 'STATE.md' .gitignore` |
| the version of the Claude application, at its automatic update | commands in the guides that call the `claude` binary | the guides look for the binary, they do not write it on a path with a version number | `! /usr/bin/grep -rqE 'claude-code/[0-9]' README.md docs` |
| the place of the work items, `work/open/` in the repository's records | paths in `AGENTS.md`, in the state file's reference and in the template | the folder name, written in all three | `grep -q 'work/open' AGENTS.md && grep -q 'records/work/open' skills/end-of-session/references/state-and-records.md && test -f template/records/work/INDEX.md` |
| the rule that stops framework links to `records/` | the template would ship with links to someone else's history, broken on any other machine | `tests/test-check-docs.py` fixes it, in both kinds of repository | `python3 tests/test-check-docs.py >/dev/null` |
| the `AGENTS.md`–module pairs | without the setting configured by restore, Claude Code would not read an `AGENTS.md` without `CLAUDE.md` beside it, and an unimported module would keep rules outside the shared source | the `MODULE:` rule in `bin/check-docs.py`, fixed by its test | `python3 tests/test-check-docs.py >/dev/null` |
| the size of `AGENTS.md` | above 24,000 bytes, Antigravity truncates the file silently | the limit in its documentation | `test "$(wc -c < AGENTS.md)" -lt 23800` |
| `bin/antigravity.sh` | skills, starting superpowers, modes and each folder's local files, in Antigravity | `tests/test-antigravity.sh`, in a fabricated HOME | `bash tests/test-antigravity.sh >/dev/null` |
| the project skeleton, `template/` | a new project would fail documentation verification right at step 5 of its guide | `check-docs.py`, run on a copy of the skeleton made into a repository | `( T=$(mktemp -d) && cp -r template/. "$T" && git -C "$T" init -q && python3 bin/check-docs.py "$T" >/dev/null; r=$?; rm -rf "$T"; exit $r )` |
| `bin/tool-bridge.sh` | tasks delegated to the other tool: working copy deleted on any exit, diff produced only after the verifier passes, contract exit codes | `tests/test-tool-bridge.sh`, with dummy agents | `bash tests/test-tool-bridge.sh >/dev/null` |
| calling Antigravity from restore | a new machine with Antigravity would remain unlinked | `restore-env.sh` calls the script by name | `grep -q 'bin/antigravity.sh' bin/restore-env.sh` |
| `bin/merge-claude-config.py` | settings and plugins of a machine where Claude Code is already used | `tests/test-merge-claude-config.py` fixes the merge, the empty `HOME` and rejection of broken JSON | `python3 tests/test-merge-claude-config.py >/dev/null` |
| the name of the workers skill's folder | the symlink in `~/.claude/skills/`, plus the invocation `/local-workers` | `restore-env.sh` links it by name | `grep -qw 'local-workers' bin/restore-env.sh` |
| the length of the workers skill | the cost of each invocation | the threshold is under 150 lines | `test "$(wc -l < skills/local-workers/SKILL.md)" -lt 150` |
| the language of the tracked files | "run without knowing the author", which is the whole point of this repository | no tracked file carries Romanian diacritics | `! git grep -lqP '(*UTF)[\x{103}\x{E2}\x{EE}\x{219}\x{21B}\x{102}\x{C2}\x{CE}\x{218}\x{21A}\x{15F}\x{163}\x{15E}\x{162}]'` |

## Unverifiable

⚠ The rows below are **not** covered by `check-maps.sh`. They are conceptual
dependencies, which do not fit into a command. They are re-read by hand when something
big changes.

- If the model of the five kinds of document changes, the documentation skill,
  `template/`, and the map in every `README.md` written after it break at once.
- If the state file stops being ignored by git, the reason the closing skill asks for
  confirmation before rewriting it breaks: the safety net would exist.
- If `projects/` leaves `.gitignore`, `check-docs.py` starts reading the projects'
  documents too, and "the environment is clean" ends up being about another tree.
