#!/usr/bin/env bash
# Test for `bin/tool-bridge.sh`, with mock agents in a fabricated repository: no
# real model is called, and nothing here touches the machine.
set -u

R="${TESTS_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
D="$T/repo"; mkdir -p "$D" "$T/bin"
printf 'old\n' > "$D/target.txt"; printf 'other\n' > "$D/other.txt"
git -C "$D" init -q && git -C "$D" add -A \
  && git -C "$D" -c user.email=p@p -c user.name=p commit -qm start

# Mock agents do what MOCK_MODE requests, in the folder they are called from, and
# log every invocation with its arguments: this reveals retries, options, and any
# call that should not have happened.
for a in agy claude; do
  cat > "$T/bin/$a" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$(basename "$0") $*" >> "$MOCK_LOG"
case "$MOCK_MODE" in
  good)     printf 'new\n' > target.txt ;;
  bad)      printf 'wrong\n' > target.txt ;;
  other)    printf 'new\n' > target.txt; printf 'touched\n' > other.txt ;;
  real)     printf 'new\n' > target.txt; printf 'written covertly\n' >> "$MOCK_REAL/other.txt" ;;
  commit)   printf 'new\n' > target.txt; git add target.txt; git -c user.email=a@a -c user.name=a commit -qm agent ;;
  nothing)  ;;
  verifier) printf 'wrong\n' > target.txt; printf 'exit 0\n' > "$MOCK_VERIFY" ;;
  bin)      printf 'new\n' > target.txt; printf 'broken\n' > ../../bin/test-tool ;;
  quota)    echo 'AGY_ERROR: {"short_error":"RESOURCE_EXHAUSTED (code 429): Individual quota reached."}' ;;
esac
EOF
  chmod +x "$T/bin/$a"
done
export PATH="$T/bin:$PATH" MOCK_LOG="$T/log" MOCK_REAL="$D" MOCK_VERIFY="$T/external-verify.sh"
printf 'Write "new" in target.txt.\n' > "$T/task"
: > "$MOCK_LOG"

bridge() {  # [verify] tool arguments — the bridge, from the root of the fabricated repository
  local v='grep -qx new target.txt'
  case "${1:-}" in --verify) v="$2"; shift 2 ;; esac
  (cd "$D" && "$R/bin/tool-bridge.sh" "$@" --target target.txt --task "$T/task" --verify "$v")
}
clean() { [ "$(cat "$D/target.txt")" = old ] && [ "$(cat "$D/other.txt")" = other ] \
            && [ "$(git -C "$D" worktree list | wc -l)" -eq 1 ]; }

failed=0
check() {  # condition message
  if eval "$1"; then printf '  ✓ %s\n' "$2"; else failed=$((failed + 1)); printf '  ✗ %s\n' "$2"; fi
}

MOCK_MODE=good bridge --tool agy --model m >"$T/out" 2>"$T/err"; code=$?
check '[ "$code" -eq 0 ] && grep -q "^+new" "$T/out"' "good agent: code 0, with target diff on output"
check 'clean' "real folder unchanged, worktree copy removed"
check 'grep -q -- "--sandbox" "$MOCK_LOG" && grep -q -- "--dangerously-skip-permissions" "$MOCK_LOG"' \
  "agy runs locked down: sandbox, no prompts only inside copy"

: > "$MOCK_LOG"
MOCK_MODE=bad bridge --tool claude --model m >"$T/out" 2>"$T/err"; code=$?
check '[ "$code" -eq 1 ] && [ ! -s "$T/out" ]' "bad agent: code 1, nothing on standard output"
check '[ "$(grep -c "^claude " "$MOCK_LOG")" -eq 2 ]' "a single retry, so two calls"
check 'grep -q "Verification failed" "$MOCK_LOG"' "retry receives the last lines of the verifier"
check 'grep -q -- "--restricted" "$MOCK_LOG" && grep -q -- "--permission-mode acceptEdits" "$MOCK_LOG"' \
  "claude runs locked down: files inside copy only, without tools that run commands"
check 'clean' "even after a failure, real folder unchanged and worktree copy removed"

MOCK_MODE=other bridge --tool agy --model m >"$T/out" 2>"$T/err"; code=$?
check '[ "$code" -eq 1 ] && grep -q "other.txt" "$T/err"' "another file touched in copy: code 1, with its name"

MOCK_MODE=real bridge --verify false --tool agy --model m >"$T/out" 2>"$T/err"; code=$?
check '[ "$code" -eq 1 ] && grep -q "real working folder" "$T/err"' \
  "a write to the real working folder is reported, even with a failed verifier"
git -C "$D" checkout -q -- other.txt

MOCK_MODE=commit bridge --tool agy --model m >"$T/out" 2>"$T/err"; code=$?
check '[ "$code" -eq 1 ] && grep -q "commit" "$T/err" && [ ! -s "$T/out" ]' "a commit made by agent in copy: code 1"

MOCK_MODE=nothing bridge --verify true --tool agy --model m >"$T/out" 2>"$T/err"; code=$?
check '[ "$code" -eq 1 ] && grep -q "did not change" "$T/err"' "an agent that changed nothing does not pass as a success"

: > "$MOCK_LOG"
head -c 130000 /dev/zero | tr '\0' 'x' > "$T/large"
(cd "$D" && MOCK_MODE=good "$R/bin/tool-bridge.sh" --tool agy --model m --target target.txt \
   --task "$T/large" --verify true) >"$T/out" 2>"$T/err"; code=$?
check '[ "$code" -eq 2 ] && [ ! -s "$MOCK_LOG" ]' "a task over 120,000 bytes: code 2, without any call"

MOCK_MODE=good bridge --tool gemini --model m >"$T/out" 2>"$T/err"; code=$?
check '[ "$code" -eq 1 ] && grep -q "agy or claude" "$T/err"' "an unknown tool is refused, with message"
(cd "$D" && "$R/bin/tool-bridge.sh" --tool agy --model m --target ../outside.txt --task "$T/task" \
   --verify true) >"$T/out" 2>"$T/err"; code=$?
check '[ "$code" -eq 1 ] && [ ! -e "$T/outside.txt" ]' "a target climbing out of repository is refused"
MOCK_MODE=good bridge --tool agy --model m --retries two >"$T/out" 2>"$T/err"; code=$?
check '[ "$code" -eq 1 ] && grep -q "numbers" "$T/err"' "a retries count that is not a number is refused"

# A verifier located outside the copy cannot be rewritten by the agent: seen on
# 1 October 2026, when two Gemini agents weakened their own translation verification.
printf 'grep -qx new target.txt\n' > "$MOCK_VERIFY"
MOCK_MODE=verifier bridge --verify "bash $MOCK_VERIFY" --tool agy --model m >"$T/out" 2>"$T/err"; code=$?
check '[ "$code" -eq 1 ] && [ ! -s "$T/out" ] && grep -q "verifier" "$T/err"' \
  "an agent rewriting the verifier outside the copy: code 1, without diff"

: > "$MOCK_LOG"
MOCK_MODE=quota bridge --tool agy --model m >"$T/out" 2>"$T/err"; code=$?
check '[ "$code" -eq 1 ] && grep -q "quota" "$T/err" && [ "$(grep -c "^agy " "$MOCK_LOG")" -eq 1 ]' \
  "an exhausted quota is named explicitly, without retry"

# Without `md5sum` and `stat -c`, as on a stock macOS, the fingerprints came out empty
# and identical before and after: the bridge no longer saw what the agent wrote outside
# the copy.
mkdir -p "$T/no-gnu"
for u in md5sum stat; do printf '#!/bin/sh\nexit 127\n' > "$T/no-gnu/$u"; chmod +x "$T/no-gnu/$u"; done
MOCK_MODE=real PATH="$T/no-gnu:$PATH" bridge --verify true --tool agy --model m >"$T/out" 2>"$T/err"; code=$?
check '[ "$code" -eq 1 ] && [ ! -s "$T/out" ]' "without the GNU tools, a write to the real folder is still caught"
git -C "$D" checkout -q -- other.txt

# The copy sits at the depth of the repository, with parents' bin/ linked: a verifier
# calling a tool via a relative path finds it.
W="$T/space"; mkdir -p "$W/bin" "$W/projects/p"; cp "$R/bin/tool-bridge.sh" "$W/bin/"
printf 'x\n' > "$W/bin/test-tool"; printf 'old\n' > "$W/projects/p/target.txt"
git -C "$W/projects/p" init -q && git -C "$W/projects/p" add -A \
  && git -C "$W/projects/p" -c user.email=p@p -c user.name=p commit -qm start
(cd "$W/projects/p" && MOCK_MODE=good "$W/bin/tool-bridge.sh" --tool agy --model m --target target.txt \
   --task "$T/task" --verify 'test -f ../../bin/test-tool && grep -qx new target.txt') >"$T/out" 2>"$T/err"; code=$?
check '[ "$code" -eq 0 ]' "a project copy finds root bin/ via relative path"
(cd "$W/projects/p" && MOCK_MODE=bin "$W/bin/tool-bridge.sh" --tool agy --model m --target target.txt \
   --task "$T/task" --verify 'grep -qx new target.txt') >"$T/out" 2>"$T/err"; code=$?
check '[ "$code" -eq 1 ] && [ ! -s "$T/out" ] && grep -q "verifier" "$T/err"' \
  "a tool modified in parents' bin/, via the link in the copy: code 1, reported"

# A repository outside the workspace whose name starts like the workspace's: a text
# prefix is not a path prefix, and the climb towards bin/ went all the way to /.
mkdir -p "$T/v/bin" "$T/vsim/r"; cp "$R/bin/tool-bridge.sh" "$T/v/bin/"
printf 'old\n' > "$T/vsim/r/target.txt"
git -C "$T/vsim/r" init -q && git -C "$T/vsim/r" add -A \
  && git -C "$T/vsim/r" -c user.email=p@p -c user.name=p commit -qm start
(cd "$T/vsim/r" && MOCK_MODE=good "$T/v/bin/tool-bridge.sh" --tool agy --model m --target target.txt \
   --task "$T/task" --verify 'grep -qx new target.txt') >"$T/out" 2>"$T/err"; code=$?
check '[ "$code" -eq 0 ] && ! grep -q "ln:" "$T/err"' "a repository named like the workspace does not climb to /"

# A target that does not exist yet is measured without an error message.
(cd "$D" && MOCK_MODE=good "$R/bin/tool-bridge.sh" --tool agy --model m --target new.txt \
   --task "$T/task" --verify true) >"$T/out" 2>"$T/err"
check '! grep -q "No such file" "$T/err"' "a target that does not exist yet is measured without error"

[ "$failed" -eq 0 ] && echo "  all passed" || { echo "  $failed failed"; exit 1; }
