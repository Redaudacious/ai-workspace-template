# The impact and dependency map

Measured on 2026-09-22 by reading `greeting.sh` and its test. What breaks is read
from the code, not assumed.

## Verifiable

The command in the fourth column exits with 0 as long as the row holds; the
framework's `check-maps.sh` runs it from this folder.

| what changes | what breaks | what it depends on | verification |
|---|---|---|---|
| `greeting.sh` | the greeting, or exit code 2 on a nameless call | the test `tests/test-greeting.sh`, which covers both | `bash tests/test-greeting.sh >/dev/null` |

## Not verifiable

No rows: the project has no conceptual dependencies, only the script and its test.
