# Reference — ponytail

Ponytail is the plugin that decides how much code gets written. Its ladder first asks whether anything needs to be written at all. The values here come from `~/.claude/plugins/cache/ponytail/ponytail/4.9.0/`, the version pinned in `plugins.lock.json`.

## Identification

| Field | Value |
|---|---|
| Full name | `ponytail@ponytail` |
| Version | 4.9.0 |
| Source | `DietrichGebert/ponytail` |
| Author | Dietrich Gebert |
| Permanent cost | ~676 tokens in each session |

## Commands

| Command | Effect |
|---|---|
| `/ponytail` | reports the current level |
| `/ponytail lite \| full \| ultra \| off` | changes the intensity or turns the mode off |
| `/ponytail-review` | analyzes the current diff and returns a list of things to delete |
| `/ponytail-audit` | analyzes the whole repository, not only the diff |
| `/ponytail-debt` | gathers the deferred `ponytail:` comments into a ledger |
| `/ponytail-gain` | shows the measurement table from the benchmark |
| `/ponytail-help` | short reference of the commands above |

The default level is `full`. You can change it permanently through the `PONYTAIL_DEFAULT_MODE` environment variable or through the `defaultMode` field in `~/.config/ponytail/config.json`.

The mode also stops when you say "stop ponytail" or "normal mode".

## The ladder

The seven rungs come from `skills/ponytail/SKILL.md`. Stop at the first rung that holds:

1. Does it need to exist? A speculative need is skipped.
2. Does it already exist in the repository? A helper, a type or a pattern that is already present is reused.
3. Does the standard library do it?
4. Does a native platform feature cover it? Use `<input type="date">` instead of a calendar library, CSS instead of JS, or a database constraint instead of code.
5. Does an already installed dependency solve it?
6. Does it fit on one line?
7. Only then: the minimum code that works.

The ladder runs **after** the problem is understood, not instead of it.

## Declared measurements

The method: a headless Claude Code session edits `fastapi/full-stack-fastapi-template`, a real FastAPI and React repository. Across twelve tasks, the same agent runs with and without the skill (n=4, model Haiku 4.5). The score comes from the final `git diff`.

| Versus the baseline | Lines of code | Tokens | Cost | Time | Safety |
|---|--:|--:|--:|--:|--:|
| **ponytail** | -54% | -22% | -20% | -27% | 100% |
| prompt "YAGNI + one-liners" | -33% | -14% | -21% | -30% | 95% |

The measurement comes from the author of ponytail.

Earlier figures of "80–94% less code" come from a measurement on one single response, without an agent. The author flags them as inflated, because the reference model padded its answer with prose and options.

## The `ponytail:` comment

Deliberate simplifications that cut a real corner are marked in the code:

```
# ponytail: global lock, per-account locks if throughput matters
```

The format is `ponytail:`, followed by the accepted ceiling and the upgrade path. `/ponytail-debt` gathers these markings.

## Hooks

| Event | Command | Interpreter |
|---|---|---|
| `SessionStart` (`startup`, `resume`, `clear`, `compact`) | `hooks/ponytail-activate.js` | node |
| `SubagentStart` | `hooks/ponytail-subagent.js` | node |
| `UserPromptSubmit` | `hooks/ponytail-mode-tracker.js` | node |

All three hooks need `node` on the path. Without it, the mode does not start by itself, though the 6 skills still load. The skills are sets of instructions that enter the conversation when the situation matches.

## State written outside the plugin

Uninstalling the plugin does not delete the mode indicator, the file `~/.config/ponytail/config.json`, or, if the configuration suggestion was accepted, a `statusLine` entry in `~/.claude/settings.json`.

For a complete cleanup, run `node scripts/uninstall.js` **before** you uninstall the plugin. The script is itself a file of the plugin.
