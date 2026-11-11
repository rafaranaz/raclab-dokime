# Requirements of the `interfaces` scope

The commands a person or a pipeline runs. This first increment has one, `contract check`, which
reads a contract file, checks it with the `contract` module and shows what it found. It holds no
logic of its own about contracts. Each requirement follows an EARS template and has at least one
test that declares it in its `SDD-EARS:` marker.

The decisions behind the output and the exit codes are in
[ADR-0040](../adr/0040-commands-exit-with-a-code-for-each-verdict.md).

## `contract check`

- **INTERFACES-001** When `contract check` is given the path of a contract file, the command shall write to the standard output one line for each finding of the check of that file, in the order the check gives them.
- **INTERFACES-002** The command shall write a finding as `path:line: VERDICT code: message`, with the first line of the finding.
- **INTERFACES-003** When a finding has more than one line, the command shall name the other lines at the end of its message.
- **INTERFACES-004** When a finding has no line, the command shall write it as `path: VERDICT code: message`.
- **INTERFACES-005** The command shall end its output with one line that gives the verdict and how many findings there are of each verdict.

## Exit codes

- **INTERFACES-010** When the verdict of the check is `PASS`, the command shall exit with the code 0.
- **INTERFACES-011** When the verdict of the check is `FAIL`, the command shall exit with the code 1.
- **INTERFACES-012** When the verdict of the check is `ERROR`, the command shall exit with the code 2.
- **INTERFACES-013** When the verdict of the check is `ASK`, the command shall exit with the code 3.

## What can go wrong

- **INTERFACES-020** If the contract file cannot be read as UTF-8 text, then the command shall report a single finding with the code `unreadable-file` and the verdict `ERROR`.
- **INTERFACES-021** If the command line is not valid, then the command shall write how it is used to the standard error and exit with the code 2.

## Output for programs

- **INTERFACES-030** When the option `--format json` is given, the command shall write to the standard output a single JSON document with the file, the verdict and the findings.
- **INTERFACES-031** When the option `--format json` is given, the command shall give for each finding its code, its verdict, its message and its lines.

## Running it

- **INTERFACES-040** When the package `dokime.interfaces` is run as a module, the command shall behave as when its entry function is called with the same arguments.
