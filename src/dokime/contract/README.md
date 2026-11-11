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
| `unknown-directive`, `several-directives`, `directive-parameter`, `directive-value`, `matcher-in-input` | `FAIL` | A directive that is not in the table, or is not written as the table states |
| `duplicate-example` | `FAIL` | Two examples with the same boundary, target and steps |
| `contradictory-examples` | `FAIL` | Two examples that expect, for the same inputs, what cannot both hold |
| `requirement-without-example`, `only-model-examples` | `ASK` | A requirement that no example approved by a person supports |
| `not-supported-yet` | `ERROR` | An example at the `http` boundary, or the matcher `$ref` |

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
