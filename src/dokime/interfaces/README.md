# interfaces

The commands a person or a pipeline runs. A command reads its input, calls the module that does
the work and shows the result; it holds no logic of its own about contracts or packs. It is also
the composition root: the only module that builds the adapters of `platform` and `sandbox`.

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

Audits a change that arrives already made. The command is built over three pull requests: its
inputs, in `inputs.py`; its run over the ports, in `audit.py`; and the command line.

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
- The ledger records `run.started`, `state.entered`, `gate.started` and `gate.finished`,
  `baseline.unstable`, `evidence.built` and `run.finished`. The evidence carries the head of the
  ledger before `evidence.built`.
- The aggregation's own findings stop the run with `ERROR`, no evidence, and a `run.finished` that
  names them. A story that is not a name, a patch that does not apply, a base that cannot be
  extracted and a policy with a finding end the audit before the run, with nothing recorded.
- `convert` turns a result of `verify` into the types of `evidence`, field by field; `CONVERTED`
  names the fields of the result that it carries, and a test fails when `verify` adds one.
