# How to load skills at the start of a session

The installed skills (sets of instructions that enter the conversation when the
situation matches) are already visible in any session — their descriptions load
by themselves. What does not load by itself is the **order**: which skill comes before
which, and which mode is stopped before what.

There are three ways to supply it, in the order of the effort required.

## 1. Through `AGENTS.md` and the tool module — automatic, with no action

The `AGENTS.md` file holds the shared rules for every tool, and loads in every
session started from its folder or from any subfolder. Claude Code reads it on
its own, through the setting configured by the restore; Antigravity, through
local files. It is not pasted, not mentioned, and cannot be forgotten.

The file already exists at the workspace root — [AGENTS.md](../../AGENTS.md) —
and covers all the projects below it, because they all sit in `projects/`. It is
not copied anywhere: a single copy is active in any session started from any
project.

It is checked in a new session by asking for the order of the skills. If the answer
knows it without it having been given, the file was loaded.

Rules specific to a single project do not belong here. They sit in the project's
`AGENTS.md`, with `CLAUDE.md` alongside it, and load just as automatically when
the session starts from that project's folder.

Together, both are part of the chain of rules (all rule files from the root down
to the folder being read), but each tool gathers it differently:

- **Claude Code** loads `CLAUDE.md` and `AGENTS.md` at launch from the starting
  folder and its parents; `AGENTS.md`, with the setting configured by
  `bin/restore-env.sh`. Those in subfolders enter only at the first file read from
  there with the Read tool; `cat` does not bring them.
- **Antigravity** does not climb above the open folder. Parent rules, house
  rules, and the memory index are brought to it by the local
  `.agents/rules/framework-NN.md` files, written by `bin/antigravity.sh` in every
  repository and folder with rules.

## 2. Through a reference to a file — for a document that does not load by itself

In Claude Code, any file is brought into the conversation by writing its path
preceded by `@`:

```
@projects/<project>/STATE.md
```

The path can be relative to the folder the session started from, so it need not
be written absolute. The content enters whole.

It is used for project documents that are not rules and so do not load
automatically: `STATE.md`, the state file (the project's state and what comes
next, rewritten at every end of session), and `IMPACT.md`, the impact map (the
table of what breaks at each change, with the command that checks it).

The two combine without repeating: `AGENTS.md` brings the order of the skills,
while the reference brings the state of the project.

## 3. Through a reference to `AGENTS.md` — for a session outside the folder

When a Claude Code session starts outside the workspace, the rules are brought
in with `@`, using the path to `AGENTS.md`:

```
@<workspace root>/AGENTS.md
```

A pasted copy falls behind at the first changed rule; the reference always
brings today's text.

## None of the three forces a skill

None of them **forces** the invocation of a skill. All three raise the
probability, by putting the rule up front. The only mechanism that really runs
without a decision is the hook. The three mechanisms are described in
[How a plugin comes to apply](../explanation/how-a-plugin-applies.md).

The confirmation stays the same in all cases: the announcement
`Using [skill] to [purpose]`. Its absence means the skill was not applied,
however many files were loaded.
