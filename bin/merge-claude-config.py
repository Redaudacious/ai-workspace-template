#!/usr/bin/env python3
"""Merge the three files in `<HOME>/.claude/` with the data from plugins.lock.json.

The script changes only its own keys. The rest of each file stays as it was, so a
machine where the user already ran Claude Code keeps its settings and the plugins
that the lockfile does not list.

If an existing file is not valid JSON, the script stops with code 2 and writes
nothing. Replacing that file with an empty one is the data loss this tool prevents.
"""
import json
import os
import pathlib
import sys
from datetime import datetime, timezone

# Compaction summarizes the conversation at this threshold. The default threshold of
# models with a one-million-token window is about 967,000 tokens.
COMPACT_THRESHOLD = 400_000

# The workspace root, found from the location of this script, and its mods in `mods/`.
ROOT = pathlib.Path(__file__).resolve().parent.parent
MODS = ["work-env-live", "records-guard"]
# The reminder at the end of each reply. `|| true`: a missing script exits with 2,
# and exit 2 blocks the Stop hook, so the session could not finish the reply.
REMINDER = f'python3 "{ROOT / "bin" / "reminder.py"}" --tool claude || true'


def read_json(path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise SystemExit(f"refused: {path} is not valid JSON: {e}")


def main():
    lock = json.loads(pathlib.Path(sys.argv[1]).read_text())
    home = pathlib.Path(sys.argv[2])
    pl = home / ".claude/plugins"

    settings_path = home / ".claude/settings.json"
    marketplaces_path = pl / "known_marketplaces.json"
    installed_path = pl / "installed_plugins.json"

    try:
        settings = read_json(settings_path)
        marketplaces = read_json(marketplaces_path)
        installed = read_json(installed_path)
    except SystemExit as e:
        print(e, file=sys.stderr)
        return 2

    settings.setdefault("enabledPlugins", {})
    settings.setdefault("extraKnownMarketplaces", {})
    for p in lock["plugins"]:
        settings["enabledPlugins"][f"{p['name']}@{p['marketplace']}"] = True
    for m in lock["marketplaces"]:
        settings["extraKnownMarketplaces"][m["name"]] = {
            "source": {"source": "github",
                       "repo": m["url"].removeprefix("https://github.com/").removesuffix(".git")}}

    # Claude Code reads `AGENTS.md` from the launch folder and its parents only with
    # this setting. Without it, a session opened in a project does not see the shared
    # rules: the import in the root `CLAUDE.md` points outside the session folder,
    # and such an import does not expand.
    # If the user chose a stricter value, `claude-md` or `managed-only`, keep it and warn.
    options = (settings.setdefault("pluginConfigs", {})
               .setdefault("agents-md@builtin", {}).setdefault("options", {}))
    if options.get("instructionFiles") in (None, "claude-md-or-agents-md"):
        options["instructionFiles"] = "claude-md-and-agents-md"
    elif options["instructionFiles"] != "claude-md-and-agents-md":
        print(f"warning: Project instructions is '{options['instructionFiles']}', chosen by the user; "
              "Claude Code does not read AGENTS.md in a project", file=sys.stderr)

    # If the user chose a threshold, keep it and warn, as for the option above.
    if settings.setdefault("autoCompactWindow", COMPACT_THRESHOLD) != COMPACT_THRESHOLD:
        print(f"warning: autoCompactWindow is {settings['autoCompactWindow']}, chosen by the user; "
              f"the workspace threshold is {COMPACT_THRESHOLD}", file=sys.stderr)

    # The workspace mods load in every session, also in sessions started by the app,
    # from CLAUDE_CODE_PLUGIN_DIRS. Folders the user already put there stay, and each
    # of our folders is added once.
    env = settings.setdefault("env", {})
    folders = [d for d in env.get("CLAUDE_CODE_PLUGIN_DIRS", "").split(os.pathsep) if d]
    for mod in MODS:
        path = str(ROOT / "mods" / mod)
        if path not in folders:
            folders.append(path)
    env["CLAUDE_CODE_PLUGIN_DIRS"] = os.pathsep.join(folders)
    # App sessions do not watch these folders without this key. A change in `mods/`
    # would then reach only the chats started after it.
    env["CLAUDE_CODE_PLUGIN_DIR_WATCH"] = "1"

    # The user's Stop hooks stay. Ours is replaced, so a moved root does not duplicate it.
    hooks = settings.setdefault("hooks", {})
    stop = [g for g in hooks.get("Stop", [])
            if not any("reminder.py" in h.get("command", "") for h in g.get("hooks", []))]
    hooks["Stop"] = stop + [{"hooks": [{"type": "command", "command": REMINDER, "timeout": 30}]}]

    # Without `lastUpdated`, Claude Code rejects the whole file as "corrupted".
    # The format is the one Claude Code itself writes: `new Date().toISOString()`.
    now = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    for m in lock["marketplaces"]:
        marketplaces[m["name"]] = {
            "source": {"source": "github",
                       "repo": m["url"].removeprefix("https://github.com/").removesuffix(".git")},
            "installLocation": str(pl / "marketplaces" / m["name"]),
            "lastUpdated": now,
        }

    installed["version"] = 2
    installed.setdefault("plugins", {})
    for p in lock["plugins"]:
        installed["plugins"][f"{p['name']}@{p['marketplace']}"] = [{
            "scope": "user",
            "installPath": str(pl / "cache" / p["marketplace"] / p["name"] / p["version"]),
            "version": p["version"],
            "gitCommitSha": p["sha"],
        }]

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    pl.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")
    marketplaces_path.write_text(json.dumps(marketplaces, indent=2) + "\n")
    installed_path.write_text(json.dumps(installed, indent=2) + "\n")
    print("settings.json, known_marketplaces.json, installed_plugins.json written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
