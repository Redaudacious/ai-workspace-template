# Reference — RTK

RTK shortens command output before the output reaches the conversation. This plugin brings the tool and places it in the path of commands. The values come from `~/.claude/plugins/cache/enix/rtk-plugin/0.1.2/`, the version pinned in `plugins.lock.json`.

## Identification

| Field | Value |
|---|---|
| Full name | `rtk-plugin@enix` |
| Version | 0.1.2 |
| Source | `enixCode/plugins` |
| Permanent cost | ~12 tokens in every session |

It is the cheapest of the three plugins, by two orders of magnitude. The plugin has almost no content of its own. It ships a binary and a dispatcher.

## Command

| Command | Effect |
|---|---|
| `/rtk-plugin:gain` | Savings dashboard: routed commands, input and output tokens, total savings, and breakdown by program |

## How it works

| Moment | What happens |
|---|---|
| `SessionStart` | `scripts/bootstrap-rtk.mjs` downloads the RTK binary into `${CLAUDE_PLUGIN_DATA}/rtk/`, then runs `rtk init -g` once per session |
| `PreToolUse` on `Bash` | `bin/dispatch.mjs` reads the command. If the program is in the list, it rewrites the command and puts the RTK binary in front of it |

The rewrite is literal: `git status` becomes `"<path>/rtk" git status`. RTK runs the command and compresses its output before the output reaches the conversation.

## Compressed programs

This is the complete list of 43 programs. It comes from the field `RtkRoute.TOOLS` in `bin/dispatch.mjs`:

| Group | Programs |
|---|---|
| Files and search | `ls`, `find`, `grep`, `diff`, `cat`, `less`, `head`, `tail` |
| Git | `git`, `gh` |
| Build and tests | `cargo`, `go`, `pytest`, `jest`, `vitest`, `playwright`, `rake`, `rspec`, `mocha` |
| Static analysis | `eslint`, `tsc`, `prettier`, `ruff`, `rubocop`, `golangci-lint` |
| Packages | `npm`, `npx`, `pnpm`, `yarn`, `pip`, `pipx`, `poetry`, `bundle`, `prisma` |
| Infrastructure | `docker`, `kubectl`, `helm`, `aws`, `gcloud`, `az` |
| Network | `curl`, `wget`, `jq` |

## What passes uncompressed

| Case | Reason |
|---|---|
| Any command with `\|`, `&&`, `$()`, or another shell construct | The dispatcher leaves it intact, so existing scripts do not break |
| A program that is not in the list of 43 | No route exists |
| A command already prefixed with `rtk` | The dispatcher does not prefix it twice |

Commands with pipes pass uncompressed. This has an important practical effect. See [How to check that it works](../how-to/check-a-plugin-works.md).

## Where the data is

| What | Path (Linux) |
|---|---|
| The binary | `~/.claude/plugins/data/rtk-plugin*/rtk/rtk` |
| The measurement history | `~/.local/share/rtk/` (SQLite) |

The plugin disables telemetry by design. Inspect it with `rtk config`.

## Source of the binary

The binary comes from `https://github.com/rtk-ai/rtk/releases`. The platform determines the file name: `rtk-<target>.<extension>`.

The download script verifies no checksum and no signature. A search for `sha256`, `checksum`, `signature`, and `verify` in `scripts/bootstrap-rtk.mjs` returns zero matches. [Conflicts and pitfalls](../explanation/conflicts-and-pitfalls.md) explains the consequences.
