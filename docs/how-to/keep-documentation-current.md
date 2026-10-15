# How to keep the documentation current

This guide is for anyone who changes code and wants to know which documents fall behind. The tool
`bin/documents.py` compares the times in git. A document needs a reread when its code changed after
it.

The tool reads the documents map. The map is the `## Documents` section of `IMPACT.md`. It links
each document to the code that it describes. Without that map, the tool exits with 2.

The guide answers three questions.

## 1. How do you write a row in the documents map?

A row has two columns. The first column names a document: `README.md` or a `.md` file under
`docs/`. The second column names its code, as git patterns between backticks.

Keep the pattern narrow. Write only the code that the document names or explains. A wide pattern,
such as `bin/`, asks for a reread at every commit. The request then stops meaning anything.

A document that describes no code gets `—` instead of patterns. Examples are an explanation of
history and a glossary. The tool never asks for a reread of such a document.

```markdown
## Documents

| document | the code that it describes |
|---|---|
| `docs/explanation/method.md` | `server/tests/`, `bin/test` |
| `docs/reference/glossary.md` | — |
```

The document `method.md` describes the tests in `server/tests/` and their runner. When one of the
tests changes, the tool asks for a reread of the document. The glossary describes no code. So the
tool never asks for a reread of it.

Each new feature gets a row for its document.
The row goes into the same commit as the feature.

## 2. What do you do when the tool lists a document?

Run the tool from the root of the repository.

```bash
python3 bin/documents.py .
```

The output names the document, the last commit of its code, and what to do.

```text
reread needed: docs/explanation/method.md — code: 3f9a1c2 2026-10-14 The bash panel leaves the repository
Fix each document with the `documentation` skill. If a document is still true, name it in the commit message, with its path and the word “reread”.
documents in the map: 12, to do: 1
```

Read the document next to the changed code. Then choose one of two paths.

1. **The document is no longer true.** Fix it with the `documentation` skill, and commit it. The
   commit that touches the document removes it from the list.
2. **The document is still true.** Name it in the sentence of a commit. Write its path and the word
   "reread". The commit may touch any other file.

A commit with the mark looks like this.

```text
The bash panel leaves the repository, because the gate takes its place, and docs/explanation/method.md is reread and still true
```

The mark counts only if it is newer than the code change. A mark written before the change is not
enough.

An uncommitted change of the code counts as a change made now. Commit the code first, then the
document or the mark. A document committed before the code is older than the code. So the tool asks
for it again.

## 3. What do the exit codes mean, and what does `--complete` catch?

The tool exits with one of three codes.

| Code | What it means | What you do |
|---|---|---|
| 0 | no document needs a reread | nothing |
| 1 | at least one document needs a reread | fix it, or write the mark "reread" |
| 2 | `IMPACT.md` has no `## Documents` section | add the section, with its rows |

The `--complete` option does not look for stale documents. It checks the map itself.

```bash
python3 bin/documents.py . --complete
```

It catches three kinds of gap. Each one has its own message.

| Message | Cause | Fix |
|---|---|---|
| `no row: docs/new.md` | a new document has no row in the map | add the row |
| `document no longer exists: …` | the map names a removed or moved document | fix or remove the row |
| `code no longer exists: doc -> pattern` | a pattern no longer finds any file | fix the pattern |

Run `--complete` after you move or remove files. Without it, a broken row stays silent. Its pattern
finds nothing anymore. So its code never changes again.

For the other checks: [How to check that a plugin really works](check-a-plugin-works.md).
