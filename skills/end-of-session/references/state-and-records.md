# The template of the state file and the format of the entries

Read once, when writing starts. The procedure is in `SKILL.md`.

## The state file: `STATE.md`

```markdown
# <repository name> — state and the next session

> Rewritten on <date>, at the closing of the session in which <what was finished>.
>
> Each closed item leaves this file. System problems go to
> `records/journal/`, pitfalls to `records/pitfalls/`, the human's decisions to
> `records/decisions/`, decisions worth explaining to `docs/explanation/`.
> The rest is deleted, because git keeps it anyway.

## What changed today

<What was finished, not what was touched. Each item with its reason.>

## The state, measured on <date>

<A table of numbers, each read now, with the command that re-measures them named below.>

## What does not work

<Only the open problems. "Nothing open" is a good answer.>

## Measurements still owed

<What was claimed without being verified.>

## The execution report

<Only after a hand execution, done by the human in another tool. One row per task, in the order of the plan. The executor writes its report in the work item's folder, not here.>

| Task | Who did it | The verifier | Deviations from the plan |
|---|---|---|---|
| <n> · <name> | the session · bridge, `<MODEL>` · the session, after the bridge with code <1 or 2> | `<command>` — passed | nothing · <what and why> |

Verification: the orchestration, after the handoff below.

---

## The next session

### The handoff

<Only when the next session is a different one: the plans, the orchestration, or the hand execution of a plan. When none follows, the section stays and says so, with the reason. For example: "No session follows. The orchestrator has merged all plans, and the work item is closed.">

| | |
|---|---|
| session | plans · orchestration · execution |
| folder | `projects/<project>`, or the root. The session opens there. |
| tier | `<large for plans and orchestration; for hand execution, from the plan header>` |
| effort | `<high for plans, medium for orchestration; for hand execution, the "by hand" effort from the plan header>` |
| plan | `records/work/open/<folder>/<plan>.md`, relative to the folder above. For orchestration, the folder. |
| branch | `execute/<name>`. For orchestration, "from the header of each plan". |

The tools, per the modules at the root:

- Claude Code: <large or medium, with the effort from the rows above, per `CLAUDE.md`. No model identifier: the model is chosen from the application's menu.>
- Antigravity: <for hand execution, the identifier, per `GEMINI.md`. For spec, plans and orchestration, "no": they stay on Claude, at the large tier.>
- Vibe: <`vibe --agent <role>`, in the folder above, per `MISTRAL.md`. "no" for a role that no decision has assigned to Vibe.>

The prompt, to paste into a **new** session, after the tool and the model are chosen:

    <the prompt, on its own lines>

### Read first, in this order

### The work of the session

### What is NOT done in this session

### The first command

### Questions already asked and answered — not asked again
```

⚠ **A number that is too round is a ceiling, not a measurement.** "About 20 documents" is not a state. A count of `21`, read now, is a state.

⚠ **"What is NOT done" is not optional.** Without it, the next session expands into the first piece of work that looks close.

⚠ **"Measurements still owed" is the list that stops an assumption.** It keeps the assumption from passing into the next session as a fact. A claim not written there looks, a day later, exactly like a verified one.

⚠ **The handoff names the model, but does not change it.** The human opens a new session in the chosen tool. The human picks the model there. A model changed in the current session would carry the whole conversation with it. That conversation is the expensive part.

⚠ **The prompt is short, because the plan is long.** It names the folder or the plan, and the skill. For orchestration, write: "Orchestrate the work item `<folder>` with the skill `orchestration`." For a hand execution, write: "Execute the plan `<path>` with the skill `execute`. The role of the session comes from the plan header." Everything else that needs to be said is already in the plan.

## The last message to the human

Write the message in the chat, not only in `STATE.md`, at the end of any session. When no session follows, say so and give the reason, in place of the prompt.

For "what the human has to do", write that the human has nothing to do. Or list only the steps that only the human can take:

- **what the human has to do now**, in steps. Name the new session to open, and its folder. Add anything only the human can do (`sudo`, a login, a decision left open).
- **the next session's prompt**, with the models it goes with. Put the rows with the folder and the model of each tool **immediately above** the block. This way the human does not read the rows without the block, or the block without the rows:

  ```text
  New session · folder: projects/<project>
  Claude Code: <model> · effort <effort>
  Antigravity: <identifier, or "no", after the handoff>
  ```
  Write one row for each tool with a module at the root, after the handoff. Then the whole prompt follows, copied from the handoff, in a block that can be pasted.

⚠ The human reads the chat, not the state file. A handoff that exists only in `STATE.md` leaves the human to search for what comes next. A prompt without a model leaves the human to guess which model to run it on.

## The record entry

Name the file `YYYY-MM-DD-short-subject.md`. Do not rewrite the entry after writing it. Rewrite only `INDEX.md`. The `documentation` skill, at `references/details.md`, gives the forms of a decision, of `closing.md`, and of the rows in the work index.

```markdown
# <the symptom, as it was seen>

**Date:** <date>
**Where:** <the machine, the repository, the file>

## What was being pursued

## What happened

## The cause

## The method by which it was found

<The part that is reapplied. The result belongs to this day, the method does not.>

## What was done
```

Keep, in the row added to `INDEX.md`, the columns of the table that already exists there. Each register has other columns. Do not make them uniform here.

⚠ **A pitfall is not a journal entry.** A pitfall is something whose **finding method you can reapply**. A problem of the laptop or of the environment goes into `records/journal/`, with the machine written under "Where". A problem of a machine kept by a project, or of a tool of that project, goes into the journal of the project. That journal is in git.

## Divergence of a translated copy

A translated copy of the framework keeps, in a one-line file called `.source-commit`, the SHA of the commit from which it was last translated. When the folder of the translated copy exists, read the changes since then at the closing of a session:

```bash
git diff "$(cat <translated-copy>/.source-commit)"..HEAD --stat
```

If the output is empty, the translation is up to date. Write nothing in the state file. If the output lists files, write their number in the handoff, on one row. The command measures. It does not repair. A session does the translation, when the human asks for it.

⚠ Without the folder, skip this step silently. A human who starts from the template has no copy to keep up to date.

## The proof of usage

Keep, in the folder of the work item the chat worked on, the chat's API cost and its share of the 7-day limit. Both stay there after Claude Code deletes its logs. A usage panel rewrites the weekly files in `records/usage/weeks/` once a minute. `usage.py --proof` writes the proof from those files:

```bash
python3 <workspace root>/bin/usage.py --proof <session code>
```

- **The session code** is the name of the folder above the scratchpad in the session instructions. The first eight characters are enough.
- **The folder**: `usage.py` finds it. It is the one named in the human's first message. If the message names none, it is the one where the chat wrote files. For another folder, pass `--in <folder>`. Without either, the command exits with 2 and writes no proof.
- **The file** is `<folder>/usage/<day>-<role>-<code>.json`. It goes into the closing commit, in the repository of the work item. For orchestration, it includes the executor and the escalation runs, because they are the agents of the chat.
- **A public repository** does not get the proof. Before you write it, run `gh repo view --json visibility -q .visibility` from the repository of the work item. If the result is `PUBLIC`, skip this step, and say so.
- **The sum for the work item**, for `closing.md`: `python3 <workspace root>/bin/usage.py --work <folder>` prints "the work item cost X $ and Y% of the weekly limits". Write that row under "What came out".
