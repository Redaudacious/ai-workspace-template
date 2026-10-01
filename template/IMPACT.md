# The impact and dependency map

Measured on <date>, reading <what exactly: the installed code, the output of command X>.
The "what breaks" column is written from what the code does, not from what might be
assumed.

## Verifiable

The fourth column is a command that must exit with 0 as long as the row is true.
`bin/check-maps.sh` runs them all.

| what changes | what breaks | what it depends on | verification |
|---|---|---|---|
| `README.md` | the map in it | `docs/` | `test -f README.md` |

## Not verifiable

⚠ The rows below are **not** covered by `bin/check-maps.sh`. These are conceptual
dependencies that cannot be expressed as a command. Re-read them by hand whenever
something significant changes.

- <"if X changes, Y breaks, because Z">
