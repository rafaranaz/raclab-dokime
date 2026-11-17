# core

Domain types that every other module shares. `core` imports no other module of the package and
does no input or output.

## Verdicts

A gate returns one of four verdicts, and a round of gates aggregates them by precedence: `ERROR`,
then `FAIL`, then `ASK`, else `PASS`. A round without verdicts is an error, so that nothing passes
because no gate ran.

```python
from dokime.core.verdicts import Verdict, aggregate

aggregate([Verdict.PASS, Verdict.ASK, Verdict.FAIL])  # Verdict.FAIL
```

## Findings

A finding is one problem found by a check: a code made of words of lowercase letters and digits
joined by hyphens, starting with a letter, a message, the lines of the file where it is and the verdict it gives, which is never `PASS`. A list
of findings summarises to the aggregation of their verdicts, and to `PASS` when it is empty.

```python
from dokime.core.findings import Finding, summarise

found = Finding(
    code="duplicate-key", message="the key 'id' appears 2 times", verdict=Verdict.FAIL, lines=(3, 7)
)
summarise([found])  # Verdict.FAIL
summarise([])  # Verdict.PASS
```

## Strict reading

`read` takes the text of a contract or of a flow file and returns its value together with every
finding, in the order of their lines. It does not open files. The rules are those of
[ADR-0037](../../../docs/adr/0037-a-contract-is-read-by-strict-rules-of-its-own.md): the library
only parses, and the reader decides what the text means.

```python
from dokime.core.reading import read

reading = read("id: a\nid: b\nflag: no\n")
reading.value  # {"id": "b", "flag": "no"}
[(f.code, f.lines) for f in reading.findings]
# [("duplicate-key", (1, 2)), ("ambiguous-value", (3,))]
```

`reading.lines` gives the line where each key of a mapping and each item of a sequence starts,
addressed by its path from the root, so that a later check can say where a problem is:

```python
reading.lines[("id",)]  # 2, the occurrence whose value is kept
```

`reading.blocks` holds the paths of the values written as literal blocks (`|`), which a quoted
text with the same content is not.

The value is `None` when the text is not YAML, does not hold exactly one document or has an anchor
or an alias. Every finding of the reader has the verdict `FAIL`.

| Code | What it reports |
|---|---|
| `not-yaml` | The text cannot be parsed |
| `not-one-document` | The text holds no document, or more than one |
| `anchor-or-alias` | An anchor (`&name`) or an alias (`*name`) |
| `tag` | An explicit tag, such as `!!str` |
| `merge-key` | The key `<<` without quotes |
| `key-not-text` | A key that is a sequence or a mapping |
| `duplicate-key` | A key that appears more than once in a mapping, with every line |
| `ambiguous-value` | A value without quotes that YAML readers type differently, or a number that would lose its last zero |
| `text-on-several-lines` | A folded block, or a scalar that continues on another line |
| `block-ending` | A literal block that does not end in exactly one newline |
| `trailing-whitespace` | A line of a literal block that ends in a space or a tab |

## The shape of what was read

`check_fields` compares a mapping that was read with a table of fields and notes what does not
fit: `unknown-field`, `missing-field`, `wrong-type` and `unknown-value`. `Notes` collects the
findings of a check and turns the path of a part into its line. The checks of a contract and of a
pack are built on them.

```python
from dokime.core.reading import read
from dokime.core.shape import Field, Notes, check_fields, one_of

table = {"name": Field("a text", lambda value: isinstance(value, str)), "level": one_of("P1", "P2")}
reading = read("name: cachetools\nlevel: P9\n")
notes = Notes(reading)
check_fields(notes, reading.value, (), table)
[(finding.code, finding.lines) for finding in notes.findings]  # [("unknown-value", (2,))]
```


## The port of the project repository

`ProjectRepository` is the port of
[ADR-0042](../../../docs/adr/0042-a-port-of-the-project-repository-composes-the-trees-that-are-built.md):
give the history from a commit, give the change of a commit, compose a tree from a commit with
paths of another commit or with a patch, and extract a tree. `core` defines it and the values it
exchanges and runs no `git`. Commit and tree names are 40 lowercase hexadecimal characters and
never equal each other; a path of the repository is relative and is decoded from its bytes as
UTF-8. An adapter that cannot do an operation raises `RefusalError`, which carries a finding with
the verdict `ERROR` for the module that called the port to add to its result.

```python
from dokime.core.repository import CommitName, RefusalError, RepoPath

CommitName("0123456789abcdef0123456789abcdef01234567")
RepoPath.from_bytes(b"src/a.py")  # RepoPath(text="src/a.py")
RefusalError("shallow-clone", "the repository is a shallow clone").finding.verdict  # Verdict.ERROR
```

The port of the audited repository, `AuditedRepository`, extends it with
`compose_tree_with_paths(tree, source, take)`: a tree, such as the base with the patch applied,
with the paths of a commit that the rule takes (ADR-0058). Only what audits a change needs it, so
the self-check of a pack and its doubles keep the port of the project repository.

## The outcome of a test run

`Outcome` is what happened to one test in one run: passed, failed, error or skipped. A `Report`
gives the outcome of each test by its name. `ReportLimits` holds how much the reader of a report
may take, as [ADR-0045](../../../docs/adr/0045-a-test-report-is-read-by-a-bounded-reader-that-refuses-any-dtd.md)
says: 32 MiB for the report, 512 MiB of memory and 10 seconds of processor time unless the caller
passes others.

```python
from dokime.core.outcomes import Outcome, ReportLimits

report = {"tests.test_a::test_one": Outcome.PASSED}
ReportLimits().report_bytes  # 33554432
```

## The port of the verification runtime

`VerificationRuntime` builds an image from a Dockerfile, runs a command in it and reads the report
the run wrote. A build gives the digest of the image and the base image of its final stage, by the
digest of the manifest of its platform, or no base when that stage starts from `scratch`. A run
gives how it ended (`exited` with its exit code, `time-limit`, `memory-limit` or `killed`) and
decides no verdict. `BuildLimits` (30 minutes) and `RunLimits` (2 GiB, 2 processors, 512 processes,
15 minutes) are passed by the caller; a pack cannot change them.

```python
from dokime.core.runtime import Ending, RunLimits, RunResult

RunLimits(processors=0.5).memory_bytes  # 2147483648
RunResult(ending=Ending.TIME_LIMIT, exit_code=None)
```

## The canonical form

The digests of the ledger, the policy and the contract are taken over one canonical form: the JSON
text of RFC 8785 restricted to texts, whole numbers within ±(2^53 − 1), booleans, null, lists and
mappings with text keys (ADR-0062). The keys are ordered by their UTF-16 code units, which differs
from the order of Python for characters outside the basic plane. A decimal, a larger number, a
lone surrogate or any other value is refused with `NotCanonicalError`, naming where it is.

```python
from dokime.core.canonical import canonical, digest

canonical({"b": [1, None], "a": "é"})  # '{"a":"é","b":[1,null]}'
digest({"a": 1})  # 'sha256:…', the SHA-256 of the canonical form in UTF-8
```

## The policy

`read_policy` reads the text of `.dokime/policy.yaml` by the strict rules and its table of fields
(ADR-0054); it does not open the file. A field left out takes its default, and fewer than two runs
is refused. Without a file, the policy is `DEFAULTS`. Either way `from_file` says where it came
from, and its digest is taken over a normalised form with the format and every field, so a file
that only states the defaults has their digest.

```python
from dokime.core.policy import DEFAULTS, read_policy

read = read_policy("format: 1\nbaseline:\n  runs: 3\n")
read.policy.baseline_runs, read.policy.verification_runs  # 3, 2
read.policy.digest() == DEFAULTS.digest()  # False: the baseline runs three times
```

## The ledger

A run appends its events to a ledger through the port `LedgerStore`, stamped by the port `Clock`
(ADR-0023, ADR-0062). Each event has `seq` from 1, `at` in UTC to the second, its `type` from a
closed table, `prev`, the hash of the event before it or null for the first, and `hash`, the
digest of the event without it. Each line is exactly the canonical form of its event with its
hash. `verify` refuses any other encoding, a hash that is not the digest, a broken chain and a
sequence out of order, with a finding for each line. A ledger opened on a store that already
holds events verifies them and continues their chain.

```python
from dokime.core.ledger import Ledger, verify

ledger = Ledger(store, clock)  # store and clock are adapters of the ports
ledger.record("gate.finished", {"gate": "baseline", "verdict": "PASS"})
verify(store.lines())  # () when every line is an event in canonical form, chained
```

The chain does not show that its last events were removed, nor that the whole ledger was written
again: every line still verifies. That is covered by the head, the hash of the last event and the
number of events, which the evidence keeps. `head` gives it for a ledger that verifies, and
`verify` with an expected head reports `wrong-head` when they differ.

```python
from dokime.core.ledger import head, verify

kept = head(store.lines())  # Head(hash='sha256:…', events=3)
verify(store.lines()[:2], kept)  # one finding, wrong-head
```

## The layout of a project

`dokime.core.layout` gives the paths of the files of the harness, relative to the root of the
project: `POLICY` is `.dokime/policy.yaml`, `change_directory(story)` is
`.dokime/changes/<story>/` and `contract_path(story)` is `contract.yaml` in it. A story that is not
a name, the rule of the `story` of a contract, is refused, so no path leaves the directory of the
changes.

## The port that observes the examples

`ExampleObserver.observe(image, project, requests, limits)` runs examples in the zone of
verification and gives what it saw (ADR-0012, ADR-0063). A request carries the identifier of its
example, its boundary (`function` or `cli`), its target and the inputs of its steps, and nothing of
what is expected; the harness compares outside the zone. A step at `function` is `Returned` (any
value that JSON holds, decimals included), `Raised` (the name of the class, its full name, the full names of the classes of its MRO, as `classes`, and the message) or `NotJson` (the
name of the type of a value that JSON cannot hold); a step at `cli` is `Exited`, with its exit code,
its output, its error and the files it wrote. An example says how it ended, `completed`, `time-limit` or
`crashed` with the signal or the exit code of its process when known, with the steps observed. `ObservationLimits` bounds one example to 60 seconds and the
observations to 32 MiB by default, with the limits of a run for the whole.
