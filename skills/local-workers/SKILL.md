---
name: local-workers
description: Use when an agent builds or updates records/local-workers.md. Use when the human says models or tools run on their machines. Use when a task deserves delegation but the workers file is missing or empty.
---

# The local workers file

`records/local-workers.md` is the only place where the framework learns that something runs on the human's machines and can take work. The file comes empty. As long as it is empty, execution delegates nothing and states the reason once.

## What to ask the human

Ask the human these questions, in this order, one at a time:

1. Which machines does the human have, and which of them keep models?
2. How does the human reach each machine: a tunnel, `ssh`, or a port? What authentication does it need?
3. Which tool takes a task and returns a diff? That tool is the bridge.
4. How is each machine prepared, and how is it released?
5. Which models does the human have, and **what was measured** for each?
6. Which local tools that are not models are worth writing down?

## The rule of numbers

Write a number taken from the internet **only** after you find it in the source page. Put the link and the date next to it. The summary of a search is not a source. On 19 September 2026, a claim from a summary was not found in the page.

Write a number measured locally together with the command that measures it again.

Leave a row without numbers empty, on purpose. A guessed row looks the same as a measured row. It is worse than a missing row.

## The six parts of the file

The headings are exact, because `execute` finds them by name:

`## The machines`, `## Access`, `## The bridge`, `## Preparing and releasing`, `## The workers`, `## Local tools`.

## What never goes in

Do not write a token, a password, a private key, a LAN address, or a number without a source into the file. The file says **how** to get the token, never what the token is.

## The bridge contract

The contract is written once, in `AGENTS.md`, under the heading "The local worker is used first, when one exists". That section says what the bridge receives and what it returns, with codes 0, 1 and 2. Any tool that honors the contract can be the bridge.

The framework ships no bridge toward house models. Toward models of the other tool, it ships `bin/tool-bridge.sh`.
