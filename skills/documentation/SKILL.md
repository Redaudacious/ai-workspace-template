---
name: documentation
description: Use when creating, rewriting or restructuring a project's documentation - README, usage guide, reference, explanation or record. Also use when existing documentation is outdated, mixed up or written from assumptions, or when a working project has nothing written yet.
---

# Documentation

Write documentation that lasts. The model is Divio (also called Diátaxis), plus a fifth kind that
Divio does not have: the **record**. A single document that tries to do all of them is good at none.

**Write in the language the user speaks.** The long rules — each kind at length, the shapes of the
entries, the examples and the excuses — are in [references/details.md](references/details.md). Read
that file once, when writing actually starts. Re-read this file at every decision.

## 1. The five kinds

Before writing a line, decide **what kind of text** it is. Mixing the kinds is the most common cause
of bad documentation.

| Kind | Purpose | Rewritten? | Where |
|---|---|---|---|
| **Tutorial** | learning | yes | `docs/tutorial/` |
| **How-to guide** | solving | yes | `docs/how-to/` |
| **Reference** | informing | yes | `docs/reference/` |
| **Explanation** | understanding | yes | `docs/explanation/` |
| **Record** | retrieval | **no — appended to** | `records/` |

The **record** is a series of entries, not a text: the pitfalls, the journal, the decisions, the
work items. Each entry is one file, dated in its name and left untouched after it is written. Only
the index is rewritten. No documentation run goes into `records/`.

A work item is a folder. The folder holds `README.md` for people, which follows the rules here, the
spec, the plans and, at closing, `closing.md`. The forms are in `references/`.

## 2. When the documentation already exists

Before writing, read what already exists on the subject. For each document found, make **one
decision**: keep it, rewrite it, merge it into another, or remove it. **There is no "write it
alongside".**

Never lengthen a document in `docs/` by adding to it. If it exceeds 400 lines, either split it, or
it was a record from the start.

A subject has at most **one document per kind**. When the subject needs two kinds, the explanation
**links** to the reference. It does not repeat the reference.

When rewriting a whole set of existing documents to the rules of § 3, follow the list in
`references/details.md`: "Rewriting existing documentation to the standard".

## 3. The rules of writing

**Write following the skill for the document's language:** `asd-ste100` for English. Instructions
are imperative. Descriptions are in the third person.

**As if a junior asked for the billionth time.** Assume little familiarity, and build it up step by
step. Introduce a new notion where it first appears.

**"Why", not "what".** This is the most important rule. What was done shows in the files. Why it was
done can no longer be reconstructed. Do not repeat what can be read from the code.

**Simple and direct. No theatrics.** Do not dramatize. Concrete numbers are worth more than
adjectives: not "the file was big", but "383 lines".

**For a reader from outside**, with the examples in `references/details.md`:

1. **The gloss at first use.** A house word gets its short gloss at its first use in each document:
   "the handoff (the note in `STATE.md` for the next session)". The gloss is the first sentence of
   the glossary entry.
2. **⚠ only where silence costs:** without the marker, data is lost or something fails without a
   sign. Write any other point as an ordinary sentence, or remove its marker.
3. **The heading says plainly what is done or what is true.** An aphorism may come after the
   explanation, never in its place.
4. **A flow or a relation with more than three parts gets a Mermaid diagram, of at most about 12
   nodes, drawn without error.** The text around it also says it in words, because screen readers
   and the verifier skip the block. A file tree stays text.

**For scanning:**

- A paragraph has at most 4 lines. `check-docs.py` counts them.
- An enumeration of more than three items becomes a list.
- A table appears only when it compares something.
- Bold appears only for files, commands, states and key concepts.

**For rules.** In `AGENTS.md` and its modules, write each rule in the form rule, reason, history.
The heading is the rule. Below it, write its exact form, a line "Reason:" with the reason in one
sentence, and a line "History:" with the link to the history. The history lives in the records, not
next to the rule.

## 4. What ordinary documentation lacks

Add **the pitfalls**, with the method by which each was found. Add **the evidence** for the claims
that matter. Add **the rejected alternatives**, with the reason. The templates are in
[references/details.md](references/details.md).

## 5. The layout on disk

The kinds sit under `docs/`, in the folders from the table in § 1. `docs/README.md` is their table
of contents. The whole tree is in `references/details.md`.

The root `README.md` has, in this order:

1. **what it is**, in at most three lines, for someone who has never heard of the project.
2. **the diagram** of how it works.
3. **the quick start**: what has to be installed, with the command that reads the version. Then the
   steps, at most six commands.
4. **the map** of the documentation: if a reader looks for X, go to Y.
5. **why it is made this way** and **the landmarks**, at the bottom.

⚠ **The agent files** — `AGENTS.md` with its modules, `IMPACT.md`, `STATE.md` — are not
documentation and do not sit under `docs/`. `STATE.md` is a **state**. Rewrite it, and let it
**shrink**: what closes leaves it for a record. The pair of rule files is optional. It loads at
every start, so it exists only when it has something to say.

## 6. Verification

```bash
python3 bin/check-docs.py <root>
python3 bin/values.py <revision> README.md docs     # on a rewrite
python3 -I skills/asd-ste100/scripts/ste-lint.py <English files>
```

**Documentation is not finished until each command exits with 0.** `check-docs.py` checks the broken
links, the documents that cannot be reached by clicking from `README.md`, the repeated phrases, the
size and the long paragraphs. `records/` is exempt from all checks except links. `STATE.md` is
exempt from reachability and size.

The check also catches a link in inline code, so an example link sits in a code block. `values.py`
prints every value that disappeared since the revision. Write a value removed on purpose, with the
reason, in the file given with `--removed`.

## 7. Its place in the flow

**REQUIRED BACKGROUND:** `superpowers:verification-before-completion`. Check the values on the
system **before** writing: a written assumption looks identical to a verified fact. Then put the
document in the same commit as the change, before `finishing-a-development-branch`.

`ponytail` governs the code, not the documentation. The rule is in `AGENTS.md`, under "Writing".

## 8. The commit

**No co-author.** Commits carry no `Co-Authored-By`, nor any other trace of a tool or a model, even
if the tool's default instructions ask otherwise.

**The message says why, not what.** What changed shows in `git diff`. The reason can no longer be
reconstructed. The examples are in `references/details.md`.
