---
name: welcome
description: Use when the user writes "Start the house tutorial." or asks for the tutorial for a new user. Takes the user from the downloaded folder to their first project.
---

# Welcome to the house

This skill takes a new user from the downloaded folder to their first project. The user does not
know the words of the house yet. Explain each step in one simple sentence.

Ask one question in each message. Wait for the user's answer before the next step.

## 1. Measure, with no questions

Run the measurement from the root of the downloaded folder, each time the skill starts:

```bash
. /etc/os-release; echo "distribution: $ID ${ID_LIKE:-}"
for p in bash git python3 node claude; do command -v "$p" >/dev/null || echo "missing: $p"; done
[ "$(readlink "$HOME/.claude/skills/spec")" = "$PWD/skills/spec" ] && echo "restore: done"
[ -e records ] && echo "history: present"
ls -d projects/*/ 2>/dev/null | head -1
```

Go to the first step that is not done:

| what the measurement shows | the step |
|---|---|
| a `missing:` line for a program other than `claude` | 2 |
| the restore is not done, and the history is not present | 3 |
| the restore is not done | 4 |
| the restore is done, and `projects/` has no folder | 6 |
| `projects/` has a folder | 7 |

Tell the user what you found, in two sentences. Then start the step.

## 2. The programs

Give the user the command for their distribution. The command installs all the programs at once:

| the distribution, from `ID` or `ID_LIKE` | the command |
|---|---|
| `debian`, `ubuntu` | `sudo apt update && sudo apt install -y bash git python3 nodejs curl` |
| `fedora` | `sudo dnf install -y bash git python3 nodejs curl` |
| `arch` | `sudo pacman -Syu --needed bash git python nodejs curl` |

The command asks for the user's password, so the user runs it in their own terminal. Wait for
"done". Then measure again.

For a different distribution, tell the user the names of the programs. The user installs them with
their package manager.

If `claude` is not in `PATH`, the tutorial continues. The user then works in the desktop
application, and the restore finds the application's binary by itself.

## 3. The history

Ask: "Do you already have a git repository with `records/`, from a different machine?" Explain:
`records/` keeps the journal, the decisions and the agent's memory.

- If yes, ask for the address of the repository. Run `git clone <address> records`.
- If no, the restore makes an empty `records/`. Recommend a private git repository for it, later.
  The history then moves to the next machine.

## 4. The restore

Ask: "Do I run the restore now, `bin/restore-env.sh`?" Explain: the script writes in `~/.claude/`
and in `records/`. It also writes in the settings of Antigravity and Vibe, if they are installed. It
deletes nothing.

After "yes", run:

```bash
./bin/restore-env.sh
```

On code 0, go to step 5. On a different code, read the last lines. Tell the user what is missing:

| the message | what is missing |
|---|---|
| `node is missing` | `node`: go back to step 2 |
| `the claude binary was not found` | Claude Code: give the user the official install, https://code.claude.com/docs/en/setup |
| `is a real folder` or `is a real file` | a skill or an agent of the user, with the same name: the user moves it, then you run the script again |
| `missing from the list` or `does not load` | a plugin: follow the [guide to environment problems](../../../docs/how-to/fix-an-environment-problem.md) |

## 5. The restart

The plugins and the skills of the house load only in a new chat. Tell the user:

1. Open a new chat, in the same folder.
2. Paste the sentence "Start the house tutorial." again.

Stop here. The new chat starts with the measurement.

## 6. The first project

Ask the questions one at a time, each in its own message:

1. "What do you want to build?"
2. "What is the name of the project?" The name has lowercase letters and hyphens, because it
   becomes the name of the folder.
3. "Do you keep the project in git?" Recommend yes: git keeps each change, and the user can undo a
   mistake.

Make the folder from the template, as in step 1 of the [guide to a new project](../../../docs/how-to/start-a-new-project.md):

```bash
mkdir -p projects/<name> && cp -r template/. projects/<name>/
```

If the user wants git, read their identity:

```bash
git config user.name && git config user.email
```

If the identity is missing, ask which name and which address go in the commits. Then run:

```bash
git config --global user.name "<name>" && git config --global user.email "<address>"
```

Make the repository, as in step 2 of the guide:

```bash
git -C projects/<name> init -q -b main && git -C projects/<name> add -A && git -C projects/<name> commit -q -m "Project starts from the template"
```

Run `./bin/restore-env.sh` again. The script links the agent's memory for the project folder too.

The top documents and the copy on GitHub stay for the spec session.

## 7. The handoff

Give the user the way to the first spec session:

1. Open a terminal in `projects/<name>`. Run `claude`.
2. Select the Opus model, with effort `high`.
3. Paste the prompt below.

```text
Use the spec skill. I want <what the user said at the first question of step 6>.
```

The rest of the way is in [First work item, through the three sessions](../../../docs/tutorial/first-work-item.md).
