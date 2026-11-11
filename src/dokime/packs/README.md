# packs

The pack of a verified project: the data that tells the harness how to build its environment and
how to run its tests. It imports only `core`. This increment has what needs no container engine;
building the environment and running the tests come with the adapter of an engine.

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
  parent report where something failed.
- `self_check(candidates)`: no finding with two witnesses among the first ten candidates;
  otherwise `too-few-witnesses`.
