# Conflicts and pitfalls

Installing the three plugins exposed the pitfalls below. A pitfall is something that cost time, together with the method that found it. Each entry records the method that caught it. That method can be applied again, but the result cannot.

## A plugin that shows "enabled" but does nothing

**The symptom.** `claude plugin list` shows `✔ enabled`. The installation reported success. Nothing that the plugin promises happens in the conversation.

**The cause.** The plugin's hooks run as separate processes. The interpreter comes from the PATH. Two of the three installed plugins start their hooks with `node`. The machine had no `node`. It was absent from `/usr/bin` and from dpkg, and it had none of nvm, fnm, volta or bun.

**Why it is a pitfall and not a quirk.** The installation never verifies the interpreter. It copies files and writes an entry into `~/.claude/settings.json`. Nothing in this chain touches the hooks.

The obvious check, the install command followed by the plugin list, passes completely. The symptom appears only in the next session, as a silent absence. An absence produces no error message.

The Claude Code binary is one 250 MB file that has node inside it. This does not help. It does not expose `node` on the PATH under that name.

**The method that caught it.** The check looks at what the plugin calls, not at the plugin itself. Read the hooks file in `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`. Find the first command word. Then look for that program on the PATH.

The general rule: **a plugin that installs successfully says nothing about the programs it calls.**

## The hooks file read wrongly

**The symptom.** A plugin repository contains a `hooks.json` that calls only `echo`. The conclusion seems clear: the plugin needs nothing installed.

**The cause.** Repositories that target several tools keep one set of hooks for each tool. A `hooks.json` that contains only an `echo` may belong to another tool, not to Claude Code. The hooks for Claude Code sit in a completely different file.

**Why it is a pitfall.** Both files are real, and both have plausible names. A search for `hooks.json` finds the wrong one first. The other file does not even have "hooks" in its name.

**The method that caught it.** Do not search for the file by name. Read the plugin manifest instead. The manifest declares the path of its hooks in the `hooks` field.

The general rule: **in a repository with several tools, the manifest says which file matters. The file name does not.**

## RTK saving less than expected

**The symptom.** `/rtk-plugin:gain` shows a saving far below the one in the documentation example. RTK is the tool that shortens the output of commands before it reaches the conversation. The saving should therefore be large.

**The cause.** The dispatcher leaves uncompressed any command that contains shell constructs: `|`, `&&` and `$()`. The exclusion is deliberate, so that existing scripts do not break. A workflow built from `grep ... | head -20` bypasses the compressor entirely.

**Why it is a pitfall.** The programs used *are* on the list of 43 supported programs. `grep` is on it, and `git` is on it. The obvious check, "is my program on the list?", passes. What decides is not the program. It is the shape of the command.

**The method that caught it.** Compare the real shape of the commands, not the programs. The general rule: **when a tool declares a list of accepted inputs, look for the list of exclusions too. The second list is usually shorter and more decisive.**

## The RTK binary downloaded without verification

**The symptom.** None. Everything works.

**The cause.** At the first session start, `scripts/bootstrap-rtk.mjs` downloads an executable from `github.com/rtk-ai/rtk/releases`. A search of the script for `sha256`, `checksum`, `signature` and `verify` returns zero matches.

**Why it matters.** That binary does not sit aside. It sits in front of every shell command, through the `PreToolUse` hook. It holds the deepest position of any of the three plugins.

This is not a reason to stop using it. A plugin downloaded from GitHub is foreign code that runs locally in any case. The other two plugins are in the same position, without downloading anything. It is a reason to know where the risk sits. The risk is not in the plugin. It is in the file that the plugin fetches later, from a repository other than the installed one.

## Ponytail and superpowers contradict each other only on small tasks

**The symptom.** None visible. The two mostly complement each other. Superpowers sets the order. Ponytail, the plugin that decides how much code to write, sets the size.

**The tension, where it exists.** Ponytail asks for the lazy version of a complex request, shipped with the question in the same response. It also says never to stall on an answer that can have a default. Superpowers asks for the opposite: invoke the skill before any response, including before clarifying questions.

The first rule pushes toward delivering something at once. The second pushes toward producing nothing before fixing the method.

**How to resolve it.** Do not choose one of them. The two conflict only on small tasks, where ponytail is right. A one-line request does not deserve about 3,800 tokens of brainstorming. On large tasks superpowers is right. Shipping the lazy version quickly is exactly the mistake that the order prevents.

The practical split: **ponytail decides how much to write. Superpowers decides whether the work is worth starting.** When the task is clearly small, the first rule wins.
