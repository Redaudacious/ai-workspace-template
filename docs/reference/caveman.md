# Reference — caveman

Caveman is the plugin that compresses model responses. Within the workspace, it is
turned off with `/caveman off` before writing documentation. The values below are
read from `~/.claude/plugins/cache/caveman/caveman/3b74643f4d91/`, the version pinned
in `plugins.lock.json`.

## Identification

| Field | Value |
|---|---|
| Full name | `caveman@caveman` |
| Version | `3b74643f4d91` (commit identifier, not a version number) |
| Source | `JuliusBrussee/caveman` |
| Author | Julius Brussee |
| Permanent cost | ~1,244 tokens in every session |

This permanent cost is the highest among the four installed plugins — more than twice
that of superpowers (the plugin governing workflow order), with 14 skills against
caveman's 21. The rationale is explored in
[What each plugin does and when it is worth it](../explanation/what-each-plugin-does.md).

## Levels

| Level | What changes |
|---|---|
| `lite` | filler and hedging disappear; articles and full sentences remain |
| `full` | articles disappear, sentence fragments are allowed, short synonyms; no tool narration, no decorative tables |
| `ultra` | conjunctions disappear as well when cause and effect remain clear; single words when one is enough |
| `wenyan-lite` / `wenyan-full` / `wenyan-ultra` | classical Chinese variants |
| `off` | disabled |

Default: `full`. Switch levels with `/caveman <level>`. The mode can also be disabled
with "stop caveman" or "normal mode".

## Rules that contradict intuition

These rules are stated explicitly in `skills/caveman/SKILL.md` and are worth noting
because they describe what the mode does **not** do:

- **No invented abbreviations** (`cfg`, `impl`, `req`, `res`, `fn`). The stated reason: tokenizers split them the same way as the full word, saving nothing while the reader still has to decode them.
- **No arrows** (`→`). They form a separate token and save nothing.
- **No words added to sound primitive.** Compression must never expand the output: "when it not" costs one token more than "when not".
- **Never cut** `not`, `never`, `no`, `only`, `except`. Reversing the meaning costs more than any token saved.
- **The language is preserved.** The style is compressed, not the language. For a request in Romanian, the answer stays in Romanian.
- Technical terms, code, API names, commands, and exact error strings remain untouched.

## Commands

| Command | Effect |
|---|---|
| `/caveman [level]` | switches the level |
| `/caveman-commit` | compressed commit message |
| `/caveman-review` | compressed review |
| `/caveman-stats` | statistics |
| `/caveman-init` | initialization |

## Skills

Twenty-one skills are provided (a skill is a set of instructions loaded into the
conversation when a situation matches), of which only some handle style compression.
The remainder are workflow skills that overlap with superpowers:

| Group | Skills |
|---|---|
| Style | `caveman`, `caveman-compress`, `caveman-help`, `caveman-stats`, `caveman-setup`, `caveman-manage`, `caveman-learn`, `caveman-optimize` |
| Workflow | `investigate-first`, `lean-build`, `safe-refactor`, `surgical-patch`, `verify-and-stop`, `migration` |
| Review | `caveman-review`, `caveman-evidence-review`, `caveman-commit` |
| Exploration | `caveman-explore`, `caveman-discover` |
| Delegation | `cavecrew` |

The overlap with superpowers is real: `investigate-first` covers the same ground as
`systematic-debugging`, `verify-and-stop` matches `verification-before-completion`,
and `lean-build` resembles the ladder in ponytail, the plugin governing how much code
is written.

This overlap is addressed in
[Conflicts and pitfalls](../explanation/conflicts-and-pitfalls.md).

## Agents

`cavecrew-builder`, `cavecrew-investigator`, `cavecrew-reviewer`.

## Hooks

| Moment | Command | Interpreter |
|---|---|---|
| `SessionStart` | `src/hooks/caveman-activate.js` | node |
| `UserPromptSubmit` | `src/hooks/caveman-mode-tracker.js` | node |

The hooks for Claude Code reside in `.claude-plugin/plugin.json`. The repository also
contains `.codex/hooks.json`, with a simple `echo` — that configuration is for Codex
and does not apply here.
