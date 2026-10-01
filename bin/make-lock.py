#!/usr/bin/env python3
"""Regenerates plugins.lock.json from the current installation.

For each plugin it writes the repository in which the SHA really exists.
installed_plugins.json does not say it: in marketplace.json, `source: "./"`
means the plugin is the marketplace's repository itself (ponytail, caveman), and
`source: {"source": "url", ...}` means a separate repository (superpowers,
rtk-plugin). A script that looks in the marketplace's repository succeeds on two
plugins out of four.

The resulting file contains no absolute path, so that it is valid on any machine
and for any user name.
"""
import json, pathlib, subprocess

home = pathlib.Path.home()
pl = home / ".claude/plugins"
inst = json.loads((pl / "installed_plugins.json").read_text())
known = json.loads((pl / "known_marketplaces.json").read_text())

def head(path):
    return subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()

out = {"marketplaces": [], "plugins": []}

for market, meta in known.items():
    out["marketplaces"].append({
        "name": market,
        "url": f"https://github.com/{meta['source']['repo']}.git",
        "sha": head(pl / "marketplaces" / market),
    })

for key, entries in inst["plugins"].items():
    name, market = key.split("@", 1)
    entry = entries[0]
    manifest = json.loads(
        (pl / "marketplaces" / market / ".claude-plugin/marketplace.json").read_text())
    source = next(p["source"] for p in manifest["plugins"] if p["name"] == name)
    url = (f"https://github.com/{known[market]['source']['repo']}.git"
           if source == "./" else source["url"])
    out["plugins"].append({
        "name": name,
        "marketplace": market,
        "version": entry["version"],
        "sha": entry["gitCommitSha"],
        "url": url,
    })

dest = pathlib.Path(__file__).resolve().parent.parent / "plugins.lock.json"
dest.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
print(f"wrote {dest.name}: {len(out['plugins'])} plugins, "
      f"{len(out['marketplaces'])} marketplaces")
