@AGENTS.md

## Only for Antigravity

The shared rules are in `AGENTS.md`. Antigravity reads that file by itself. The first line above imports it for Gemini CLI. Checked on 1 October 2026, with application 2.19.1 and the `agy` CLI 1.2.14. For a new version, check again with the [Antigravity reference](docs/reference/antigravity.md).

### Models by tier

| Tier, in the head of the plan | Model, with the identifier for `agy --model` |
|---|---|
| large, thinking `max` or `high` | Gemini 3.1 Pro, thinking High: `gemini-3.1-pro-high` |
| medium, thinking `xhigh` or `high` | Gemini 3.8 Flash, thinking High: `gemini-3.8-flash-high` |
| medium, thinking `medium` | Gemini 3.8 Flash, thinking Medium: `gemini-3.8-flash-medium` |

On AI Pro, the quota resets every five hours, up to a weekly limit. All Gemini models use the same quota. The Claude models in Antigravity, Sonnet 4.6 and Opus 4.6, have their own quota. When the Gemini quota runs out, the execution tier moves to `claude-sonnet-4-6`. Measured on 1 October 2026, with the Gemini quota used up.

### Rules above the open folder come from local files

Antigravity reads `AGENTS.md` and `GEMINI.md` from the open folder by itself. It does not go higher. The `.agents/rules/framework-NN.md` files bring the rules of the parent folders and the memory index. Each file holds one include. `bin/antigravity.sh` writes them into every repository and folder with rules, and keeps them out of git.

The documentation says that, when a file in a subfolder is touched, Antigravity also loads the rules there. The test without an interface did not see this. For that reason, open the session in the folder named in the handoff, not above it.

Reason: the loading test of 1 October 2026, with a marker word in each file. The 24,000-byte limit of a rules file is counted after the includes are added.

### Skills, plugins and modes

- The framework skills, and those of superpowers and ponytail, are linked in `~/.gemini/config/skills/`. They come from the same folders as in Claude Code. `bin/antigravity.sh` links them.
- Antigravity has no Skill tool. It loads a skill by reading its `SKILL.md`, or with `/<name>`. A skill named in the rules as `superpowers:<name>` is the skill `<name>`.
- Antigravity has no hook at session start. So superpowers and ponytail start from the global rules that are always active in `~/.gemini/config/rules/`. Stop ponytail with "stop ponytail".
- Before each model call, the `memento` hook in `~/.gemini/config/hooks.json` adds a note. After a skill is read, the note asks for its announcement. After an edit, the note asks for the sentence about it. `bin/antigravity.sh` links this whole hook.
- rtk does not rewrite commands itself. Its global rule asks for `rtk` before `git` commands and tests. Those are the only commands that go through the terminal anyway.
- Announce a skill in the same reply as the call that reads it, before the call: `Using <skill> to <purpose>`. The rule also holds for `end-of-session`.

### Where the rules require a stop, the session asks with `ask_question` and waits

Antigravity is built to carry a task to the end by itself. The "Turbo" permission preset runs its commands without asking. The rules require a stop in these places:

- the questions of brainstorming, one at a time, before the options
- a decision that the plan does not cover
- the "yes" at the end of an execution, before the merge and the push

Put each stop in `ask_question`, one question at a time. Do not continue until there is an answer. An answer that was skipped is not a "yes". Stop, and say what you wait for.

The window shows only the question and the options. So explain the options in the chat, before the window, under the rule in `AGENTS.md`. Write whole sentences. Say what each option means, what the person gains, what the person risks, which option you recommend, and why. In the window, put the recommended option first, with "(Recommended)".

In the spec, the first question is about the purpose: what the person wants to get, and how the person knows it works. The constraints follow. The architecture options come only after them.

`AGENTS.md` asks for facts from outside the framework before the options. Search for them with `search_web`. Read them from their page with `read_url_content`. Do not propose an option that names a service, a package or an API without a search made in this session. The rule holds even when the name seems known. The explanation of the option says what you found and where.

Approval of a design, a part of a design, the spec or the plan is not a choice between options. Ask for it in the chat, without numbered options, with this sentence: "Approve? Answer "yes" or say what you change." The person answers a numbered list with its number, and "1" is not a "yes".

Make at most two searches or opened pages in the whole session, counted together. Antigravity has no reader, so the third search is not made. Write the remaining fact in the spec as an assumption, with the test that would settle it.

Reason: on 1 October 2026, two executions from Antigravity wrote the state file, committed and pushed without the person's "yes". A spec test skipped the clarifying questions. On 14 October 2026, three spec sessions made 6, 8 and 10 searches and pages, and two asked for approval with numbered options.

### Every sentence after a write or a check also says the percent

The note asks for the sentence about an edit. Add to it how much is done. Example: "I did 40%. About 6 minutes remain." The percent comes from the steps of the plan or of the spec. Without it, the person cannot see how long the wait is.

### Every session ends with `end-of-session`, in its order

Gemini skips the closing steps when it thinks the work is done. So the order is written here:

1. Read `skills/end-of-session/SKILL.md` and `skills/end-of-session/references/state-file-and-records.md`.
2. Show the list of what you write and what you commit. Then ask for a "yes" with `ask_question`.
3. Only after the "yes", write the state file, with the handoff in the form of the reference, and make the commit. The commit message is one sentence in the language of the repository. It says why, not what.
4. Write the last message. It has, in order: the folder, one model row per tool, and the prompt, in one block to paste. The row for Claude Code takes its model from `CLAUDE.md`, under "Models by tier". It follows the tier and the thinking in the plan. When no session follows, the message says why. For example, the work was closed by the orchestrator.

### The next session opens in the app, not in the terminal

The person works in the Antigravity app. A new session opens there, in the folder named in the handoff, with the model chosen from its menu. `agy` in the terminal is only for the bridge and the tests. So a handoff prompt is never an `agy` command.

The session ends with the handoff prompt. If the person then writes "continue", do not start the next session, least of all the plans session after a spec. Say that it opens new, with the prompt above.

### The output of a background command is not an answer

Antigravity puts the full output of each background command into the conversation, like a message. After each output, write what it means. Follow the rule in `AGENTS.md`: "Tell the person what you did, what came out, and what comes next."

### The worker in Claude Code

On the medium tier, a task with a verifier goes through the bridge to Claude Code. Start this command from the root of the repository you change:

```bash
bin/tool-bridge.sh --tool claude --model sonnet --target <file> --task <file> --verify '<command>'
```

The command needs `claude` signed in once, from the terminal, with `/login`. Add the command to the permission list of the terminal. Without sign-in, Sonnet 4.6 comes from Antigravity itself, with `--tool agy --model claude-sonnet-4-6`.

From inside a project, the command runs from the `bin/` of the workspace root, not from the `bin/` of the project. The bridge answers under the contract in `AGENTS.md`.

### The temporary folder and the subagents

The temporary folder of the session is a new folder under `/tmp`. The session makes it and removes it at the end. Any helper script stays there, not in the repository. A script left in the repository enters `git status`. With a `git add -A`, it also enters the commit.

The framework agents belong to Claude Code. In Antigravity, do not start any subagent, not even with `invoke_subagent`. A task list is a `task` artifact, not a tool. Do not write the `task` artifact in the session of a plan: the list of tasks is in the plan.
