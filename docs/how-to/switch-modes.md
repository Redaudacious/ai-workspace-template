# How to switch modes

Ponytail (the plugin that decides how much code is written) and caveman (the plugin that
compresses the model's answers) operate as permanent modes: they start at session launch
and remain active until explicitly stopped.

Superpowers (the plugin that decides the order of the work) and RTK (the tool that
shortens the output of commands before it reaches the conversation) do not have modes.

## Switching during the session

1. **The current level is checked** by running the command without arguments:

   ```
   /ponytail
   ```

   The response reports the active level.

2. **The level is changed** by passing the desired argument:

   ```
   /ponytail ultra
   ```

   Accepted levels: `lite`, `full`, `ultra`, `off`. For caveman, additionally:
   `wenyan-lite`, `wenyan-full`, `wenyan-ultra`.

3. **The mode is stopped** using a command or a plain-text phrase:

   ```
   /caveman off
   ```

   The phrases "stop caveman" and "normal mode" have the same effect. For ponytail:
   "stop ponytail".

The change lasts until the end of the session. The next session restarts from the
default level.

## Changing the default level

To have each new session start at a level other than `full`, write to
`~/.config/ponytail/config.json`:

```json
{ "defaultMode": "lite" }
```

Alternatively, if an environment variable is preferred: `PONYTAIL_DEFAULT_MODE=lite`.

Both accept `lite`, `full`, `ultra`, and `off`. The `off` value leaves the plugin
installed and its skills available, but does not start the mode on its own.

## Caveman is stopped before writing documentation

Caveman and documentation writing are fundamentally in conflict — the reason is
explained in [Conflicts and pitfalls](../explanation/conflicts-and-pitfalls.md).

Here, `caveman off` means more than simply turning off compression: it is the mode in
which the model explains concepts for someone outside the field. That means full
sentences, but also concrete comparisons, numbers alongside their significance, and
decisions stated openly.

1. Before requesting documentation:

   ```
   /caveman off
   ```

2. The documentation is requested.
3. Afterward, if the mode is wanted back:

   ```
   /caveman full
   ```

The order matters: turning it off after the document has been written does not
rewrite it.

## The plugin is disabled so that it costs nothing any more

Switching modes does not unload the plugin, so the permanent cost is still incurred.
To remove that cost as well, the plugin is disabled:

```bash
claude="$(command -v claude || { ls -d ~/.config/Claude/claude-code/*/claude ~/"Library/Application Support/Claude"/claude-code/*/claude 2>/dev/null | sort -V | tail -1; })"
"$claude" plugin disable caveman
```

Re-enabling is done with `enable` instead of `disable`. Both require restarting the
application. Why the binary is located this way, and not through a fixed path, is
explained at the start of the guide
[How to check that it works](check-a-plugin-works.md).

Ponytail also writes state outside its own folder. Its complete uninstallation is
described in [Reference — ponytail](../reference/ponytail.md).
