# ADR-0037 · A contract is read by strict rules of its own, and every problem is reported

**Status:** accepted

## Context

Milestone A1 validates a contract file and says what it lacks. A contract is signed by its digest,
so what the validator reads has to be what the person read. YAML does not give that by itself. A
repeated key keeps one of its values. A value without quotes changes type depending on the reader:
`no` becomes a boolean in some, `1.10` becomes the number 1.1, `010` becomes 10, `2026-11-10`
becomes a date. A text written on several lines is joined with spaces unless it is a literal
block, and whether a literal block ends in a newline depends on a hyphen (`|` or `|-`). An alias
or a merge key makes one place of the file mean what another place says.

## Decision

- **The library only parses.** A contract, and a flow file, is parsed with PyYAML into its events
  and its tree of nodes. What each node means is decided by the rules below, not by the library.
- **A plain subset.** One document. No anchors, aliases, tags or merge keys.
- **Keys.** A key is a text, compared as written. A key that repeats inside a mapping is a
  finding, and so is an `id` that repeats among the requirements, the examples or the relations.
  The finding names every line where it appears.
- **Values without quotes.** `true` and `false` are booleans, `null` is null, and a number written
  as JSON writes it is a number. A value that some YAML reader would read as another type is
  rejected, asking for quotes: `yes`, `no`, `on`, `off`, `y`, `n`, `~`, an empty value, a number
  with leading zeros, underscores, a leading `+` or a bare dot, hexadecimal and octal forms,
  infinities, dates and times. A number whose decimals end in zero, such as `1.10`, is rejected in
  the same way. Anything else is a text. A value in quotes is always a text.
- **Texts on several lines.** A scalar that takes more than one line of the file must be a
  literal block (`|`) whose value ends in exactly one newline. A folded block (`>`), a block with
  `|-`, and a plain or quoted scalar continued on the next line are rejected. So is a line of a
  literal block that ends in a space or a tab.
- **Every problem in one run.** The check reports every finding, each with a code from a closed
  list and its lines, including the findings whose verdict the aggregation drops. A check that
  needs a part that an earlier check rejected does not run on that part. A file that is not YAML,
  or that has an alias, stops the later checks.
- **Verdicts.** A file that breaks these rules gives `FAIL`. A file that cannot be opened gives
  `ERROR`.

## Basis

Verified by running code (PyYAML 6.0.3, `ruamel.yaml` 0.19.1, `strictyaml` 1.6.2) and a prototype
of the reader:

- PyYAML keeps the last of two equal keys and says nothing, and reads `on` and `no` as booleans.
- `ruamel.yaml` in YAML 1.2 keeps `no` as a text but still reads `1.10` as 1.1, `010` as 10,
  `1_000` as 1000, `2026-11-10` as a date and an empty value as null. It accepts aliases and merge
  keys, and keeps `1` and `'1'` as two different keys.
- Both libraries give, for every scalar, its style (plain, quoted, `|`, `>`) and its first and
  last line. They do not give the hyphen of `|-`, but the value shows it. A `|+` block with no
  blank lines after it gives the same value as `|`.
- The prototype, with PyYAML only as parser, reports every repeated key with all its lines, every
  rejected value and every rejected text in one run. On the three hand-written contracts of
  milestone A0 it found the seven `|-` blocks and one value nobody had noticed: a table header
  `n`.
- `strictyaml` rejects repeated keys, aliases and implicit types, and also the flow style
  (`{a: 1}`, `[1, 2]`) that every contract uses.
- The three A0 contracts, rewritten to these rules, give no finding, and all their examples still
  pass against the real code (7, 17 and 15). Four defects seeded in one of them were all caught.
- PyYAML and `ruamel.yaml` both had a release in the last fourteen months.

Read in the sources:

- The YAML 1.2.2 specification says that the keys of a mapping are unique, and that whether two
  keys are equal depends on the schema.
- The rules for values without quotes are those of the JSON schema of that specification (`null`,
  `true`, `false` and numbers as JSON writes them), with two differences: what does not match is
  a text instead of an error, and a number with a bare dot or with decimals ending in zero is
  rejected. The core schema of the specification has no dates, so `ruamel.yaml` reading
  `2026-11-10` as a date goes beyond it.
- The YAML 1.1 type list counts `y`, `n`, `yes`, `no`, `on` and `off` as booleans.

Not looked at: bindings of other parsers. Reasoning: with rules of its own the
meaning of a contract does not change if the library changes; the rule about decimals ending in
zero; reporting everything at once, which saves the person a round trip per problem. The test that
confirms the whole is the criterion of A1, a set of contracts with seeded defects where every
defect has to be reported.

## Alternatives considered

- **Trust the types of `ruamel.yaml` in YAML 1.2.** It removes the `no` trap and leaves the
  others listed above.
- **`strictyaml`.** It has the right philosophy and the wrong surface: without the flow style an
  example of three lines takes fifteen.
- **Another format, JSON or TOML.** JSON has no comments and writes a text of several lines as
  one line with escapes; TOML is awkward for lists of nested examples. Both remove the traps by
  removing what makes a contract readable. This is reasoning, not a test.
- **Stop at the first problem.** Simpler to write. Each run then reveals one problem.

## Consequences

- PyYAML becomes a runtime dependency. Only its parser is used.
- The reader lives in `core`, because `contract` and the flow loader
  ([ADR-0035](0035-the-flow-is-loaded-and-validated-in-core.md)) both use it. It receives text;
  it does not open files.
- The three contracts of A0, rewritten to these rules, become the valid test contracts of the
  validator.
- A person who wants the text `no` or `1.10` writes it in quotes, and the validator says so.
