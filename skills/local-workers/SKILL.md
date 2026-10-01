---
name: local-workers
description: Use when records/local-workers.md is being built or brought up to date - when the human says they have models or tools running on their machines, when a task would be worth delegating but the workers file is missing or empty, or when /local-workers is typed.
---

# The local workers file

`records/local-workers.md` is the only place from which the framework learns that
something runs on the human's machines to which work can be given. It comes empty.
As long as it is empty, execution delegates nothing and says once why.

## What the human is asked

In this order, one at a time:

1. which machines there are and which of them keeps models;
2. how each one is reached — a tunnel, `ssh`, a port — and what authentication it needs;
3. which tool takes a task and returns a diff, that is, the bridge;
4. how the machine is prepared and how it is released;
5. which models there are and **what was measured** for each;
6. which local tools that are not models are worth writing down.

## The rule of numbers

A number taken from the internet goes in **only** after it has been found in the
source page, with the link and the date next to it. The summary of a search is not a
source: once, a claim from a summary was not found in the page. A
number measured locally goes in with the command that re-measures it. A row without
numbers stays empty on purpose — a guessed row looks identical to a measured one, and
is worse than its absence.

## The six parts of the file

The exact headings, because `execute` looks for them by name:

`## The machines`, `## Access`, `## The bridge`, `## Preparing and releasing`,
`## The workers`, `## Local tools`.

## What never goes in

A token, a password, a private key, a LAN address, or a number without a source. The
file says **how** the token is obtained, never what it is.

## The bridge contract

It is written once, in `AGENTS.md`, under "The local worker is used first, when one exists": what the
bridge receives and what it returns, with the codes 0, 1 and 2. Any tool that honours
it can be the bridge. Toward house models, the framework ships none; toward models of
the other tool, it ships `bin/tool-bridge.sh`.
