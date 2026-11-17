# Requirements of the `interfaces` scope

The commands a person or a pipeline runs: `contract check`, which reads a contract file, checks it
with the `contract` module and shows what it found, `env check`, which self-checks a pack with
the `packs` module over the git and the podman adapters, and `audit`, which audits a change that
arrives already made. They hold no logic of their own about
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
- **INTERFACES-061** When a candidate has been looked at, the command shall write its line, with its commit, whether it is a witness and the tests that turned green, before the next candidate is looked at.
- **INTERFACES-062** The command shall write each finding of `env check` as `path: VERDICT code: message`, the path being the file of the pack.
- **INTERFACES-063** The command shall end the output of `env check` with the line of the verdict of INTERFACES-005.
- **INTERFACES-064** When the option `--format json` is given to `env check`, the command shall write one JSON document with the pack, the verdict, the programs, the candidates and the findings, each candidate with its commit, the tree, the image and the base of each side, whether it is a witness and the tests that turned green.

## `audit`: the inputs

`audit` reads its inputs from the tree of the base commit, extracted into a directory of its own,
or from files given from outside the patch
([ADR-0064](../adr/0064-the-evidence-of-a3-is-an-unsigned-statement-with-a-closed-predicate.md)).

- **INTERFACES-070** When `audit` is given a story, the command shall read the contract at `.dokime/changes/<story>/contract.yaml` of the tree of the base commit.
- **INTERFACES-071** When `audit` is given a contract file with `--contract`, the command shall read the contract from that file.
- **INTERFACES-072** If the story given is not a name of letters and digits in words joined by hyphens, starting with a letter, then the command shall report a finding of the contract with the code `not-a-story` and the verdict `ERROR`.
- **INTERFACES-073** When the contract has been read, the command shall give as the findings of the contract those of its check by the `contract` module.
- **INTERFACES-074** If the `story` of the contract differs from the name of the directory that holds the contract file, then the command shall report a finding of the contract with the code `story-not-directory` and the verdict `ERROR` that names both.
- **INTERFACES-075** When `audit` is not given `--pack`, the command shall read the pack at `.dokime/pack.yaml` of the tree of the base commit and its Dockerfile beside it in that tree, never from the patch, since the pack says what is protected (`tests.paths`, `tests.config` and the sections of its mixed files) and a patch that changed it could unprotect its own tests.
- **INTERFACES-076** When `audit` is given a pack file with `--pack`, the command shall read the pack from that file and its Dockerfile from beside it.
- **INTERFACES-077** When the pack has been read, the command shall give as the findings of the environment those of its check by the `packs` module.
- **INTERFACES-079** When `audit` reads the policy, the command shall read `.dokime/policy.yaml` of the tree of the base commit, and take the defaults of the policy when the file is absent.

## `audit`: reading the tree without links

A patch can bring a symbolic link that points outside the tree, and the base can hold one, so what
`audit` reads of an extracted tree on the machine of the person follows no link, as the reader of
the report does ([ADR-0045](../adr/0045-a-test-report-is-read-by-a-bounded-reader-that-refuses-any-dtd.md)).

- **INTERFACES-085** When the command reads a file of an extracted tree, the command shall open each part of its path without following a link.
- **INTERFACES-086** If a part of the path of a file of the tree is a link, or the file is not a regular file, then the command shall report a finding with the code `file-not-regular` and the verdict `ERROR` that names the path.
- **INTERFACES-087** If a file of the tree that the command reads is missing, then the command shall report a finding with the code `file-missing` and the verdict `ERROR` that names the path.
- **INTERFACES-088** If a file of the tree that the command reads has more than 1 MiB, then the command shall report a finding with the code `file-too-large` and the verdict `ERROR` that names the path.
- **INTERFACES-089** If the contract, the pack or the policy cannot be read as UTF-8 text, then the command shall report a finding with the code `unreadable-file` and the verdict `ERROR`.

## `audit`: the run

`audit` goes through the states of the audit flow of A3
([`04-states-and-flows.md`](../architecture/04-states-and-flows.md#the-audit-flow)) over the ports
it is given, runs the gates of `verify` and builds the evidence with `evidence`
([ADR-0065](../adr/0065-the-evidence-of-a3-lists-every-gate-of-the-audit-flow.md)).

- **INTERFACES-090** When `audit` runs, the command shall go through the states of the audit flow in their order: `checking-contract` with `contract`, `preparing` with `environment`, `baselining` with `baseline`, `verifying` with `protected-paths`, `existing-tests`, `visible-examples`, `relations`, `changed-line-coverage`, `behaviour-differences` and `repeatability`, and `sealed` with `sealed-examples`.
- **INTERFACES-091** The command shall give its states the gates that, joined in the order of the states, are the gates of the audit flow that `evidence` requires.
- **INTERFACES-092** When a state ends with a verdict other than `PASS`, the command shall stop the run and list each gate of the later states as not reached, with the state and the verdict that stopped it, or as not applicable when this version does not build it.
- **INTERFACES-093** When `audit` runs, the command shall take the contract and the pack from the tree of the base commit or from the files given, never from the tree with the patch, so that a patch can neither change its own judge nor unprotect its own tests.
- **INTERFACES-094** When the state `checking-contract` runs, the command shall give the gate `contract` the findings of the contract read.
- **INTERFACES-095** When the state `preparing` runs, the command shall give the gate `environment` the findings of the pack read and, when a pack was read, build its image with the Dockerfile read, copied outside the tree, and the tree of the base as the context of the build.
- **INTERFACES-096** If the build of the image is refused, then the command shall give the gate `environment` the finding of the refusal.
- **INTERFACES-097** When the states `baselining` and `verifying` run, the command shall run the gates of `verify` with the contract, the pack, the policy and the image of the earlier states.
- **INTERFACES-098** When `audit` runs, the command shall record in the ledger `run.started`, `state.entered` for each state, `gate.started` and `gate.finished` for each gate that ran, `baseline.unstable` for each gate that left something out as unstable, `evidence.built` with the digest of the evidence, and `run.finished` with the verdict.
- **INTERFACES-099** When the run has gone through its states, the command shall build its evidence with the head of the ledger before `evidence.built`, the gates of every state, and the inputs the run reached.
- **INTERFACES-100** If the aggregation of a state gives findings of its own, then the command shall stop with the verdict `ERROR` and those findings, record `run.finished` with them, and write no evidence, since they are a fault of the harness and not a result of the run.
- **INTERFACES-101** When the state `verifying` runs, the command shall observe the examples of `visible-examples` in an image built with the tree of the change of [ADR-0058](../adr/0058-existing-tests-runs-the-tests-of-the-base-on-the-code-of-the-patch.md) as the context, as those of `baseline` are observed in the image built with the tree of the base, so that a pack that installs the project observes the code and the dependencies of the patch.
- **INTERFACES-102** If the build of the image of the change is refused, then the command shall give the gate `visible-examples` the finding of the refusal.
- **INTERFACES-103** When the image of the change has been built, the command shall record its digest in the event `gate.finished` of `visible-examples`, since the predicate records only the image of the environment.

## `audit`: from `verify` to `evidence`

`evidence` imports nothing but `core`, so `audit` converts the results of `verify` into the types of
`evidence`.

- **INTERFACES-105** When a result of a gate of `verify` is converted, the command shall carry each of its fields: the gate, its verdict, its findings, its checks, and what it left out as unstable, as tests for `existing-tests` and as examples for `baseline`.
- **INTERFACES-106** If a result of a gate other than `existing-tests` and `baseline` lists something as unstable, then the command shall refuse to convert it with an error that names the gate.

## `audit`: before the run

- **INTERFACES-110** If the patch does not apply on the base, or the tree of the base cannot be extracted, then the command shall end with the verdict `ERROR` and the finding of the refusal before the run starts, recording nothing and writing no evidence, since there is no tree to attest.
- **INTERFACES-111** If the policy of the base has a finding, then the command shall end with the verdict `ERROR` and the findings of the policy before the run starts.
- **INTERFACES-112** If the story of the run, the one given or the name of the directory of the contract given, is not a name, then the command shall end with the verdict `ERROR` and a finding with the code `not-a-story` before the run starts, since the file of the evidence is named after it.

## `audit`: the command

- **INTERFACES-120** When `audit` is run, the command shall take the project from `--project`, the current directory when it is absent, the base commit from `--base`, the patch from the file given with `--patch`, and either the story from `--story` or the contract from `--contract`, exactly one of the two.
- **INTERFACES-121** If the name given with `--base` is not 40 lowercase hexadecimal characters, then the command shall report a single finding with the code `not-a-commit-name` and the verdict `ERROR`.
- **INTERFACES-122** If the file given with `--patch` cannot be read, then the command shall report a single finding with the code `unreadable-file` and the verdict `ERROR`.
- **INTERFACES-123** If the directory given with `--out` holds an entry, then the command shall report a single finding with the code `out-not-empty` and the verdict `ERROR`, before opening any adapter.
- **INTERFACES-124** If the directory given with `--out` is the project or is inside it, then the command shall report a single finding with the code `out-inside-project` and the verdict `ERROR`, since the evidence never lives inside the tree it describes.
- **INTERFACES-125** When `audit` runs, the command shall create the directory given with `--out` when it is absent, keep the ledger of the run in its `ledger.jsonl`, and write the evidence there as `<story>.statement.json`.
- **INTERFACES-126** When `audit` runs, the command shall open the git adapter on the project and the podman adapter, and audit the change over them with the version of the installed package as the version of the harness, or `unversioned` when the package is not installed, since how the harness is versioned is decided before A4, and with the digest of the program of the podman adapter that observes.
- **INTERFACES-127** If an adapter refuses to open, then the command shall report its finding, with the verdict `ERROR`.
- **INTERFACES-128** When the audit ends, the command shall write one line for each gate as `gate <name>: <status>` followed by the verdict of a gate that ran or the reason of one that did not, then each finding as `<gate>: VERDICT code: message`, with its lines in parentheses when it has any, then the line `evidence <path> <digest>` when there is evidence, and the line of the verdict last.
- **INTERFACES-129** When the option `--format json` is given to `audit`, the command shall write one JSON document with the verdict, the path and the digest of the evidence or `null`, the path of the ledger, the gates and the findings.
- **INTERFACES-130** When the audit ends, the command shall exit with the code of its verdict ([ADR-0040](../adr/0040-commands-exit-with-a-code-for-each-verdict.md)).
- **INTERFACES-131** If the harness receives SIGINT or SIGTERM while `audit` runs, then the command shall close the container of the run, the temporary directories and the adapters, from the inside out, before it ends.
