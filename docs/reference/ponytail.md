# Reference — ponytail

Ponytail governs how much code gets written: its ladder asks first whether anything
needs to be written at all. Reference values come from
`~/.claude/plugins/cache/ponytail/ponytail/4.9.0/`,
the version pinned in `plugins.lock.json`.

## Identification

| Field | Value |
|---|---|
| Full name | `ponytail@ponytail` |
| Version | 4.9.0 |
| Source | `DietrichGebert/ponytail` |
| Author | Dietrich Gebert |
| Permanent cost | ~676 tokens in every session |

## Commands

| Command | Effect |
|---|---|
| `/ponytail` | reports the current level |
| `/ponytail lite \| full \| ultra \| off` | changes the intensity or stops the mode |
| `/ponytail-review` | analyzes the current diff and returns a list of things to delete |
| `/ponytail-audit` | analyzes the whole repository, not only the diff |
| `/ponytail-debt` | gathers the deferred `ponytail:` comments into a record |
| `/ponytail-gain` | displays the table of measurements from the benchmark |
| `/ponytail-help` | short reference of the commands above |

The default level is `full`. It can be changed permanently through the
`PONYTAIL_DEFAULT_MODE` environment variable or through the `defaultMode` field in
`~/.config/ponytail/config.json`.

The mode also stops with the phrase "stop ponytail" or "normal mode".

## The ladder

The seven rungs from `skills/ponytail/SKILL.md`, stopping at the first that holds:

1. Does it need to exist? Speculative need → it is skipped.
2. Does it already exist in the repository? A helper, a type, a pattern already present → it is reused.
3. Does the standard library do it?
4. Does a native feature of the platform cover it? `<input type="date">` instead of a
   calendar library, CSS instead of JS, a database constraint instead of code.
5. Does an already installed dependency solve it?
6. Does it fit in one line?
7. Only then: the minimum code that works.

The ladder applies **after** the problem is understood, not instead of it.

## Declared measurements

The method: a headless Claude Code session edits
`fastapi/full-stack-fastapi-template`, a real FastAPI + React repository. Across twelve
tasks, running the same agent with and without the skill (n=4, model Haiku 4.5), scoring
evaluates the final `git diff`.

| Versus the baseline | Lines of code | Tokens | Cost | Time | Safety |
|---|--:|--:|--:|--:|--:|
| **ponytail** | -54% | -22% | -20% | -27% | 100% |
| caveman | -20% | +7% | +3% | +2% | 100% |
| prompt "YAGNI + one-liners" | -33% | -14% | -21% | -30% | 95% |

The measurement comes from the author of ponytail, and caveman (the plugin that
compresses model answers) appears in it as a comparison baseline. The interpretation
of this fact is in
[What each plugin does and when it is worth it](../explanation/what-each-plugin-does.md).

Earlier figures citing "80–94% less code" come from single-response tests without an
agent. The author notes that these numbers were inflated because the baseline model
padded its answers with extra prose and alternative options.

## The `ponytail:` comment

Deliberate simplifications that cut a real corner are marked in the code:

```
# ponytail: global lock, per-account locks if throughput matters
```

The format is `ponytail:` followed by the accepted ceiling and the upgrade path.
`/ponytail-debt` gathers these markings.

## Hooks

| Moment | Command | Interpreter |
|---|---|---|
| `SessionStart` (`startup`, `resume`, `clear`, `compact`) | `hooks/ponytail-activate.js` | node |
| `SubagentStart` | `hooks/ponytail-subagent.js` | node |
| `UserPromptSubmit` | `hooks/ponytail-mode-tracker.js` | node |

All three hooks require `node` on the path. Without it, the 6 skills (sets of
instructions that enter the conversation when the situation matches) load, but the mode
does not start by itself.

## State written outside the plugin

Uninstalling the plugin leaves several artifacts behind: the mode indicator, the file
`~/.config/ponytail/config.json`, and, if the configuration suggestion was accepted, a
`statusLine` entry in `~/.claude/settings.json`.

A complete cleanup is performed with `node scripts/uninstall.js`, run **before**
uninstalling — the script is itself a file of the plugin.
