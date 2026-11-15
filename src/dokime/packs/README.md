# packs

The pack of a verified project: the data that tells the harness how to build its environment and
how to run its tests, and the self-check that proves it. It imports only `core`, and drives the
self-check over the ports of the project repository and of the verification runtime that
`interfaces` gives it.

## A pack

```yaml
format: 1
name: cachetools
environment:
  dockerfile: Dockerfile        # beside the pack
tests:
  command: [python, -m, pytest, --junitxml, /dokime/out/report.xml]
  report: report.xml            # in the output directory, in JUnit XML
  paths: ["tests/**"]           # which files of the project are tests
```

`check` reads the text of a pack with the strict reader of `core`, compares it with its table of
fields and returns every finding at once, with the pack when there is none.

```python
from dokime.packs.check import check

checked = check(text)
checked.verdict  # PASS or FAIL
checked.pack  # the pack, or None when there is a finding
```

Besides the findings of the reader and of the shape check of `core`, it reports `empty-list` for a
test command or a list of test paths without items, and `path-outside-pack`,
`path-outside-output` and `path-outside-project` for a path that is absolute or has `..`.

## The rules of the self-check

A pack proves itself with the history of its project
([ADR-0041](../../../docs/adr/0041-the-environment-of-a-verified-project-is-a-dockerfile.md)).
The rules are decisions over results that something else obtains:

- `is_candidate(pack, changed)`: a commit that changed a test and code that is not a test.
- `is_witness(parent, commit)`: a test passes on the commit and did not pass on the parent, in a
  parent report where something failed. `turned_green(parent, commit)` names those tests.
- `self_check(candidates)`: no finding with two witnesses among the first ten candidates;
  otherwise `too-few-witnesses`.

## The loop of the self-check

```python
from dokime.packs.loop import Program, run_self_check

result = run_self_check(pack, dockerfile, start, repository, runtime, programs)
result.verdict  # PASS, FAIL (too-few-witnesses) or ERROR
result.candidates  # each with its commit, its two sides and the tests that turned green
result.programs  # the git and the podman that ran, as the caller names them
```

- `order_history` orders the history by the rule of
  [ADR-0044](../../../docs/adr/0044-the-packs-module-drives-the-self-check-in-an-order-of-its-own.md)
  and leaves out the commits without exactly one parent.
- Each candidate runs on two sides: the tree of its parent with the test paths of the commit, and
  the tree of the commit. `run_tests` builds the image of a side from the Dockerfile read once
  from the working copy, with the tree as the context, runs the test command and reads the report.
  `verify` reuses it in A3.
- The second witness ends the loop, and so does a finding with the verdict `ERROR`: a refusal of
  a port, an unreadable report, or `run-killed` when the container dies at a limit.
- Each side lives in a temporary directory, removed after it runs and on SIGINT or SIGTERM.
- The self-check has no limit of time of its own; the budget of a run belongs to the flow.
