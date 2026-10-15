#!/bin/bash
# test-greeting.sh — the test of greeting.sh: the greeting, and the use without a name.
set -u
S="$(cd "$(dirname "$0")/.." && pwd)/greeting.sh"
[ "$("$S" Ana 2>/dev/null)" = "hello, Ana" ] || { echo "✗ the greeting is missing"; exit 1; }
"$S" >/dev/null 2>&1
[ $? -eq 2 ] || { echo "✗ without a name, the code must be 2"; exit 1; }
echo "✓ 2 tests passed"
