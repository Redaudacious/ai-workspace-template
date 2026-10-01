#!/bin/bash
# greeting.sh — prints "hello, <name>". Without a name, says how it is used and exits with 2.
[ $# -eq 1 ] || { echo "usage: greeting.sh <name>" >&2; exit 2; }
echo "hello, $1"
