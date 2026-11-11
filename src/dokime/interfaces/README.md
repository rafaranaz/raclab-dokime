# interfaces

The commands a person or a pipeline runs. A command reads its input, calls the module that does
the work and shows the result; it holds no logic of its own about contracts.

## `contract check`

Validates a contract file and says what it lacks.

```console
$ python -m dokime.interfaces contract check change/contract.yaml
change/contract.yaml:12: FAIL duplicate-id: the id 'E-4f1a' appears 2 times among the examples (also line 31)
change/contract.yaml:40: ASK requirement-without-example: the requirement 'keep-totals' has no example
FAIL: 2 findings (1 fail, 1 ask)
```

Each finding is one line on the standard output, `path:line: VERDICT code: message`, in the order
of the lines of the file, and the last line gives the verdict and the counts. A file that cannot
be read is a finding too, `unreadable-file`. With `--format json` the output is one JSON document
with the file, the verdict and the findings.

The exit code is that of the verdict
([ADR-0040](../../../docs/adr/0040-commands-exit-with-a-code-for-each-verdict.md)):

| Verdict | Exit code |
|---|---|
| `PASS` | 0 |
| `FAIL` | 1 |
| `ERROR`, and a command line that is not valid | 2 |
| `ASK` | 3 |

The codes of the findings are listed in the README of
[`contract`](../contract/README.md) and of [`core`](../core/README.md).
