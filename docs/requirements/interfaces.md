# Requirements of the `interfaces` scope

The commands a person or a pipeline runs: `contract check`, which reads a contract file, checks it
with the `contract` module and shows what it found, and `env check`, which self-checks a pack with
the `packs` module over the git and the podman adapters. They hold no logic of their own about
contracts or packs; `interfaces` is the place that builds the adapters. Each requirement follows an EARS template and has at least one
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

## `env check` ([ADR-0041](../adr/0041-the-environment-of-a-verified-project-is-a-dockerfile.md), [ADR-0044](../adr/0044-the-packs-module-drives-the-self-check-in-an-order-of-its-own.md))

The exit codes are those of INTERFACES-010 to INTERFACES-013, and a command line that is not valid
is INTERFACES-021. Known limit: the commit to start from has to be given by its full name; the
command does not resolve `HEAD`.

- **INTERFACES-050** When `env check` is run, the command shall self-check the pack in the file `.dokime/pack.yaml` of the project, or in the file given with `--pack`.
- **INTERFACES-051** When `env check` is run, the command shall take as the project the current directory, or the directory given with `--project`.
- **INTERFACES-052** When `env check` is run, the command shall start the self-check from the commit given with `--from`.
- **INTERFACES-053** If the name given with `--from` is not 40 lowercase hexadecimal characters, then the command shall report a single finding with the code `not-a-commit-name` and the verdict `ERROR`.
- **INTERFACES-054** When the pack has a finding, the command shall write the findings of its check and run nothing.
- **INTERFACES-055** When `env check` is run, the command shall read the Dockerfile at the path that the pack gives, from the directory of the pack.
- **INTERFACES-056** When `env check` is run, the command shall open the git adapter on the project and the podman adapter, and give the self-check the path and the version of each program.
- **INTERFACES-057** If an adapter refuses to open, then the command shall report its finding, with the verdict `ERROR`, and run nothing.
- **INTERFACES-058** If the pack file cannot be read as UTF-8 text, then the command shall report a single finding with the code `unreadable-file` and the verdict `ERROR`.
- **INTERFACES-059** If the harness receives SIGINT or SIGTERM while `env check` runs, then the command shall close the adapters, leaving no container and no temporary directory of the run, and let the interruption go on.

### What `env check` writes

- **INTERFACES-060** When the adapters are open, the command shall write one line for each program, with its name, its path and its version, before the self-check starts.
- **INTERFACES-061** When the self-check ends, the command shall write one line for each candidate looked at, with its commit, whether it is a witness and the tests that turned green.
- **INTERFACES-062** The command shall write each finding of `env check` as `path: VERDICT code: message`, the path being the file of the pack.
- **INTERFACES-063** The command shall end the output of `env check` with the line of the verdict of INTERFACES-005.
- **INTERFACES-064** When the option `--format json` is given to `env check`, the command shall write one JSON document with the pack, the verdict, the programs, the candidates and the findings, each candidate with its commit, the tree, the image and the base of each side, whether it is a witness and the tests that turned green.
