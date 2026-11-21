# contract

The check of a contract and the meaning of what its examples expect. It imports only `core`, and it
runs nothing: it reads a text and says what it found.

## Checking a contract

`check` takes the text of a contract and returns every finding at once, in the order of the lines,
together with the contract when it can be used.

```python
from dokime.contract.check import check

checked = check(text)
checked.verdict  # PASS, ASK, FAIL or ERROR
[(finding.code, finding.lines) for finding in checked.findings]
checked.contract  # the contract, or None when a finding has the verdict FAIL or ERROR
```

The text is read with the strict reader of `core`, whose findings are reported too. The fields of
each part of a contract and the directives are listed in the
[requirements](../../../docs/requirements/contract.md); the decisions behind them are in
[ADR-0038](../../../docs/adr/0038-directives-in-a-contract-are-marked-with-a-dollar.md) and
[ADR-0039](../../../docs/adr/0039-what-a-contract-of-the-first-version-may-say.md).

| Code | Verdict | What it reports |
|---|---|---|
| `wrong-type`, `unknown-field`, `missing-field`, `unknown-value`, `empty-list` | `FAIL` | A part of the contract that does not have the shape of its table of fields |
| `duplicate-id` | `FAIL` | An id that appears more than once among the requirements, the examples or the relations |
| `block-outside-text` | `FAIL` | A literal block that is not the value of `$text` |
| `not-ears` | `FAIL` | A requirement whose text is not in one of the five EARS templates, or has `shall` twice |
| `replaces-without-change` | `FAIL` | `replaces` in a requirement whose kind is not `change` |
| `unknown-requirement` | `FAIL` | An example or a relation that names a requirement the contract does not have |
| `two-expectations`, `no-expectation` | `FAIL` | A step that expects `returns` and `raises`, or nothing |
| `path-outside-directory` | `FAIL` | A file of a command, given or expected, named outside its working directory: empty, absolute or with `..` |
| `unknown-directive`, `several-directives`, `directive-parameter`, `directive-value`, `matcher-in-input` | `FAIL` | A directive that is not in the table, or is not written as the table states |
| `duplicate-example` | `FAIL` | Two examples with the same boundary, target and steps |
| `contradictory-examples` | `FAIL` | Two examples that expect, for the same inputs, what cannot both hold |
| `relation-target-ambiguous`, `relation-needs-via`, `relation-via-not-allowed`, `relation-needs-over`, `bad-over` | `FAIL` | A relation whose channel is not declared where it has to be, is declared where it is not allowed, or names no input of its examples (ADR-0076) |
| `requirement-without-example`, `only-model-examples` | `ASK` | A requirement that no example approved by a person supports |
| `relation-without-example` | `ASK` | A relation whose target no visible example of its requirement has, so that nothing tells its boundary nor feeds it |
| `not-supported-yet` | `ERROR` | An example at the `http` boundary, or the matcher `$ref` |

The channel of a relation is checked against the visible examples of its requirement at its target,
whose boundary is its own: `idempotent` at `cli` says `via`, `stdout` or `files`; at `function`, a
relation names with `over` the argument it works on, `args[N]` or a keyword argument that an
example gives, and `idempotent` needs it when an example gives more than one argument; at `cli`,
`order-insensitive` names `stdin` or a file of the input. While an example does not read or names
an unknown requirement, the channels are not checked, so that a relation does not lose a source it
has.

An example with a finding of its own is left out of the search for duplicates and contradictions.
Two matchers for the same field are not compared with each other.

## When an expectation holds

`holds` says whether what an example expects holds for what was observed. An exact value holds
only for an equal value of the same type; the matchers are `Contains`, `FullMatch`, `Approx`,
`Unordered`, `AnyValue` and `Json`.

```python
from dokime.contract.expectations import Approx, holds

holds(
    {"total": Approx(10.03, 0.005), "currency": "EUR"}, {"total": 10.031, "currency": "EUR"}
)  # True
holds(1, 1.0)  # False: an exact value has its type
```

## Held-out examples

After the split (ADR-0014), a contract keeps its visible examples in `examples` and, in `held_out`,
only the id, the requirement, the case and the digest of each held-out example; the salt and the
text are in the sealed batch.

```yaml
held_out:
  - id: E-7c21
    requirement: round-total-once
    case: normal
    digest: sha256:4f0d…
```

`check` returns them in `contract.held_out`. An id that is both in `examples` and in `held_out` is
`held-out-in-clear`, an `ERROR`: that example is in the file in clear, and has to be replaced and
sealed again.

```python
from dokime.contract.held_out import example_texts, held_out_digest

texts = example_texts(text)  # the block of each example, by its id, as written
held_out_digest(salt, texts["E-7c21"])  # salt of 16 bytes; "sha256:" and the SHA-256 of
# the canonical form of {"salt": salt in hexadecimal, "text": the text}
```

The text of an example reads back the same alone as inside its contract, since the strict reader
refuses anchors, aliases, tags and merge keys.
