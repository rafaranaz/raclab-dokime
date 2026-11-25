# interfaces

The commands a person or a pipeline runs. A command reads its input, calls the module that does
the work and shows the result; it holds no logic of its own about contracts or packs. It is also
the composition root: the only module that builds the adapters of `platform` and `sandbox`.

## `--version`

Prints the version of the installed harness, the same one the evidence records, and exits with 0.

```console
$ python -m dokime.interfaces --version
dokime 0.0.0
```

When the harness is not installed as a distribution it prints `dokime unversioned`.

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

## `contract seal`

Splits an approved contract and seals its held-out examples (ADR-0014, ADR-0072, ADR-0073), in the
clean checkout of the project where the pull request of the contract is made.

```console
$ python -m dokime.interfaces contract seal --story add-one \
    --contract ~/approved/add-one.yaml --out ~/runs/seal-add-one
the batch will be sealed for these recipients of HEAD:
  age1…
seal? [y/N] y
kept visible, already published: E-a1
no held-out example in R-add/c2: single-example
PASS: 2 held-out examples sealed for 1 recipients
```

- **The contract** with all its examples comes from outside the tree, where the agent that works
  in the checkout cannot read it; a contract or `--out` inside the tree is `inside-the-tree`. The
  directory of the change receives only the contract with its visible examples and its list
  `held_out`, and `sealed.age`: the held-out examples are never written into the tree.
- **The base** is `HEAD` of the clean checkout (`not-a-clean-checkout` otherwise). The recipients
  are those of `.dokime/recipients.txt` at that commit, shown and confirmed with `y` on the
  terminal, or through the descriptor `--recipients-confirmed-by-fd N`; without both,
  `no-confirmation-source`.
- **An example already published**, in a version of the contract in the history of `HEAD` by its
  id or by its boundary, target and steps, as `published` of `verify` tells it, the function that
  the gate of the sealed examples uses, is kept visible, whatever the seed. The seed, the salts
  and the canary come from the randomness of the system. A contract whose split holds out nothing
  is `nothing-to-hold-out`.
- **The ledger** of the run, in `--out/ledger.jsonl`, records its start with the story and the
  base, the question and the answer of the confirmation, and its end with the digests of the seed
  and of the batch.
- **The contract written** has to keep visible exactly the examples of the split and hold out
  exactly those sealed, or nothing is written (`split-not-written`).
- **Limits, not guarantees.** The command can be run again, each run drawing a new seed, so whoever
  seals can repeat it until the split suits, with no trace, since the ledger is local; the
  maintainer accepts it because the hold-out protects from the agent, and whoever seals already
  knows every example. An example is recognised as published by its id or by its boundary, target
  and steps as YAML reads them: one published with a field added or a space changed in a value is
  not recognised, as the history under an earlier path is not read.

## `env check`

Self-checks a pack on the history of its project, with the git adapter and the podman adapter.

```console
$ python -m dokime.interfaces env check --from 1ce79ef... --project ../cachetools
program git /usr/bin/git 2.47.3
program podman /usr/bin/podman 5.4.2
candidate 4b1e...: witness: tests.test_keys::test_typed_key
candidate 9c02...: not a witness
candidate 77d3...: witness: tests.test_ttl::test_expire
PASS: no findings
```

- The pack is `.dokime/pack.yaml` of the project unless `--pack` names another file. Its
  Dockerfile is read from the directory of the pack, once.
- `--from` takes the full name of a commit, 40 lowercase hexadecimal characters; any other text is
  `not-a-commit-name`. A full name that is not a commit of the project is `unknown-commit`, from
  the git adapter.
- The lines of the programs are written before the self-check starts, and the line of each
  candidate as soon as it has been looked at. The findings come at the end, with the verdict on
  the last line; `--format json` gives one document with the trees, images and bases of each side
  as well.
- The exit code is that of the verdict, as for `contract check`.
- SIGINT and SIGTERM close every layer, from the inside out: the container of the run, the
  directories of the side, then the adapters. No container and no temporary directory is left,
  except the working container of a build that was interrupted, a known limit of `podman build`.

## `audit`

Audits a change that arrives already made: its inputs are in `inputs.py`, its run over the ports in
`audit.py`, and the command line in `audit_command.py`.

```console
$ python -m dokime.interfaces audit --project ../semver --base 1ce79ef... --patch change.patch \
    --story replace-keeps-the-constructor-error --out ../runs/replace
program git /usr/bin/git 2.47.3
program podman /usr/bin/podman 5.4.2
gate contract: run PASS
gate environment: run PASS
gate baseline: run PASS
gate protected-paths: run PASS
gate existing-tests: run PASS
gate visible-examples: run PASS
gate relations: not-applicable: the gate is built in block B
...
evidence ../runs/replace/replace-keeps-the-constructor-error.statement.json sha256:...
PASS: no findings
```

- `--base` is the full name of a commit and `--patch` the file of the patch; exactly one of
  `--story` and `--contract` is given; `--pack` takes the pack from outside the patch.
- `--out` is a directory that is empty, or absent, and outside the project (`out-not-empty`,
  `out-inside-project`); it gets the ledger of the run, `ledger.jsonl`, and the evidence,
  `<story>.statement.json`.
- Each finding is written as `<gate>: VERDICT code: message`, with its lines in parentheses; a
  finding that ended the audit outside a gate is written under `audit`. `--format json` gives one
  document with the verdict, the evidence, the ledger, the gates and the findings. The exit code is
  that of the verdict, as for `contract check`.
- The version of the harness in the evidence is that of the installed package, or `unversioned`
  when it is not installed, and its commit is the one `platform` gives for the checkout of the
  package, asked once the git adapter has checked its version and before anything is written. The
  output says both, as `harness <version> <commit>` or `harness <version> without a commit`, and
  `harness <version> commit not asked` when the audit ended before the git adapter opened; the JSON
  document says it in `commit_asked`.
- `--summary FILE` appends the summary of the job to the file, in Markdown, as
  `$GITHUB_STEP_SUMMARY` expects (ADR-0070): the verdict, the story, the digest of the contract, the
  version and the commit of the harness, the digest of the evidence, and a table with each gate,
  its status, its verdict and the codes of its findings; when there is no evidence, the codes of
  the findings that ended the audit. It writes only names, statuses, verdicts, codes, versions and
  digests that match their patterns, never a message or a reason, which may quote the code of the
  change. A file that cannot be written ends the command with the code of `ERROR`.
- SIGINT and SIGTERM close every layer, from the inside out, as for `env check`.

- The contract comes from `.dokime/changes/<story>/contract.yaml` of the tree of the base commit,
  or from the file given with `--contract`, never from the patch. Its `story` has to be the name of
  the directory that holds it (`story-not-directory`), and a story that is not a name is
  `not-a-story`.
- The pack comes from `.dokime/pack.yaml` of the tree of the base, with its Dockerfile beside it,
  or from the file given with `--pack`, never from the patch: the pack says what is protected, and
  a patch that changed it could unprotect its own tests.
- The policy comes from `.dokime/policy.yaml` of the tree of the base, or its defaults when the
  file is absent.
- A file of the extracted tree is opened part by part without following a link, and is at most
  1 MiB: `file-not-regular` for a link or anything that is not a regular file, `file-missing`,
  `file-too-large`, and `path-outside-tree` for a path that leaves the tree. A file given from
  outside is the person's, and is read as it is.

`run_audit(request, ports, store, clock)` runs an audit over the ports it is given and records it in
the ledger store:

- It goes through the states of the audit flow of A3 (`STATES`): `checking-contract`,
  `preparing`, `baselining`, `verifying` and `sealed`. Their gates, joined, are `AUDIT_GATES` of
  `evidence`. It stops at the first state whose verdict is not `PASS`, and lists every gate after
  it as not reached, or as not applicable when this version does not build it.
- The gate `contract` has the findings of the contract read. The gate `environment` has those of
  the pack, and builds the image with the Dockerfile read from the base, copied out of the tree,
  and the tree of the base as the context. The gates of `verify` run with the contract, the pack
  and the policy. The examples of each side are observed in an image built with that side as the
  context: `baseline` in the image of the environment, `visible-examples` in one built with the
  tree of the change of ADR-0058, whose digest goes in its `gate.finished`. So a pack that
  installs the project observes the code and the dependencies of the patch.
- When the gate `repeatability` is built, the other gates of `verifying` run as many times as
  `verification.runs` of the policy says, each `gate.started` and `gate.finished` with the number
  of its run. Each gate enters the aggregation with the result of its worst run, by the precedence
  of ADR-0015, the first on a tie, together with `repeatability` over every run, so the verdict does
  not depend on the order of the runs; the evidence gets `repeated` only then. The image of the
  change is built once for the audit, and goes to the evidence as `inputs.change_image`.
- The ledger records `run.started`, `state.entered`, `gate.started` and `gate.finished`,
  `baseline.unstable`, `evidence.built` and `run.finished`. The evidence carries the head of the
  ledger before `evidence.built`.
- The aggregation's own findings stop the run with `ERROR`, no evidence, and a `run.finished` that
  names them. A story that is not a name, a patch that does not apply, a base that cannot be
  extracted and a policy with a finding end the audit before the run, with nothing recorded.
- `convert` turns a result of `verify` into the types of `evidence`, field by field; `CONVERTED`
  names the fields of the result that it carries, and a test fails when `verify` adds one.

### The gate of the sealed examples in `audit`

`--identity PATH` names the key, which has to exist outside the tree of the project
(`inside-the-tree`, `no-identity`); without it, the identity of its default path is the key when a
file is there, and otherwise the key is not here, as in CI. The entries `held_out` of the contract
of the story and `sealed.age` are read from the tree of the base, and `applicability` of `verify`
decides before anything is opened: a batch without entries, or entries without a batch, is an
`ERROR` with or without the key; neither makes the gate not applicable with `the contract holds out
no example`; without the key it is not applicable with `the key is not here`. Only when the gate
runs is the passphrase asked, once, from `--passphrase-fd N` or the terminal; the batch is opened
in memory and the gate runs on the change, and when it observed, the evidence gets the hold-out of
ADR-0075. With `--contract`, the entries `held_out` of the contract given have to be those of the
base: a whole contract that was sealed, without them, is a `sealed-batch-mismatch` that says a
local audit is made with the visible contract. The gate runs once `verify` lists it in `BUILT`.

When the run opened the batch, it gives the command its sentinel, the impossible value of the
canary (`Audited.sentinel`). Before it writes the evidence, the command looks for it in every path,
file and link, never followed, of `--out`, where the ledger is, and in the bytes of the evidence.
Found, the audit ends in `ERROR` with `sentinel-in-out` under `audit`, whose message says where and
not the value, and no evidence is written: that output holds held-out content in clear, whether
from the agent or from the harness (INV-3). The ledger was already written, and keeps its
`evidence.built` and its `run.finished`; the missing evidence and the exit code say that the run is
not taken as good.

### The gate of the relations in `audit`

The command draws the seed of the relations of each audit from the randomness of the system, and
the run records it in the event `gate.started` of the gate `relations`. The gate runs in the state
`verifying`, on the image of the change, with that seed and `relations.permutations` of the
policy, as many times as the verification runs; the evidence gets the record of the run whose
result it lists, the seed and each follow-up that did not hold with its order. A refused build of
the image of the change is an `ERROR` of the gate and nothing else. The gate runs once `verify`
lists it in `BUILT`.
