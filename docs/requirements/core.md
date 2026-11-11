# Requirements of the `core` scope

Domain types that every module shares. This first increment holds what the contract check of
milestone A1 needs: the verdicts of a gate, the findings that explain them, and the strict reader
of contract and flow files. Each requirement follows an EARS template and has at least one test
that declares it in its `SDD-EARS:` marker.

## Verdicts ([ADR-0015](../adr/0015-a-gate-returns-one-of-four-verdicts.md))

- **CORE-001** The verdict type shall have exactly the values `PASS`, `FAIL`, `ASK` and `ERROR`.
- **CORE-002** When any verdict of a round is `ERROR`, the aggregation shall return `ERROR`.
- **CORE-003** When no verdict of a round is `ERROR` and any is `FAIL`, the aggregation shall return `FAIL`.
- **CORE-004** When no verdict of a round is `ERROR` or `FAIL` and any is `ASK`, the aggregation shall return `ASK`.
- **CORE-005** When every verdict of a round is `PASS`, the aggregation shall return `PASS`.
- **CORE-006** If a round has no verdicts, then the aggregation shall raise an error that says the round is empty.
- **CORE-007** The aggregation shall return the same verdict for any order of the same verdicts.

## Findings

A finding is one problem found by a check. Its verdict is `FAIL`, `ASK` or `ERROR`.

- **CORE-010** The finding shall carry a code, a message, a verdict and a list of lines, which may be empty.
- **CORE-011** If a finding is given the verdict `PASS`, then the finding shall be rejected with an error naming the verdict.
- **CORE-012** If a finding has an empty code or an empty message, then the finding shall be rejected with an error naming the empty field.
- **CORE-013** When a list of findings is summarised, the summary shall be the aggregation of their verdicts.
- **CORE-014** When a list of findings is empty, the summary shall be `PASS`.
- **CORE-015** If a finding code is not made of lowercase words joined by hyphens, then the finding shall be rejected with an error naming the code.
- **CORE-016** If a finding has a line smaller than 1, then the finding shall be rejected with an error naming the line.

## Strict reading ([ADR-0037](../adr/0037-a-contract-is-read-by-strict-rules-of-its-own.md))

The reader receives the text of a contract or of a flow file. It does not open files. The library
only parses; the rules below decide what the text means. Every finding of the reader has one of
the codes named here.

- **CORE-020** When a text is read, the reader shall return the value the text holds together with every finding of the text.
- **CORE-021** The reader shall give the verdict `FAIL` to every finding it reports.
- **CORE-022** If a text is not YAML, then the reader shall return no value and a single finding with the code `not-yaml` and the line of the error.
- **CORE-023** If a text does not hold exactly one document, then the reader shall return no value and a finding with the code `not-one-document`.
- **CORE-024** If a text has an anchor or an alias, then the reader shall return no value and a finding with the code `anchor-or-alias` for each of them, with its line.
- **CORE-025** If a node has an explicit tag, then the reader shall report a finding with the code `tag` and the line of the node.
- **CORE-026** If a mapping has the key `<<` without quotes, then the reader shall report a finding with the code `merge-key` and the line of the key.
- **CORE-027** If a key is a sequence or a mapping, then the reader shall report a finding with the code `key-not-text` and the line of the key.
- **CORE-028** The reader shall read every key as a text, as it is written.
- **CORE-029** If a key appears more than once in a mapping, then the reader shall report one finding with the code `duplicate-key` that names the key and lists every line where it appears.
- **CORE-030** When a value without quotes is `true` or `false`, the reader shall read it as a boolean.
- **CORE-031** When a value without quotes is `null`, the reader shall read it as null.
- **CORE-032** When a value without quotes is a number in the form JSON writes it, the reader shall read it as a number.
- **CORE-033** If a value without quotes has one of the forms of the table of ambiguous values, then the reader shall report a finding with the code `ambiguous-value` and the line of the value.
- **CORE-034** If a number without quotes has two or more decimals and the last one is zero, then the reader shall report a finding with the code `ambiguous-value` and the line of the value.
- **CORE-035** When a value without quotes has none of the forms above, the reader shall read it as a text.
- **CORE-036** When a value is in quotes, the reader shall read it as a text.
- **CORE-037** If a scalar is a folded block or continues on another line without being a literal block, then the reader shall report a finding with the code `text-on-several-lines` and the line where the scalar starts.
- **CORE-038** If the value of a literal block does not end in exactly one newline, then the reader shall report a finding with the code `block-ending` and the line where the block starts.
- **CORE-039** If a line of a literal block ends in a space or a tab, then the reader shall report a finding with the code `trailing-whitespace` and that line.

- **CORE-040** When a text is read, the reader shall give the line where every key of a mapping and every item of a sequence starts, addressed by its path from the root.
- **CORE-041** If a key appears more than once in a mapping, then the reader shall give for its path the line of the occurrence whose value it keeps.

- **CORE-042** When a text is read, the reader shall give the paths of the values that are written as literal blocks.

### Table of ambiguous values

A value without quotes in one of these forms is read with different types by different YAML
readers, so the reader rejects it and asks for quotes.

| Form | Examples |
|---|---|
| Words that some readers read as booleans or null, in any case | `yes`, `no`, `on`, `off`, `y`, `n`, `True`, `FALSE`, `Null`, `~` |
| An empty value | `key:` |
| A number with leading zeros | `010`, `-007` |
| Hexadecimal, octal and binary forms | `0x10`, `0o10`, `0b10` |
| Digits with underscores | `1_000` |
| A number with a leading `+` or a bare dot | `+1`, `.5`, `1.` |
| Infinities and not-a-number | `.inf`, `-.inf`, `.nan` |
| Dates and times | `2026-11-10`, `2026-11-10T10:00:00Z`, `12:30` |
