# Requirements of the `contract` scope

The check of a contract: it reads the text with the strict reader of `core`, validates its shape,
its requirements, its examples and its relations, and says what the contract lacks. It runs
nothing. Each requirement follows an EARS template and has at least one test that declares it in
its `SDD-EARS:` marker.

The decisions behind these requirements are in ADR-0037 (strict reading), ADR-0038 (directives) and
ADR-0039 (what a contract of the first version may say).

## The result of a check

- **CONTRACT-001** When a contract is checked, the checker shall report every finding of the strict reader.
- **CONTRACT-002** If the strict reader gives no value, then the checker shall report the findings of the reader and no other.
- **CONTRACT-003** The checker shall report every finding of a contract in one result, in the order of their lines.
- **CONTRACT-004** The checker shall give the verdict `FAIL` to every finding for which these requirements name no other verdict.
- **CONTRACT-005** When a contract has no finding with the verdict `FAIL` or `ERROR`, the checker shall return the contract with its requirements, its examples and its relations.
- **CONTRACT-006** If a contract has a finding with the verdict `FAIL` or `ERROR`, then the checker shall return no contract.

## Shape

The tables of fields below say, for each mapping of a contract, which fields it may have, which
are mandatory and what each holds.

- **CONTRACT-010** If the contract is not a mapping, then the checker shall report a finding with the code `wrong-type` and run no other check.
- **CONTRACT-011** If a mapping has a field that the table of fields does not list for it, then the checker shall report a finding with the code `unknown-field` that names the field, with its line.
- **CONTRACT-012** If a mapping lacks a field that the table of fields marks as mandatory, then the checker shall report a finding with the code `missing-field` that names the field, with the line of the mapping.
- **CONTRACT-013** If the value of a field is not what the table of fields states, then the checker shall report a finding with the code `wrong-type` that names the field, with its line.
- **CONTRACT-014** If a field with a closed list of values has another value, then the checker shall report a finding with the code `unknown-value` that lists the values allowed, with its line.
- **CONTRACT-015** If a list that the table of fields marks as not empty has no item, then the checker shall report a finding with the code `empty-list`, with its line.
- **CONTRACT-016** If an id appears more than once among the requirements, among the examples or among the relations, then the checker shall report one finding with the code `duplicate-id` that lists every line where it appears.
- **CONTRACT-017** If a literal block is not the value of the directive `$text`, then the checker shall report a finding with the code `block-outside-text`, with its line.

## Requirements

- **CONTRACT-020** If the text of a requirement matches none of the five EARS templates, then the checker shall report a finding with the code `not-ears` that names the requirement, with the line of the text.
- **CONTRACT-021** If the text of a requirement has the word `shall` more than once, then the checker shall report a finding with the code `not-ears` that names the requirement, with the line of the text.
- **CONTRACT-022** If a requirement has the field `replaces` and its kind is not `change`, then the checker shall report a finding with the code `replaces-without-change`, with the line of the field.

## Examples

- **CONTRACT-030** If an example or a relation names a requirement that the contract does not have, then the checker shall report a finding with the code `unknown-requirement`, with its line.
- **CONTRACT-031** If the boundary of an example is `http`, then the checker shall report a finding with the code `not-supported-yet` and the verdict `ERROR`, with its line.
- **CONTRACT-032** If a step at the `function` boundary expects both `returns` and `raises`, then the checker shall report a finding with the code `two-expectations`, with the line of the expectation.
- **CONTRACT-033** If a step expects nothing, then the checker shall report a finding with the code `no-expectation`, with the line of the expectation.

## Directives

A mapping inside an input or an expectation that has a key starting with `$` is a directive. The
table of directives below says what each one holds and where it may appear.

- **CONTRACT-040** If a directive is not in the table of directives, then the checker shall report a finding with the code `unknown-directive` that names it, with its line.
- **CONTRACT-041** If a mapping has more than one key that starts with `$`, then the checker shall report a finding with the code `several-directives`, with its line.
- **CONTRACT-042** If a directive has a parameter that the table of directives does not list for it, then the checker shall report a finding with the code `directive-parameter` that names the parameter, with its line.
- **CONTRACT-043** If a directive lacks a parameter that the table of directives marks as mandatory, then the checker shall report a finding with the code `directive-parameter` that names the parameter, with its line.
- **CONTRACT-044** If the value of a directive is not what the table of directives states, then the checker shall report a finding with the code `directive-value`, with its line.
- **CONTRACT-045** If a matcher appears in an input, then the checker shall report a finding with the code `matcher-in-input`, with its line.
- **CONTRACT-046** If the matcher `$ref` appears, then the checker shall report a finding with the code `not-supported-yet` and the verdict `ERROR`, with its line.
- **CONTRACT-047** When a `$text` has `final_newline: false`, the checker shall give its text without the newline that ends the block.
- **CONTRACT-048** When a `$text` has `final_newline: true`, the checker shall give its text as the block holds it.
- **CONTRACT-049** When a value is under `$literal`, the checker shall give it as it is written, without reading the directives inside it.
- **CONTRACT-050** When a `$json` is in an input, the checker shall give the text of its value written as JSON.

## When an expectation holds

The meaning of an expectation lives here, because the check for contradictions needs it and the
comparison with what is observed uses the same rules.

- **CONTRACT-060** When an expectation is an exact value, the expectation shall hold for an observed value of the same type that is equal to it.
- **CONTRACT-061** When an expectation is a mapping that is not a directive, the expectation shall hold for an observed mapping with the same keys whose values hold one by one.
- **CONTRACT-062** When an expectation is a list, the expectation shall hold for an observed list of the same length whose items hold one by one.
- **CONTRACT-063** When an expectation is `$contains`, the expectation shall hold for an observed text that contains its text.
- **CONTRACT-064** When an expectation is `$fullmatch`, the expectation shall hold for an observed text that its regular expression matches from the first character to the last.
- **CONTRACT-065** When an expectation is `$approx`, the expectation shall hold for an observed number that differs from its number by no more than its `tolerance`.
- **CONTRACT-066** When an expectation is `$unordered`, the expectation shall hold for an observed list whose items can be paired one to one with its items so that each pair holds.
- **CONTRACT-067** When an expectation is `$any: uuid`, the expectation shall hold for an observed text that is a UUID.
- **CONTRACT-068** When an expectation is `$any: timestamp`, the expectation shall hold for an observed text that is a date and a time in ISO 8601.
- **CONTRACT-069** When an expectation is `$json`, the expectation shall hold for an observed text that is JSON whose value satisfies the expectation inside it.

## Coverage

- **CONTRACT-070** If a requirement has no example, then the checker shall report a finding with the code `requirement-without-example` and the verdict `ASK`, with the line of the requirement.
- **CONTRACT-071** If a requirement has examples and all of them have the origin `model`, then the checker shall report a finding with the code `only-model-examples` and the verdict `ASK`, with the line of the requirement.

## Duplicates and contradictions

Two examples are compared when they have the same boundary and the same target. Their steps are
compared from the first one, as long as the inputs are the same.

- **CONTRACT-080** If two examples have the same boundary, the same target and the same steps, then the checker shall report a finding with the code `duplicate-example` that names both, with the lines of both.
- **CONTRACT-081** If two compared examples expect, at a step with the same inputs from the start, two different exact values for the same field, then the checker shall report a finding with the code `contradictory-examples` that names both, with the lines of both.
- **CONTRACT-082** If two compared examples expect, at a step with the same inputs from the start, an exact value and a matcher that the value does not satisfy, then the checker shall report a finding with the code `contradictory-examples` that names both, with the lines of both.
- **CONTRACT-083** If two compared examples expect, at a step with the same inputs from the start, one `returns` and the other `raises`, then the checker shall report a finding with the code `contradictory-examples` that names both, with the lines of both.
- **CONTRACT-084** When two compared examples expect two matchers for the same field, the checker shall report no contradiction between them.
- **CONTRACT-085** If an example has a finding of its shape or of its directives, then the checker shall leave it out of the search for duplicates and contradictions.

## Tables of fields

A name is a text of letters, digits and hyphens that starts with a letter. A value is any data, with
the directives allowed where it is.

| Mapping | Field | Mandatory | Holds |
|---|---|---|---|
| Contract | `format` | Yes | The number 1 |
| Contract | `story` | Yes | A name |
| Contract | `may_modify_tests` | No | A list of texts |
| Contract | `requirements` | Yes | A list of requirements, not empty |
| Contract | `examples` | Yes | A list of examples |
| Contract | `relations` | No | A list of relations |
| Requirement | `id` | Yes | A name |
| Requirement | `kind` | Yes | `new`, `change` or `preserve` |
| Requirement | `text` | Yes | A text of one line |
| Requirement | `source` | Yes | `written` or `imported` |
| Requirement | `replaces` | No | A text of one line |
| Example | `id` | Yes | A name |
| Example | `requirement` | Yes | A name |
| Example | `case` | Yes | A name |
| Example | `boundary` | Yes | `function`, `cli` or `http` |
| Example | `target` | Yes | At `function`, a text `module:function`; at `cli`, a text of one line |
| Example | `description` | No | A text of one line |
| Example | `origin` | Yes | `human` or `model` |
| Example | `steps` | Yes | A list of steps, not empty |
| Step | `input` | Yes | A mapping |
| Step | `expect` | Yes | A mapping |
| Input at `function` | `args` | No | A list of values |
| Input at `function` | `kwargs` | No | A mapping of values |
| Expectation at `function` | `returns` | No | A value |
| Expectation at `function` | `raises` | No | A mapping with `type`, a name, and optionally `message`, a text or a matcher |
| Input at `cli` | `args` | No | A list of texts |
| Input at `cli` | `stdin` | No | A text |
| Input at `cli` | `files` | No | A mapping from a file name to a text |
| Input at `cli` | `env` | No | A mapping from a name to a text |
| Expectation at `cli` | `exit` | No | An integer |
| Expectation at `cli` | `stdout` | No | A text or a matcher |
| Expectation at `cli` | `stderr` | No | A text or a matcher |
| Expectation at `cli` | `files` | No | A mapping from a file name to a text or a matcher |
| Relation | `id` | Yes | A name |
| Relation | `requirement` | Yes | A name |
| Relation | `relation` | Yes | `idempotent` or `order-insensitive` |
| Relation | `target` | Yes | A text of one line |
| Relation | `over` | Only for `order-insensitive` | A text of one line |

## Table of directives

| Directive | Holds | Parameters | Where |
|---|---|---|---|
| `$text` | A literal block | `final_newline`, mandatory, `true` or `false` | Inputs and expectations |
| `$json` | A value | None | Inputs and expectations |
| `$literal` | Any data | None | Inputs and expectations |
| `$contains` | A text | None | Expectations |
| `$fullmatch` | A text that is a regular expression of Python | None | Expectations |
| `$approx` | A number | `tolerance`, mandatory, a number that is not negative | Expectations |
| `$unordered` | A list of values | None | Expectations |
| `$any` | `uuid` or `timestamp` | None | Expectations |
| `$ref` | Not supported in the first version | — | — |
