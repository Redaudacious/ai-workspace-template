# The template of the state file and the format of the entries

Read once, when writing actually starts. The procedure is in `SKILL.md`.

## The state file: `STATE.md`

```markdown
# <repository name> — state and the next session

> Rewritten on <date>, at the closing of the session in which <what was finished>.
>
> What closes **leaves** this file: system problems go to
> `records/journal/`, pitfalls to `records/pitfalls/`, the human's decisions to
> `records/decisions/`, decisions worth explaining to `docs/explanation/`,
> the rest is deleted — git keeps it anyway.

## What changed today

<What was finished, not what was touched. Each thing with its reason.>

## The state, measured on <date>

<A table of numbers, each read now, with the command that re-measures them named below.>

## What does not work

<Only the open problems. "Nothing open" is a good answer.>

## Measurements still owed

<What was claimed without being verified.>

## The execution report

<Only after an execution. One row per task, in the order of the plan.>

| Task | Who did it | The verifier | Deviations from the plan |
|---|---|---|---|
| <n> · <name> | the session · bridge, `<MODEL>` · the session, after the bridge with code <1 or 2> | `<command>` — passed | nothing · <what and why> |

Requests review: <no · yes, because …>

---

## The next session

### The handoff

<Only when the next session is another one: the execution of a plan, or the review of an execution.>

| | |
|---|---|
| session | execution · review |
| folder | `projects/<project>`, or the root — the session is opened there |
| model | `<from the plan header>` |
| effort | `<from the plan header>` |
| plan | `records/work/open/<folder>/<plan>.md`, relative to the folder above |
| branch | `execute/<name>` |

The tools, from the modules at the root:

- Claude Code: <model and effort, from `CLAUDE.md`>
- Antigravity: <identifier, from `GEMINI.md`>

The prompt, to paste into a **new** session after the tool and model have been chosen:

    <the prompt, on its own lines>

### Read first, in this order

### The work of the session

### What is NOT done in this session

### The first command

### Questions already asked and answered — not asked again
```

⚠ **A number that is too round is a ceiling, not a measurement.** "About 20
documents" is not a state; `21` read now is.

⚠ **"What is NOT done" is not optional.** Without it, the next session spreads over
the first piece of work that looks close.

⚠ **"Measurements still owed" is the list that stops an assumption** from slipping
into the next session as a fact. A claim not written there looks, a day later,
exactly like a verified one.

⚠ **The handoff names the model, but does not change it.** The human opens a new
session and chooses it from the menu. Changed in the current session, the model would
carry the whole conversation along, and that is the expensive part.

⚠ **The execution prompt is short, because the plan is long.** It is enough to name the
plan and the skill: "Execute the plan `<path>` with the skill `execute`. The role of the
session comes from the plan header." Everything else that would need saying is already
in the plan.

## The record entry

The file name: `YYYY-MM-DD-short-subject.md`. The entry **is not rewritten** once it
has been written; only `INDEX.md` is rewritten. The forms of a decision, of
`closing.md` and of the rows in the work index are in the `documentation` skill, at
`references/details.md`.

```markdown
# <the symptom, as it was seen>

**Date:** <date>
**Where:** <the machine, the repository, the file>

## What was being pursued

## What happened

## The cause

## The method by which it was found

<The part that is reapplied. The result belongs to this day; the method does not.>

## What was done
```

The row added to `INDEX.md` keeps the columns of the table that is already there —
every record has different columns, and they are not made uniform here.

⚠ **A pitfall versus the journal.** A pitfall is something whose **method of finding
is reapplied**. A problem of the laptop or of the environment goes into
`records/journal/` of the personal repository, with the machine written under
"Where". A problem of a machine kept by a project, or of a tool of its, goes into
the project's journal, which is in git.

## The template's divergence

`projects/ai-workspace-template/` is the English copy of the framework. It keeps, in a
one-line file called `.source-commit`, the SHA of the commit from which it was last
translated. When the folder exists, the closing of a session reads how much has gathered
since:

```bash
git diff "$(cat projects/ai-workspace-template/.source-commit)"..HEAD --stat
```

Empty output: the template is up to date, and nothing is written in the state file.
Output with files: their number goes into the handoff, on one row. The command
**measures**, it does not repair: the translation is paid for by a session, when the
human wants it.

⚠ Without the folder, the step is skipped silently. A human who starts from the template
has no copy to keep up to date.
