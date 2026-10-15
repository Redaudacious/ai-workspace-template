---
name: spec
description: Use in a work's spec session when the person wants something new, says "let's make the spec", or when STATE.md hands over the spec.
---

# The spec of a work

This session talks with the person and writes the spec. The spec says what to build, why, and how. It also lists the rejected options. This session does not write the plans or any code. A new plans session writes the plans. The rule in `AGENTS.md` keeps the spec and the plans in different sessions. The method belongs to `superpowers:brainstorming`. The places, names, and order of the steps are in this file.

Where `brainstorming` says something else, this skill applies:

- The spec does not go in `docs/superpowers/specs/`. It goes in the work folder.
- The spec is not followed by `writing-plans`. Section 6 stops the session instead.
- A work classified as "bounded" or "spike" also gets a spec, not an implementation.

## 1. Before the first question

Before each read, write one sentence in the chat. Say what you read and why.

1. **The repository state:** check it first. Apply the rule in `AGENTS.md` under the heading "The state of the repository is read first".
2. **The handover:** read the `STATE.md` of the repository. If it exists, also read `request.md` in the work folder.
3. **The rules and the map:** read the `AGENTS.md` and `IMPACT.md` of the repository. Then read the files that the request touches.
4. **The work folder:** `records/work/open/YYYY-MM-DD-subject/`, in the records of the repository that the work changes. The date is today.
5. **The method:** read all of `superpowers:brainstorming`. Then announce it in the chat with `Using brainstorming to ...`, in the same reply as the next step.

## 2. The questions

1. Before the first question, say in the chat what you understood from the request. Also say the kind of work, after `brainstorming`.
2. The first question is about the goal: what the person wants to get, and how the person sees that it works. Constraints come next. Architecture options come only after them.
3. Ask one question per message, at its end. Wait for the answer. The module of the tool says whether the question goes in the chat or in a window.
4. Give each option a letter or a number. Explain the options as the rule in `AGENTS.md`, "Tell the human what you did, what came out, and what comes next", says. Say what each option means, what it gains, and what risk the person takes with it. Then say which option you recommend, and why. Put the recommended option first.
5. **After each answer:** write one sentence that repeats it, so the person sees what you noted.
6. **`request.md`:** write it in the work folder after the first answer, with the words of the person, word for word. Complete it after each answer. An interrupted session does not lose it.

## 3. Facts from outside, before the options

Apply the rule in `AGENTS.md`, "Variants and the spec rest on verified facts". Check each tool, service, package, or model from outside this framework in its source, in this session, even when it seems known. Put the fact in the spec, with the link and the date.

1. The search gives the addresses. Read the fact on the source page, after you open it.
2. Test a fact about the machine or about a file on the real thing, with a small test. Tell the person the test before you run it. Delete the test after.
3. Say openly any assumption that remains, with the test that would settle it.
4. Give long pages and broad searches through code to the reader agent, where the module of the tool has one. The session gets the quotes with their source. The session checks the decisive figures itself.
5. For a package to install (npm, pip, cargo, or another), read its registry, age, download count, and source repository on the package page. Put them in the spec. Name as a risk a package without a source repository, or one published only a few days ago.

## 4. The options and the design

1. Propose two or three options, after section 2.
2. Write the design in numbered pieces, "piece 2 of 4". Make each piece as long as its complexity needs. After each piece, ask whether it fits. Write the spec only after the "yes" on the last piece.
3. Note on the spot what the person rejects, with the reason. Put the note in the spec, under the decisions.

## 5. The spec

1. **The file:** name it with the full name of the work folder, including its date at the start, followed by `-design.md`. Put it in the work folder, next to `request.md`. Without the date, the plans session does not find it by the folder name.
2. **The form:** start with the title `# <Work>: the spec` and a paragraph with the date and the source. Then write these parts, one after another:
   - what it aims at
   - the decisions taken with the person, with the rejected options
   - the design
   - how to see that it worked
   - what is out
   - the documents, under the heading `## Documents`: which documents the work changes, and why. Say also which new document a new feature gets, with its kind and place. Otherwise write "none", with the reason.
   - deviations from the framework rules that the person asked for, if any
   - what is not known yet, with the test for each item
   - the sources, with the link and the date
3. **The criteria:** write them under "How to see that it worked", one per line, with the number and the kind.

   ```markdown
   - **C1** (command: `<command>`): what must be true.
   - **C2** (person): what the person does and what the person must see.
   - **C3** (later, <YYYY-MM-DD>): what is measured on that date and how.
   ```

   The command exits with 0 while the criterion is true. "Person" is the criterion that only the person can judge. The person judges a "later" criterion only after some time. The plans name in their header the criteria they close. The script `python3 bin/check-docs.py --criteria <folder>` fails on a criterion that no plan closes.

4. **The writing:** apply the skill `asd-ste100` and the rules of the skill `documentation`.
5. **The check:** run `python3 bin/check-docs.py <root of the repository>`. The script must exit with 0. Also check that a Mermaid diagram draws without error.
6. **The reread:** reread the spec. Nothing may stay empty, nothing may contradict, and nothing may read in two ways. Repair what you find before the commit.
7. **The commit:** make it in the repository of the work. Write one sentence in the language of the repository that says why. Do not use prefixes such as `docs:`, and do not add `Co-Authored-By`.
8. **The person reads the spec** and says "yes", or says what to change.

## 6. Stop

After the "yes" on the spec, do not write the plans. Close the session with `end-of-session`. The handover of `end-of-session` asks for a new plans session. That session runs on the large tier, with effort `high`, in the folder of the work's repository.
