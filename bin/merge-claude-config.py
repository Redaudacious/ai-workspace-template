#!/usr/bin/env python3
"""Merges the three files in `<HOME>/.claude/` with what comes from plugins.lock.json.

It changes only our keys — the rest of the file stays as it was, so that on a machine
where the human was already using Claude Code they do not lose their settings or the
plugins the lockfile does not know.

An existing file that is not valid JSON stops everything with code 2, without writing
anything: replacing it with an empty one is exactly the data loss the tool repairs.
"""
import json
import pathlib
import sys
from datetime import datetime, timezone


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

    # Claude Code reads `AGENTS.md` on its own from the launch folder and its parents
    # only with this setting. Without it, a session opened in a project does not see
    # the shared rules: their import from the root's `CLAUDE.md` steps outside the
    # session folder, and such an import does not expand.
    # A stricter human choice, `claude-md` or `managed-only`, remains: report it.
    options = (settings.setdefault("pluginConfigs", {})
               .setdefault("agents-md@builtin", {}).setdefault("options", {}))
    if options.get("instructionFiles") in (None, "claude-md-or-agents-md"):
        options["instructionFiles"] = "claude-md-and-agents-md"
    elif options["instructionFiles"] != "claude-md-and-agents-md":
        print(f"warning: Project instructions is '{options['instructionFiles']}', chosen by the human; "
              "Claude Code does not read AGENTS.md in a project", file=sys.stderr)

    # Without `lastUpdated`, Claude Code rejects the whole file as "corrupted".
    # The format is the one Claude Code itself writes it with: `new Date().toISOString()`.
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
