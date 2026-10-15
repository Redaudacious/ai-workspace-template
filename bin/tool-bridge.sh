#!/usr/bin/env bash
# Bridge to the execution model of the other tool. A task with a verifier runs in
# an isolated working copy. The diff is emitted only if the verifier passed.
# The contract follows AGENTS.md, "The local worker is used first, when one exists":
# 0 and the diff, 1 for a refusal or a failed verifier, 2 when the task does not fit.
#
#   bin/tool-bridge.sh --tool agy|claude|vibe --model <id> --target <file> \
#                      --task <file> --verify '<command>' [--retries <n>]
#
# For vibe, `--model` is the profile in ~/.vibe/agents/ (`execute`, `execute-fast`).
# The profile fixes the model. BRIDGE_CAP sets the money cap of one call, 1 dollar by default.
#
# Call it from the repository that the task changes. The target is relative to its root.
set -uo pipefail

tool='' model='' target='' task='' verify='' retries=1
while [ $# -gt 0 ]; do
  case "$1" in
    --tool) tool="${2:-}" ;;
    --model) model="${2:-}" ;;
    --target) target="${2:-}" ;;
    --task) task="${2:-}" ;;
    --verify) verify="${2:-}" ;;
    --retries) retries="${2:-}" ;;
    *) echo "bridge: unknown argument: $1" >&2; exit 1 ;;
  esac
  shift 2 || break
done
case "$tool" in
  agy|claude|vibe) ;;
  *) echo "bridge: --tool is agy, claude or vibe, not '$tool'" >&2; exit 1 ;;
esac
if [ -z "$model" ] || [ -z "$target" ] || [ ! -f "$task" ] || [ -z "$verify" ]; then
  echo "bridge: missing --model, --target, --task or --verify" >&2; exit 1
fi
case "/$target/" in
  //*|*/../*) echo "bridge: target is relative to the repository and must not climb out of it: $target" >&2; exit 1 ;;
esac
limit="${BRIDGE_LIMIT:-150000}"
if ! [[ "$retries" =~ ^[0-9]+$ && "$limit" =~ ^[0-9]+$ ]]; then
  echo "bridge: --retries and BRIDGE_LIMIT must be numbers" >&2; exit 1
fi

repo="$(git rev-parse --show-toplevel)" || exit 1
root="$(cd "$(dirname "$0")/.." && pwd)"
# The agent rewrites the whole target, so the response must also fit. The task goes
# in a single argument, and Linux does not accept one larger than 128 KiB.
# Use `wc -c` and `cksum`, not `stat -c` and `md5sum`. Those two are GNU tools. Without
# them, the sizes and fingerprints below would be empty, so equal before and after the agent.
if [ "$(wc -c 2>/dev/null < "$repo/$target" || echo 0)" -gt "$limit" ] \
   || [ "$(wc -c < "$task")" -gt 120000 ]; then
  echo "bridge: target exceeds $limit bytes or task exceeds 120000" >&2; exit 2
fi

if [ "$tool" = claude ]; then
  # As in `restore-env.sh`: use the binary in PATH, otherwise the newest one in the application folder.
  claude_bin="$(command -v claude || true)"
  [ -n "$claude_bin" ] || claude_bin="$(find "$HOME/.config/Claude" -name claude -type f 2>/dev/null | sort -V | tail -1)"
  [ -n "$claude_bin" ] || { echo "bridge: claude binary not found" >&2; exit 1; }
fi

agent() {  # prompt: runs the agent of the other tool in the current folder
  case "$tool" in
    agy) timeout 960 agy -p "$1" --model "$model" --sandbox --dangerously-skip-permissions \
           --print-timeout 900s </dev/null ;;
    # `--restricted` keeps the file tools inside the working folder and removes the
    # tools that run commands.
    claude) timeout 960 "$claude_bin" -p "$1" --model "$model" --restricted \
              --tools Read,Edit,Write,Glob,Grep --permission-mode acceptEdits </dev/null ;;
    # `--trust`: the copy is not in the trusted folders, and without it Vibe would not read
    # the `AGENTS.md` of the copy. Vibe keeps the terminal, so only the fingerprints
    # below catch a write outside the copy: those of the repository and of the verifier.
    vibe) timeout 960 vibe --agent "$model" -p "$1" --auto-approve --trust \
            --max-price "${BRIDGE_CAP:-1}" </dev/null ;;
  esac
}

state() {  # repository: its state by content, not only by file names
  { git -C "$1" -c core.quotePath=false status --porcelain -uall
    git -C "$1" diff HEAD --binary --no-color --no-ext-diff; } | cksum
}
list() { git -C "$1" -c core.quotePath=false status --porcelain -uall; }

before="$(state "$repo")"; list_before="$(list "$repo")"
base="$(git -C "$repo" rev-parse HEAD)"
tmp="$(mktemp -d)" || exit 1
# The copy sits at the depth of the repository relative to the workspace, with the
# `bin/` of each parent linked. Without the links, a test called by a relative path is
# missing and skips with 77, and the verifier passes without having run.
# The prefix is matched as a path, not as text: `/x/v` is not the parent of `/x/vsim/r`.
case "$repo/" in "$root"/*) rel="${repo#"$root"}" ;; *) rel="" ;; esac
copy="$tmp/space$rel"; mkdir -p "$(dirname "$copy")"
linked=()
if [ -n "$rel" ]; then
  up="$repo"
  while [ "$up" != "$root" ] && [ "$up" != / ]; do
    up="$(dirname "$up")"
    [ -d "$up/bin" ] && ln -sfn "$up/bin" "$tmp/space${up#"$root"}/bin" && linked+=("$up/bin")
  done
fi

# The verifier stays outside the copy: the files with absolute paths in the command, and
# the `bin/` of the parents, linked in the copy. An agent that rewrites them makes its
# own verdict. On 1 October 2026, two Gemini agents weakened their translation check this way.
verifier_fingerprint() {
  local w
  set -f
  for w in $verify; do
    w="${w//[\'\"]/}"
    case "$w" in /*) [ -f "$w" ] && cksum "$w" ;; esac
  done
  set +f
  for w in "${linked[@]}"; do find -L "$w" -type f -not -path '*/__pycache__/*' -exec cksum {} + 2>/dev/null; done
}
verifier_before="$(verifier_fingerprint)"
# Remove the copy on every exit. A bridge that leaves its copy on disk after a failure
# fills `git worktree list` with copies that nobody cleans up.
trap 'git -C "$repo" worktree remove --force "$copy" 2>/dev/null; rm -rf "$tmp"' EXIT
git -C "$repo" worktree add --quiet --detach "$copy" HEAD || exit 1

prompt="$(cat "$task")

You are working in $copy. Change only the file $target. Do not commit. When you finish,
the verification runs from this folder: $verify"

for ((i = 0; i <= retries; i++)); do
  (cd "$copy" && agent "$prompt") >"$tmp/agent.log" 2>&1
  # What the agent does outside the copy does not reach the diff, so check it separately.
  if [ "$(state "$repo")" != "$before" ]; then
    echo "bridge: agent changed the real working folder:" >&2
    diff <(printf '%s\n' "$list_before") <(list "$repo") >&2
    exit 1
  fi
  if [ "$(verifier_fingerprint)" != "$verifier_before" ]; then
    echo "bridge: agent changed verifier files outside the copy:" >&2
    diff <(printf '%s\n' "$verifier_before") <(verifier_fingerprint) >&2
    exit 1
  fi
  # Do not retry after an exhausted quota: a second call would get the same refusal.
  quota='RESOURCE_EXHAUSTED|usage limit reached|Rate limit exceeded|Price limit exceeded'
  if grep -qE "$quota" "$tmp/agent.log"; then
    echo "bridge: quota or cap of model $model is exhausted:" >&2
    grep -m1 -E "$quota" "$tmp/agent.log" | cut -c1-200 >&2
    exit 1
  fi
  if [ "$(git -C "$copy" rev-parse HEAD)" != "$base" ]; then
    echo "bridge: agent committed in the copy, so the diff would be empty" >&2; exit 1
  fi
  other="$(list "$copy" | cut -c4- | grep -vxF -- "$target" || true)"
  if [ -n "$other" ]; then echo "bridge: agent also touched: $other" >&2; exit 1; fi
  if (cd "$copy" && timeout "${BRIDGE_VERIFY_TIMEOUT:-900}" bash -c "$verify" </dev/null) \
       >"$tmp/verify.log" 2>&1; then
    git -C "$copy" add -N -- "$target"
    diff="$(git -C "$copy" diff --no-color --no-ext-diff -- "$target")"
    if [ -z "$diff" ]; then echo "bridge: agent did not change the target" >&2; exit 1; fi
    printf '%s\n' "$diff"
    exit 0
  fi
  prompt="$prompt

Verification failed. Its last lines:
$(tail -20 "$tmp/verify.log")"
done

echo "bridge: verifier did not pass after $((retries + 1)) attempts" >&2
tail -20 "$tmp/verify.log" >&2
echo "--- last lines of the agent:" >&2
tail -10 "$tmp/agent.log" >&2
exit 1
