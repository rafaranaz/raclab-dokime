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

A finding is one problem found by a check: a code made of lowercase words joined by hyphens, a
message, the lines of the file where it is and the verdict it gives, which is never `PASS`. A list
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
