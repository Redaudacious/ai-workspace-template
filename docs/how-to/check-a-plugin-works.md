# How to check that a plugin really works

A plugin can appear as `enabled` without actually doing anything. [Conflicts and pitfalls](../explanation/conflicts-and-pitfalls.md) explains the underlying causes. The checks below run from the cheapest to the slowest.

These commands need the `claude` binary. Where it is not installed separately on PATH, use the one from the desktop application. Never write its path with a version number. The application updates itself and keeps only recent versions on disk. So a path pinned to one version exits with 127.

```bash
claude="$(command -v claude || ls -d ~/.config/Claude/claude-code/*/claude | sort -V | tail -1)"
"$claude" plugin list
```

`sort -V` compares version numbers as numbers. A plain sort places `2.1.99` after `2.1.266`, so it would pick the older version.

## 1. The installation is in the configuration

```bash
cat ~/.claude/settings.json
```

The plugin must appear in `enabledPlugins` with the value `true`. Its marketplace, the repository that installs it, must appear in `extraKnownMarketplaces`. If it is missing from here, the installation did not reach the file, so the remaining checks make no sense.

## 2. The interpreter the hooks require exists

This command lists the commands that the plugin calls:

```bash
grep -rhoE '"command": *"[^"]+"' ~/.claude/plugins/cache/*/*/*/hooks/*.json ~/.claude/plugins/cache/*/*/*/.claude-plugin/plugin.json 2>/dev/null | sort -u
```

For each program in the list, typically `node` or `bash`, check that it is present:

```bash
command -v node
```

A missing program means a dead hook, whatever the plugin list reports.

## 3. The mode starts by itself

After restarting the application, in a new session:

```
/ponytail
```

This command belongs to ponytail, the plugin that decides how much code is written. A response that names the active level shows that the `SessionStart` hook ran. A response that says the command does not exist means the plugin did not load.

## 4. The skills trigger

The skills in superpowers, the plugin that decides the order of the work, have no slash commands. So check them by their effect instead. A skill loads only when its situation comes up.

Write a prompt that describes a situation, not an action. For example, a prompt that states uncertainty about the cause of a defect.

The sign that a skill applied is the announcement `Using [skill] to [purpose]`. Its absence means the skill did not apply. [How to trigger a skill from a prompt](trigger-a-skill-from-a-prompt.md) documents the prompt wordings that trigger skills.

## 5. RTK really compresses

RTK cuts command output short before the conversation sees it.

```
/rtk-plugin:gain
```

The dashboard reports the number of routed commands and the savings. Two results need interpretation:

| Result | What it means |
|---|---|
| "RTK is not installed yet" | The `SessionStart` hook did not download the binary. Restart the application. |
| Zero routed commands, although work was done | The commands given contained pipes or chains, so they passed through uncompressed. |

The second case is not a malfunction. The check that tells the two cases apart compares the form of the commands given. It compares them with the exclusion list in [Reference — RTK](../reference/rtk.md), not with the list of accepted programs.

## 6. The cost paid is the expected one

```bash
claude="$(command -v claude || ls -d ~/.config/Claude/claude-code/*/claude | sort -V | tail -1)"
"$claude" plugin details ponytail
```

The example uses ponytail, the plugin that decides how much code is written. The report shows the component inventory and the permanent cost. It also shows the cost of each skill when invoked. This is worth running before enabling a new plugin, not after.

## 7. The documents are current

```bash
python3 bin/documents.py .
```

The tool exits with 0 when no document lags behind its code. With 1, it lists the documents to reread. In full: [How to keep the documentation current](keep-documentation-current.md).
