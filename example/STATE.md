# example — state and the next session

> Rewritten on 2026-09-22, at the close of the session in which the orchestrator merged
> `execute/greeting` into `main` and closed the work item.
>
> Whatever is closed **leaves** this file:
> - System problems go to records/journal/.
> - Pitfalls go to records/pitfalls/.
> - The human's decisions go to records/decisions/.
> - Decisions worth explaining go to `docs/explanation/`.
>
> The rest is deleted. Git keeps it anyway.

## What changed today

The "Greeting" work item is closed. The orchestrator ran the verifiers on the branch again,
merged it into `main` with `git merge --ff-only`, and moved the folder into
`records/work/closed/`. `main` is now at `b7e04d6`. The executor's report went into that
folder. `closing.md` holds the evidence.

## The state, measured on 2026-09-22

| What | How many |
|---|---|
| commits in `main` over the template | 2 |
| tests in `tests/` | 1, with 2 checks |
| verifiable rows in `IMPACT.md` | 1 |
| open work items | 0 |

Re-measure with `git log --oneline`, `ls tests/`, `records/work/INDEX.md` and
`bin/check-maps.sh` from the workspace root.

## What does not work

Nothing open.

## Measurements still owed

None: every number above is read at the closing.

---

## The next session

### Read first, in this order

`records/work/INDEX.md`, then the `closing.md` of the work item, if the session resumes any
part of it.

### The work of the session

None handed over. The work item is closed, and the project has no other open one. A new
request starts from the spec, in a new session.

### What is NOT done in this session

The closed work item is not reopened. Anything more wanted from the script is a new work item.

### The first command

```bash
git status -sb && bash tests/test-greeting.sh
```

### Questions already asked and answered — not asked again

- Without a name, does the script greet the world? No: it exits with 2 and says how to use it.
- Does the project need rules of its own, an `AGENTS.md` with a `CLAUDE.md` beside it? No:
  it has nothing to say that would cost.
