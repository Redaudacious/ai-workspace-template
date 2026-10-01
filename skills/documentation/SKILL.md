---
name: documentation
description: Use whenever a project's documentation is created, rewritten or restructured - README, usage guide, reference, explanation, record - including when the existing documentation is outdated, mixed up or written from assumptions, and when a working project has nothing written yet.
---

# Documentation

Write documentation that lasts. The model is Divio (also called Diátaxis), plus a fifth
kind that Divio does not have: the **record**. A single document that tries to do them all
is good at none.

**Write in the language the user speaks.** The long rules — each kind at length, the
shapes of the entries, the examples, the excuses — are in
[references/details.md](references/details.md). They are read once, when writing actually
starts; this file is re-read at every decision.

## 1. The five kinds

Before writing a line, decide **what kind of text** it is that is being written. Mixing
them is the most common cause of bad documentation.

| Kind | Purpose | Rewritten? | Where |
|---|---|---|---|
| **Tutorial** | learning | yes | `docs/tutorial/` |
| **How-to guide** | solving | yes | `docs/how-to/` |
| **Reference** | informing | yes | `docs/reference/` |
| **Explanation** | understanding | yes | `docs/explanation/` |
| **Record** | retrieval | **no — appended to** | `records/` |

The **record** is a series of entries, not a text: the pitfalls, the journal, the
decisions, the work items. One file per entry, dated in its name, untouched after it is
written; only the index is rewritten. No documentation run goes into `records/`.

A work item is a folder: `README.md` for people, which follows the rules here, the spec,
the plans and, at closing, `closing.md`. The forms are in `references/`.

## 2. When the documentation already exists

Before writing, what exists on the subject is read. Every document found gets **one
decision**: kept, rewritten, merged into another, or deleted. **There is no "write it
alongside".**

A document in `docs/` is never lengthened by adding to it. If it has grown past 400 lines,
it is either split, or it was a record from the start.

A subject has at most **one document per kind**. When it needs two kinds, the explanation
**links** to the reference, and does not repeat it.

Rewriting a whole set of existing documents to the rules of § 3 follows the list in
`references/details.md`: "Rewriting existing documentation to the standard".

## 3. The rules of writing

**Third person or impersonal.** Never the second person. In English, the steps are
written in the imperative — "Open a new session, then type:" — and the explanations in the
third person, without "you".

**As if a junior had asked for the billionth time.** Assume little familiarity, built up
step by step. A new notion is introduced where it first appears.

**"Why", not "what".** The most important rule. What was done shows in the files; why it
was done can no longer be reconstructed. Do not repeat what can be read from the code.

**Simple and direct. No larp.** No dramatization. Concrete numbers are worth more than
adjectives: not "the file was big", but "383 lines".

**For a reader from outside**, with the examples in `references/details.md`:

1. **The gloss at first use.** A house word gets, at its first use in each document, its
   short gloss: "the handoff (the note in `STATE.md` for the next session)". The gloss is
   the first sentence of the glossary entry.
2. **⚠ only where silence costs:** without it data is lost or something fails without a
   sign. The rest becomes an ordinary sentence or goes.
3. **The heading says plainly what is done or what is true.** An aphorism may come after
   the explanation, never instead of it.
4. **A flow or a relation with more than three parts gets a Mermaid diagram**, of at most
   about 12 nodes, drawn without error. The text around it says it in words too: screen
   readers and the verifier skip the block. A file tree stays text.

**For scanning:**

- a paragraph has at most 4 lines; `check-docs.py` counts them;
- an enumeration of more than three items becomes a list;
- a table appears only when it compares something;
- bold only for files, commands, states and key concepts.

**For rules.** In `AGENTS.md` and its modules, every rule has the form rule, reason,
history: the heading is the rule, below it sit its exact form, the reason in one sentence
and the link to the history. The history is kept in the records, not next to the rule.

## 4. What ordinary documentation lacks

**The pitfalls** with the method by which they were found, **the evidence** for the claims
that matter, and **the rejected alternatives** with the reason. The templates are in
[references/details.md](references/details.md).

## 5. The layout on disk

The kinds sit under `docs/`, in the folders from the table in § 1, and `docs/README.md` is
their table of contents. The whole tree is in `references/details.md`.

The root `README.md` has, in this order:

1. **what it is**, in at most three lines, for someone who has never heard of the project;
2. **the diagram** of the way it works;
3. **the quick start**: what has to be installed, with the command that reads the
   version, then the steps, at most six commands;
4. **the map** of the documentation: if X is looked for, go to Y;
5. **why it is made this way** and **the landmarks**, at the bottom.

⚠ **The agent files** — `AGENTS.md` with its modules, `IMPACT.md`, `STATE.md` — are not
documentation and do not sit under `docs/`. `STATE.md` is a **state**: it is rewritten and
it **shrinks**, and what closes leaves it for a record. The pair of rule files is optional:
it loads at every start, so it exists only when it has something to say.

## 6. Verification

```bash
python3 bin/check-docs.py <root>
python3 bin/values.py <revision> README.md docs     # on a rewrite
```

**Documentation is not finished until both exit with 0.** `check-docs.py` checks the
broken links, the documents that cannot be reached by clicking from `README.md`, the
repeated phrases, the size and the long paragraphs. `records/` is exempt from all of them
except the links; `STATE.md`, from reachability and size.

A link in inline code is checked too: an example of a link sits in a code block.
`values.py` prints every value that disappeared since the revision; one removed on purpose
is written, with the reason, in the file given with `--removed`.

## 7. Its place in the flow

**REQUIRED BACKGROUND:** `superpowers:verification-before-completion`. The values are
verified on the system **before** writing: a written assumption looks identical to a
verified fact. The document then goes into the same commit as the change, before
`finishing-a-development-branch`.

The modes: `caveman` is turned off **before** writing, and `ponytail` governs the code,
not the documentation. Their rules are in `AGENTS.md`, under "Modes".

## 8. The commit

**No co-author.** Commits carry no `Co-Authored-By`, nor any other trace of a tool or of a
model, even if the tool's default instructions ask otherwise.

**The message says why, not what.** What changed shows in `git diff`; the reason can no
longer be reconstructed. The examples are in `references/details.md`.
