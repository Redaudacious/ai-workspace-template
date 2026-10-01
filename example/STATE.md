# example — state and the next session

> Rewritten on 2026-09-22, at the closing of the session in which the review merged
> `execute/greeting` into `main` and closed the work item.
>
> What closes **leaves** this file: system problems go to records/journal/, pitfalls to
> records/pitfalls/, the human's decisions to records/decisions/, decisions worth
> explaining to `docs/explanation/`, and the rest is deleted — git keeps it anyway.

## What changed today

The "Greeting" work item is closed: the review ran the verifiers on the branch, merged
it into `main` with `git merge --ff-only`, which is now at `b7e04d6`, and moved the
folder into `records/work/closed/`. The execution report left here for `closing.md`,
with the evidence.

## The state, measured on 2026-09-22

| What | How many |
|---|---|
| commits in `main` over the template | 2 |
| tests in `tests/` | 1, with 2 checks |
| verifiable rows in `IMPACT.md` | 1 |
| open work items | 0 |

Re-measured with `git log --oneline`, `ls tests/`, `records/work/INDEX.md` and
`bin/check-maps.sh` from the workspace root.

## What does not work

Nothing open.

## Measurements still owed

None: every number above is read at the closing.

---

## The next session

### Read first, in this order

`records/work/INDEX.md`, then the work item's `closing.md`, if anything from it is
picked up again.

### The work of the session

None handed over: the work item is closed and the project has no other open one. A new
request starts from the spec, in a new session.

### What is NOT done in this session

The closed work item is not reopened; anything more wanted from the script is a new
work item.

### The first command

```bash
git status -sb && bash tests/test-greeting.sh
```

### Questions already asked and answered — not asked again

- Without a name, does the script greet the world? No: it exits with 2 and says how to
  use it.
- Does the project need rules of its own, an `AGENTS.md` with a `CLAUDE.md` beside it? No:
  it has nothing to say that would cost.
