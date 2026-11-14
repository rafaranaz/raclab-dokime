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

## The shape of what was read

A check of a file that was read (a contract, a pack, a flow) compares each of its mappings with a
table of fields: which fields the mapping may have, which are mandatory and what each holds.

- **CORE-050** If a mapping has a field that its table does not list, then the shape check shall report a finding with the code `unknown-field` that names the field, with its line.
- **CORE-051** If a mapping lacks a field that its table marks as mandatory, then the shape check shall report a finding with the code `missing-field` that names the field, with the line of the mapping.
- **CORE-052** If the value of a field is not what its table states, then the shape check shall report a finding with the code `wrong-type` that names the field, with its line.
- **CORE-053** If a field with a closed list of values has a value that is not in the list with the same type, then the shape check shall report a finding with the code `unknown-value` that lists the values allowed, with its line.
- **CORE-054** When a finding is about a part that has no line of its own, the shape check shall give the line of the nearest part that contains it.

## The port of the project repository ([ADR-0042](../adr/0042-a-port-of-the-project-repository-composes-the-trees-that-are-built.md), [ADR-0044](../adr/0044-the-packs-module-drives-the-self-check-in-an-order-of-its-own.md))

`core` defines the port and the values it exchanges; it runs no `git`. What an adapter does with a
real repository (how it composes and extracts a tree, when it refuses and with which code) is
required in the scope of the adapters, for every adapter of the project repository, where it can
be tested. The order in which the self-check takes the commits of a history belongs to `packs`.

### Names and paths

- **CORE-060** The name of a commit and the name of a tree shall accept a text of 40 lowercase hexadecimal characters.
- **CORE-061** If the name of a commit or of a tree is not 40 lowercase hexadecimal characters, then the name shall be rejected with an error that quotes the text.
- **CORE-062** The name of a commit shall not be equal to the name of a tree with the same text.
- **CORE-063** The path of the repository shall accept a relative path whose parts are separated by `/`.
- **CORE-064** If a path of the repository is empty, starts or ends with `/`, has an empty part, has a part `.` or `..`, or has a NUL character, then the path shall be rejected with an error that quotes the path.
- **CORE-065** When a path of the repository is made from the bytes that a repository stores, the path shall decode them as UTF-8.
- **CORE-066** If the bytes of a path are not valid UTF-8, then the path shall be rejected with an error that quotes the bytes.

### What the port gives and takes

- **CORE-067** The port shall offer five operations: give the history from a commit, give the change of a commit, compose a tree from a commit with paths of another commit, compose a tree from a commit with a patch, and extract a tree to a directory.
- **CORE-068** The history from a commit shall carry every commit reachable from it, each with its commit date in whole seconds and its parents in the order the commit names them.
- **CORE-069** The change of a commit shall carry the name of the commit, the name of its one parent and the paths it changed.
- **CORE-070** The composition with paths of another commit shall receive the paths to take as a rule that says, for each path of the repository, whether it is taken.
- **CORE-071** The port shall return the name of the composed tree from each composition.

### Refusals

A refusal is how an adapter says that it cannot do an operation. It is not an error of the
harness: the module that called the port adds its finding to its result, and the round ends in
`ERROR`.

- **CORE-072** When an adapter refuses an operation, the port shall raise a refusal that carries a finding with the verdict `ERROR`.
- **CORE-073** If a refusal is given a code or a message that a finding does not accept, then the refusal shall be rejected with the error of the finding.

## The outcome of a test run ([ADR-0045](../adr/0045-a-test-report-is-read-by-a-bounded-reader-that-refuses-any-dtd.md))

The adapter of the verification runtime reads the report of a run and gives these values to the
module that called it. They live in `core` because an adapter imports only `core`.

- **CORE-074** The outcome of a test shall be one of passed, failed, error and skipped.
- **CORE-075** The report of a run shall give, for the name of each test, its outcome.
- **CORE-076** The limits of reading a report shall carry the largest size of the report in bytes, the memory of the reader in bytes and the processor time of the reader in seconds.
- **CORE-077** The limits of reading a report shall default to 32 MiB for the report, 512 MiB for the memory of the reader and 10 seconds of processor time.
- **CORE-078** If a limit of reading a report is not a whole number greater than zero, then the limits shall be rejected with an error that names the limit.
