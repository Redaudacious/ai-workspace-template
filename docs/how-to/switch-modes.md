# How to switch modes

Ponytail is the plugin that decides how much code gets written. It is a permanent mode.
It starts with the session and stays active until it is explicitly stopped.

Superpowers is the plugin that decides the order of the work. RTK is the tool that
shortens command output before the output reaches the conversation. Superpowers and RTK
have no modes.

## Switching during the session

1. **Check the current level.** Run the command without an argument:

   ```
   /ponytail
   ```

   The response shows the active level.

2. **Change the level.** Pass the level you want as an argument:

   ```
   /ponytail ultra
   ```

   Accepted levels: `lite`, `full`, `ultra`, and `off`.

3. **Stop the mode.** Run the command or use a plain-text phrase:

   ```
   /ponytail off
   ```

   The phrases "stop ponytail" and "normal mode" have the same effect.

The change lasts until the end of the session. The next session starts again at the
default level.

## Changing the default level

To start each new session at a level other than `full`, write this to `~/.config/ponytail/config.json`:

```json
{ "defaultMode": "lite" }
```

If you prefer an environment variable, set `PONYTAIL_DEFAULT_MODE=lite` instead.

Both accept `lite`, `full`, `ultra`, and `off`. The value `off` keeps the plugin installed
and its skills available. It does not start the mode on its own.

## Disable the plugin to remove its cost

Switching modes does not unload the plugin, so the permanent cost is still paid.
To remove that cost too, disable the plugin:

```bash
claude="$(command -v claude || ls -d ~/.config/Claude/claude-code/*/claude | sort -V | tail -1)"
"$claude" plugin disable ponytail
```

To enable the plugin again, use `enable` instead of `disable`. Both commands need a
restart of the application. The start of the guide
[How to check that a plugin really works](check-a-plugin-works.md) explains why the
command looks for the binary this way, and not through a fixed path.

Ponytail also writes state outside its own folder. To uninstall it completely, see
[Reference — ponytail](../reference/ponytail.md).
