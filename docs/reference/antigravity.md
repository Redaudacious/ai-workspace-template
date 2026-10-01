# Antigravity

Antigravity is Google's AI coding tool. The workspace uses it alongside Claude Code,
with the same rules, skills, and records, plus its own module, `GEMINI.md`. This
reference covers what gets installed, where each component lives, how to keep it up
to date, and what was verified through testing.

## What gets installed

| What | Where | Version, read with |
|---|---|---|
| the 2.0 application | `~/opt/antigravity/`, with the launcher `~/.local/share/applications/antigravity.desktop` | `cat ~/opt/antigravity/.version` |
| the `agy` CLI | `~/.local/bin/agy` | `agy --version` |

The Antigravity IDE is not installed: it is the older variant, and the panel that
directs agents is moving into the 2.0 application.

**The application comes from an archive, not from apt.** The download page,
`https://antigravity.google/download/`, provides the `Antigravity.tar.gz` archive.
Google's apt repository has a single package, `antigravity`, which remains on the
1.x versions. The command that reports the latest version available there:

```bash
curl -fsSL https://us-central1-apt.pkg.dev/projects/antigravity-auto-updater-dev/dists/antigravity-debian/main/binary-amd64/Packages | grep '^Version:' | sort -V | tail -1
```

A 2.x version in its output means switching to apt is possible.

**The CLI** comes from the official script, `https://antigravity.google/cli/install.sh`.
Its final step, `agy install`, writes to shell configuration files; when `~/.local/bin`
is already in PATH, this step is unnecessary and can be skipped. The human logs in via
the browser on the first run of `agy`.

## Updating

- **The application:** `./bin/antigravity.sh update`, from the workspace root, with
  the application closed. The in-app updater only handles AppImage, deb, and rpm
  packages, so it cannot update itself from an archive.
- **The CLI** updates itself automatically in the background; `agy update` does it
  immediately.

## Where Antigravity keeps its files

| Path | What sits there |
|---|---|
| `~/.gemini/config/skills/` | skills symlinked by `bin/antigravity.sh`: house skills and those of pinned plugins |
| `~/.gemini/config/rules/` | always-active global rules: `superpowers.md`, `caveman.md`, `ponytail.md`, `rtk.md` |
| `~/.gemini/antigravity/` | application state |
| `~/.gemini/antigravity-cli/` | CLI state, with its settings in `settings.json` |
| `.agents/rules/framework-NN.md`, in each repository and folder with rules | local rule files, one per include: parent rules, `GEMINI.md`, house rules, memory index |

A local file includes another file using Antigravity's include syntax: a label in
square brackets followed by the path. From a sub-project's folder, for example, including
its project rules:

```text
@[/projects/<project>/AGENTS.md](../../../../AGENTS.md)
```

The 24,000-byte limit on a rule file is calculated after inclusion; each include
therefore gets its own file, and the root `AGENTS.md` does not share its file with
anything else.

The `@path` form without a label includes nothing in Antigravity: it only creates a
reference link.

## What was tested

Each test placed a unique canary word inside a rule file and asked the agent in a fresh
conversation via `agy -p` what words it saw.

| Test | What it showed | What was decided |
|---|---|---|
| `AGENTS.md` and `GEMINI.md` in the same folder | both read, once each | `GEMINI.md` starts with `@AGENTS.md`, which duplicates nothing here and includes the file in Gemini CLI |
| `GEMINI.md` including `AGENTS.md` with a label | `AGENTS.md` read twice | labeled includes are not used between files in the same folder |
| opened in a sub-project's folder with local files, first in a single file, then one per include | each rule, from the root down, loaded once, in both cases | the local rule files mechanism was adopted |
| opened at the root, after reading a file from a project | project rules do not load | the session is opened in the project folder |
| skill symlinked in `~/.gemini/config/skills/` | found and used | skills are symlinked, not copied |
| skill symlinked in `~/.gemini/antigravity-cli/skills/` | not found | that folder is not used |

## Limits that matter

- **A rule file of 24,000 bytes or larger is truncated** without any message.
  `check-docs.py` keeps `AGENTS.md` below the threshold.
- **All always-active rules share 20,000 tokens** (the units measuring text read by
  a model). Above that limit, the largest become plain references.
- **Hooks** (small programs the tool runs on its own, at a specific moment) have no
  event at session start or on every message, and cannot rewrite a command. Modes are
  therefore always-active rules, and RTK is a rule requiring `rtk` in front of commands.
- **In headless mode**, `agy -p`, a tool requesting permission is denied: a terminal
  command requires a `permissions.allow` rule in `settings.json`.

## Models

`agy models` lists the account's models, with the identifiers for `agy --model`;
the tier table sits in `GEMINI.md`. On the Google AI Pro subscription, according to its
subscription page, the quota refills every five hours up to a weekly limit, and all
Gemini models draw from the same quota.

The account's Claude models, `claude-sonnet-4-6` and `claude-opus-4-6-thinking`, have a
quota of their own: with the Gemini quota used up, a trial run through
`bin/tool-bridge.sh` on `claude-sonnet-4-6` passed in 18 seconds.

An exhausted quota shows up in `agy`'s output as `RESOURCE_EXHAUSTED (code 429)`, with the
time left until it refills.
