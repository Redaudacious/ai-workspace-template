# Antigravity

Antigravity is Google's AI coding tool. The workspace uses it alongside Claude Code, with the same rules, skills, and records, plus its own module, `GEMINI.md`. This reference covers what gets installed, where each part lives, how to keep it up to date, and what was tested.

## What gets installed

| What | Where | Version, read with |
|---|---|---|
| the 2.0 application | `~/opt/antigravity/`, with the launcher `~/.local/share/applications/antigravity.desktop` | `cat ~/opt/antigravity/.version` |
| the `agy` CLI | `~/.local/bin/agy` | `agy --version` |

The Antigravity IDE is not installed. It is the older variant, and the panel that directs agents moves into the 2.0 application.

**The application comes from an archive, not from apt.** The download page, `https://antigravity.google/download/`, provides the `Antigravity.tar.gz` archive. Google's apt repository has one package, `antigravity`, and that package is still on the 1.x versions. The command that shows the latest version in that repository:

```bash
curl -fsSL https://us-central1-apt.pkg.dev/projects/antigravity-auto-updater-dev/dists/antigravity-debian/main/binary-amd64/Packages | grep '^Version:' | sort -V | tail -1
```

A 2.x version in the output means that switching to apt is possible.

**The CLI** comes from the official script, `https://antigravity.google/cli/install.sh`. Its last step, `agy install`, writes to the shell configuration files. When `~/.local/bin` is already in PATH, that step is not needed, and it can be skipped. The user completes the login in the browser on the first run of `agy`.

## Updating

- **The application:** `./bin/antigravity.sh update`, from the workspace root, with the application closed. The in-app updater handles only AppImage, deb, and rpm packages, so it cannot update itself from an archive.
- **The CLI** updates itself in the background. `agy update` does it right away.

## Where Antigravity keeps its files

| Path | What is there |
|---|---|
| `~/.gemini/config/skills/` | the skills, symlinked by `bin/antigravity.sh`: the house skills and the skills of pinned plugins |
| `~/.gemini/config/rules/` | the global rules that are always active: `superpowers.md`, `ponytail.md`, `rtk.md` |
| `~/.gemini/config/hooks.json` | the global hooks. `memento`, the note hook, slips Gemini a reminder after some tools. `bin/antigravity.sh` links it next to the others, by name. |
| `~/.gemini/antigravity/` | application state |
| `~/.gemini/antigravity-cli/` | CLI state, with its settings in `settings.json` |
| `brain/<conversation>/.system_generated/logs/transcript_full.jsonl`, under each of the two paths above | the full log of a conversation: each model reply, with the chat text, the thoughts, and the tool calls |
| `.agents/rules/framework-NN.md`, in each repository and folder with rules | the local files, one per include: the parent rules, `GEMINI.md`, the house rules, and the memory index |

A local file includes another file with the include syntax of Antigravity. The syntax is a label in square brackets, followed by a path. For example, a game's folder includes its project rules this way:

```text
@[/projects/<project>/AGENTS.md](../../../../AGENTS.md)
```

The 24,000-byte limit on a rule file is counted after inclusion. That is why each include has its own file. The root `AGENTS.md` shares its file with nothing.

The `@path` form, without a label, includes nothing in Antigravity. It only makes a reference.

## What was tested

Each loading test put a unique word in a rule file. Then it asked the agent, in a new conversation through `agy -p`, which words it could see.

Each behavior test gave the agent a small defect to repair, in a throwaway repository with the same rules as a project. Then the test read the conversation log for what the agent wrote alongside each tool call.

The last four rows come from the bench. The bench gives the same task to any tool. It then reads the tool's log to see whether the tool followed the house rules. Each of the first three of these four rows tests one stage of the house. Each stage was tuned in rounds on two tasks. The last of these four rows tests one full cycle in the application. How to run the bench: [Bench](bench.md).

| Test | What it showed | What was decided |
|---|---|---|
| `AGENTS.md` and `GEMINI.md` in the same folder | both read, once each | `GEMINI.md` starts with `@AGENTS.md`, which duplicates nothing here and includes the file in Gemini CLI |
| `GEMINI.md` including `AGENTS.md` with a label | `AGENTS.md` twice | the labeled include is not used between files in the same folder |
| opened in a game's folder, with local files: first in a single file, then one per include | each rule, from the root down, loaded once, in both runs | the local-file mechanism |
| opened at the root, after reading a file from a project | the project's rules do not load | the session opens in the project folder |
| skill symlinked in `~/.gemini/config/skills/` | found and used | skills are symlinked, not copied |
| skill symlinked in `~/.gemini/antigravity-cli/skills/` | not found | that folder is not used |
| the small defect, on Gemini 3.1 Pro, with the response-compression rule that exempted only explanations, the report, and the handoff | 8 tool calls, none with text beside them. The skill announcement came only in the final reply. The report was compressed. | the compression rule now exempts the skill announcement too, and a sentence after each step, in the same reply as the next call |
| the same defect, on Gemini 3.1 Pro, with the widened exemption, in two runs | a sentence after a step appeared in one run of two. The announcement was never on time. It appeared once, in the final reply. The report used full sentences in both runs. | the exemption stays. An on-time announcement needs the note |
| the same defect, on Gemini 3.8 Flash, with the widened exemption | each skill announced on time, a sentence after each step, `rtk` on all 5 commands | on Flash, the rules are enough |
| the same defect, on Gemini 3.1 Pro, with the note, in two runs | the skill announcement right after reading, and the sentence after editing, in both runs. Text appeared beside 4 of 5 and 3 of 6 calls. | the note stays |
| the same runs, first with rtk required for `git`, `grep`, `ls`, `find`, tests, and builds | `rtk python` and `rtk pytest` failed. `find` bypassed the rule. With the rule tightened, the test ran through `rtk test python3` in both runs. | the rtk rule requires only `rtk git <subcommand>` and `rtk test <test command>` |
| bench, spec stage, Gemini 3.1 Pro, six rounds | In round 0, the spec was in another folder. The plan and the code were written there too, through subagents. After round 5, every task passed the threshold, in different rounds. On a small work item, it asked one or two questions and gave the design in one piece. | the `spec` skill, with the house steps in order. The note requires a web search before the variants and ends the turn after a skipped reply |
| bench, plans stage, Gemini 3.1 Pro, two rounds | in round 0, it skipped reading the house rules. The plan described the code instead of writing it. In round 1, both tasks passed, with the full code tested in a copy. | the new `plans` skill |
| bench, execute stage, Gemini 3.8 Flash, two rounds | passed from round 0, on Claude's plans. In round 1, it passed without the two useless searches at closing. | the `execute` skill names seven steps that Claude used to take unwritten. The note requires the search only in the spec session |
| a full cycle, in the application, on a new topic: spec and plans on 3.1 Pro, execution on 3.7 Flash | the threshold passed in all three sessions. The spec wrote a different command from the one approved in chat. The plans did not see the wrong line in their own output. Execution followed the plan exactly. | the handoffs (the notes in `STATE.md` for the next session) recommend Gemini only for execution |

## Limits that matter

- **A rule file of 24,000 bytes or larger is truncated** without any message. `check-docs.py` keeps `AGENTS.md` below the threshold.
- **All always-active rules together get 20,000 tokens** (the units in which the text that a model reads is measured). Above that limit, the largest rules become plain references.
- **Hooks** (small programs that the tool runs on its own, at a specific moment) have no event at session start. That is why modes are always-active rules. rtk is a rule that requires `rtk` in front of `git` commands and tests.
- **`PreInvocation`** runs before each model call. It receives the conversation log in `transcriptPath`, which is current to the step just taken. An `ephemeralMessage` that it returns appears in the log as an `EPHEMERAL_MESSAGE` step. The note depends on that step.
- **The `overwrite` field of `PreToolUse`**, described in the built-in `agy-customizations` skill, would rewrite a tool's arguments before the tool runs. It is untested.
- **In headless mode**, `agy -p`, a tool that asks for permission is denied. A terminal command needs a `permissions.allow` rule in `settings.json`.

## Models

`agy models` lists the account's models, with the identifiers for `agy --model`. The tier table is in `GEMINI.md`.

On the Google AI Pro subscription, according to its subscription page, the quota refills every five hours up to a weekly limit. All Gemini models draw from the same quota.

The account's Claude models, `claude-sonnet-4-6` and `claude-opus-4-6-thinking`, have a quota of their own. With the Gemini quota used up, a test through `bin/tool-bridge.sh` on `claude-sonnet-4-6` passed in 18 seconds.

An exhausted quota appears in the output of `agy` as `RESOURCE_EXHAUSTED (code 429)`, with the time until it refills.
