# How to check that a plugin really works

A plugin can appear as `enabled` without actually doing anything. The underlying causes
are covered in [Conflicts and pitfalls](../explanation/conflicts-and-pitfalls.md). The
checks below are arranged from the cheapest to the slowest.

These commands require the `claude` binary. Where it is not installed separately
on PATH, the one provided by the desktop application is used. Its path is never
written with a version number: the application updates automatically and retains
only recent versions on disk, so a path pinned to a single version exits with 127.

The application stores its binaries under `~/.config/Claude/` on Linux and under
`~/Library/Application Support/Claude/` on macOS, so the lookup command covers both.

```bash
claude="$(command -v claude || { ls -d ~/.config/Claude/claude-code/*/claude ~/"Library/Application Support/Claude"/claude-code/*/claude 2>/dev/null | sort -V | tail -1; })"
"$claude" plugin list
```

The `sort -V` flag compares version numbers numerically. Standard lexicographical
sorting places `2.1.99` after `2.1.266`, which would select the older version.

## 1. The installation has entered the configuration

```bash
cat ~/.claude/settings.json
```

The plugin must appear in `enabledPlugins` with the value `true`, and its marketplace
(the repository it is installed from) in `extraKnownMarketplaces`. If it is missing
from here, the installation was not written, and subsequent checks are pointless.

## 2. The interpreter the hooks require exists

The commands called by the plugin are extracted, then looked up on PATH:

```bash
grep -rhoE '"command": *"[^"]+"' ~/.claude/plugins/cache/*/*/*/hooks/*.json ~/.claude/plugins/cache/*/*/*/.claude-plugin/plugin.json 2>/dev/null | sort -u
```

For each program that appears — typically `node` or `bash` — its presence is verified:

```bash
command -v node
```

A missing program means a dead hook, regardless of what the plugin list reports.

## 3. The mode starts by itself

After restarting the application, in a new session:

```
/ponytail
```

This command belongs to ponytail (the plugin that decides how much code is written).
A response stating the active level confirms that the `SessionStart` hook ran. A
response reporting that the command does not exist means the plugin was not loaded.

## 4. The skills trigger

The skills in superpowers (the plugin that decides the order of the work) have no
slash commands, so they are checked by their effect instead (a skill is a set of
instructions that enters the conversation when the situation matches).

A prompt is formulated that presents a situation rather than requesting an action —
for example, one that declares uncertainty about the cause of a defect.

Confirmation comes from the announcement `Using [skill] to [purpose]`. Its absence
means the skill was not applied; prompt wordings that trigger skills are documented in
[How to trigger a skill from a prompt](trigger-a-skill-from-a-prompt.md).

## 5. RTK really compresses

RTK is the tool that shortens the output of commands before it reaches the conversation.

```
/rtk-plugin:gain
```

The dashboard reports the number of routed commands and the savings achieved. Two
results require interpretation:

| Result | What it means |
|---|---|
| "RTK is not installed yet" | the `SessionStart` hook did not download the binary; the application is restarted |
| Zero routed commands, although work was done | the commands run contained pipes or chains, so they passed through uncompressed |

The second case is not a malfunction. It is verified by comparing the syntax of the
issued commands with the exclusion list in [Reference — RTK](../reference/rtk.md),
rather than against the list of accepted programs.

## 6. The cost paid is the expected one

```bash
claude="$(command -v claude || { ls -d ~/.config/Claude/claude-code/*/claude ~/"Library/Application Support/Claude"/claude-code/*/claude 2>/dev/null | sort -V | tail -1; })"
"$claude" plugin details caveman
```

The example uses caveman (the plugin that compresses the model's answers). The report
shows the component inventory and the permanent cost, plus the invocation cost of
each skill. This is worth running before enabling a new plugin, not after.
