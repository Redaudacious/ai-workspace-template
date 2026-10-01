# Conflicts and pitfalls

The pitfalls below (a pitfall is what cost time, with the method by which it was found)
were encountered while installing the four plugins. Each entry records the method used to
catch it, because that method can be applied again whereas the specific outcome cannot.

## An "enabled" plugin that does nothing

**The symptom.** `claude plugin list` displays `✔ enabled`, and the installation
reported success. None of the plugin's features actually run during the conversation.

**The cause.** The plugin's hooks run as separate processes, with the interpreter
resolved from the path. Three of the four installed plugins launch their hooks with
`node`. The host machine had no `node`: absent from `/usr/bin`, absent from dpkg, and
without nvm, fnm, volta, or bun.

**Why it is a pitfall and not a peculiarity.** The installation never verifies the
interpreter. It merely copies files and writes an entry to `~/.claude/settings.json`;
nothing in this chain touches the hooks.

The obvious check — running the install command, then checking the plugin list — passes
completely. The symptom appears only in the next session as a silent absence, and an
absence produces no error message.

The Claude Code binary is compiled into a single 250 MB file with Node inside. That
does not help: it does not expose an executable named `node` on the path.

**The method that caught it.** The check examines what the plugin calls rather than the
plugin itself. The hooks file is read from
`~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` to find the leading command
word.

That program is then looked up on the path. The general rule: **a successfully
installed plugin says nothing about the programs it calls.**

## The hooks file read wrongly

**The symptom.** A plugin repository contains a `hooks.json` file that specifies only
`echo`. The conclusion seems clear: the plugin needs nothing installed.

**The cause.** Repositories targeting several tools keep a set of hooks for each. In
caveman, the plugin that compresses the model's answers, `.codex/hooks.json` contains
an `echo` and is meant for Codex. The hooks for Claude Code sit in a completely
different file, `.claude-plugin/plugin.json`, and call `node`.

**Why it is a pitfall.** Both files are real, both have plausible names, and searching
for `hooks.json` finds the wrong one first — while the other does not even have "hooks"
in its name.

**The method that caught it.** Files should not be located by name alone. Instead, the
plugin manifest is read, which declares the hook path in its `hooks` field. The general
rule: **in a multi-tool repository, the manifest says which file matters; the filename
does not.**

## RTK savings lower than expected

**The symptom.** `/rtk-plugin:gain` shows savings far below the documentation's example.
Here RTK is the tool that shortens the output of commands before it reaches the
conversation, so the savings should be substantial.

**The cause.** The dispatcher leaves uncompressed any command containing shell
constructs — `|`, `&&`, `$()`. The exclusion is deliberate, so as not to break existing
scripts. A workflow built around `grep ... | head -20` bypasses the compressor entirely.

**Why it is a pitfall.** The programs used *are* on the list of 43 supported programs:
`grep` is there, and `git` is there. The obvious check — "is my program on the list?" —
passes. What actually decides is not the program name, but the command's shape.

**The method that caught it.** One compares the actual form of the commands given, not
the programs alone. The general rule: **when a tool declares a list of accepted inputs,
check the list of exclusions too; the second is usually shorter and more decisive.**

## The RTK binary downloaded without verification

**The symptom.** None. Everything works as expected.

**The cause.** At the first session start, `scripts/bootstrap-rtk.mjs` downloads an
executable from `github.com/rtk-ai/rtk/releases`. Searching the script for `sha256`,
`checksum`, `signature`, and `verify` returns zero matches.

**Why it matters.** That binary does not sit aside: it is placed in front of every
shell command, through the `PreToolUse` hook. It occupies the deepest position of any
of the four plugins.

This is not a reason to disable it — a plugin downloaded from GitHub is foreign code
running locally anyway, and the other three plugins share that situation without
downloading extra files. Rather, it is a reason to know where the risk lies: not in the
plugin package, but in a secondary file fetched later from an external repository.

## Caveman spoils the writing of documentation, unless it is stopped first

**The symptom.** Documentation is written in sentence fragments, without articles, and
without tables.

**The cause.** Caveman rules apply to every response until explicitly stopped. They
require stripping articles, allow sentence fragments, and forbid decorative tables.

**Why it is a real conflict and not a preference.** Good documentation demands
exactly what caveman removes: complete sentences that someone else can read a year
later. The two rule sets cannot be reconciled by adjusting intensity, because they
differ in purpose — one compresses text, while the other builds it as a product.

**How it is avoided.** By stopping the mode beforehand rather than correcting text
afterward: send "stop caveman" or `/caveman off` before writing documentation, and
restart it afterward. The steps are in [How to switch modes](../how-to/switch-modes.md).

## Caveman and superpowers match the same request

**The symptom.** Two different skills (a skill is a set of instructions that enters the
conversation when the situation matches) match the same request.

**The cause.** Of the 21 skills in caveman, six cover ground already handled by
superpowers, the plugin that decides the order of the work.

Specifically, `investigate-first` covers `systematic-debugging`, `verify-and-stop`
covers `verification-before-completion`, `lean-build` covers the ponytail ladder, and
both `caveman-review` and `caveman-evidence-review` cover `requesting-code-review`.

**Why it is a pitfall.** The overlap does not produce an error, but a silent choice.
One skill is applied, and the absence of the other goes unnoticed.

**How it is kept under control.** By explicitly naming the desired family in the
request. A prompt that says "systematic" or "methodical" pulls toward superpowers; one
that says "caveman" pulls toward the other set.

## Ponytail and superpowers contradict each other only on small tasks

**The symptom.** None visible. The two complement each other for the most part —
superpowers sets the order, while ponytail (the plugin that decides how much code is
written) sets the size.

**The tension, where it exists.** Ponytail asks: "Complex request? Ship the lazy
version and question it in the same response. Never stall on an answer you can
default." Superpowers asks the opposite: the skill is invoked **before any response,
including before clarifying questions**.

The first rule pushes toward delivering something immediately. The second pushes
toward producing nothing before the method is fixed.

**How it is resolved.** Not by choosing one. The two contradict each other only on
small tasks, where ponytail is right — a one-line request does not deserve ~3,800
tokens of brainstorming. On large tasks superpowers is right, and the quick delivery of
the lazy version is exactly the mistake the order prevents.

The practical division: **ponytail decides how much is written, superpowers decides
whether it is worth starting.** When the task is clearly small, the first rule wins.
