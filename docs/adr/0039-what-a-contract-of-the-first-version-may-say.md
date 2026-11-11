# ADR-0039 · What a contract of the first version may say, and what its check decides

**Status:** accepted

## Context

Milestone A1 checks a contract and says what it lacks. Writing its requirements showed that the
format left several things open: which boundaries the first version accepts, which fields an
example has at each one, whether an example must say its origin, which relations exist, what
exactly a contradiction and a duplicate are, and what each matcher means. A check cannot reject
what the format does not define.

## Decision

- **Boundaries.** The first version checks examples at `function` and `cli`. An example at `http`,
  or the matcher `$ref`, gives a finding `not-supported-yet` with the verdict `ERROR`: the harness
  could not evaluate it, and the contract is not blamed.
- **Origin.** Every example says its `origin`, `human` or `model`. There is no default.
- **Relations.** The catalogue starts with two: `idempotent` and `order-insensitive`. A relation
  has `id`, `requirement`, `relation` and `target`; `order-insensitive` also has `over`, the input
  whose order does not matter. The first version checks their shape; they run from block B. The
  catalogue grows only by ADR.
- **Contradiction.** Two examples with the same boundary, target and inputs whose expectations
  cannot both hold. Two different exact values contradict. An exact value contradicts a matcher
  that it does not satisfy. Two matchers are not compared. With several steps, the steps with the
  same inputs from the start are the ones compared.
- **Duplicate.** Two examples with the same boundary, target and steps, whatever their id, case
  and description.
- **Verdicts.** A broken schema, a requirement text that is not EARS, a contradiction and a
  duplicate give `FAIL`. A requirement with no example, or with examples of origin `model` only,
  gives `ASK` ([ADR-0013](0013-provenance-decides-what-a-check-can-do.md)).

The fields of an example are closed; an unknown one is a finding. What `expect` does not declare
is not compared, and a step declares at least one expectation.

| Boundary | `target` | `input` | `expect` |
|---|---|---|---|
| `function` | `module:function` | `args` (a list), `kwargs` (a mapping) | `returns` (a value) or `raises` (`type`, the name of the exception, and optionally `message`) |
| `cli` | The command | `args` (a list of texts), `stdin` (a text), `files` and `env` (mappings from a name to a text) | `exit` (an integer), `stdout`, `stderr` (texts), `files` (a mapping from a name to a text) |

The matchers of the first version:

| Matcher | Expected value | Holds when |
|---|---|---|
| `$contains` | A text | The observed text contains it |
| `$pattern` | A regular expression of Python | It matches the whole observed text |
| `$approx`, with `tolerance` | A number | The observed number differs by no more than `tolerance`, which is absolute and mandatory |
| `$unordered` | A list | The observed list has the same items, in any order |
| `$any` | `uuid` or `timestamp` | The observed text is a UUID, or a date and time in ISO 8601 |

## Basis

From the three hand-written contracts of milestone A0: they use `args`, `kwargs`, `returns`,
`exit`, `stdout` and `files`, one relation (`idempotent`) and one matcher (`$contains`). The other
fields, `order-insensitive` and the other matchers have not been used in a real contract.

Read in the sources:

- The JSON Schema specification says that its regular expressions are not anchored: a pattern
  matches anywhere in the text. `$pattern` does the opposite on purpose. A pattern that is too
  strict fails where a person sees it; one that is too loose passes in silence. `$contains`
  already covers "anywhere".
- `pytest.approx` (version 9.2.0) compares with a relative tolerance of one in a million by
  default. `$approx` has no default: the person who approves sees the tolerance.
- `ERROR` for what the version cannot check follows
  [ADR-0015](0015-a-gate-returns-one-of-four-verdicts.md): it never passes and it does not mark
  the change as bad.

Reasoning, without a test: a mandatory `origin`, because a default of `human` would grant trust
that nobody wrote; `FAIL` for a duplicate, because it inflates the number of examples per case
that the hold-out counts; fixing two relations now, as milestone A1 opened `interfaces` early
([ADR-0036](0036-a-milestone-may-open-an-increment-of-a-later-module.md)), so that an invented
name is caught from the first version. Not looked for: how other tools define a contradiction
between examples.

## Alternatives considered

- **`FAIL` for what is not supported yet.** It would blame the contract for a limit of the tool.
- **Only the fields that A0 used.** A smaller surface, and the first contract with an error case
  or with standard input would need a change of format.
- **`origin` with `human` by default.** One line less per example.
- **Check only the shape of relations until block B.** An invented relation name would pass the
  check of the first version.
- **Compare two matchers.** Deciding whether two patterns can both hold is not possible in
  general; a partial answer would look like a complete one.

## Consequences

- The meaning of the matchers lives in `contract`, because the contradiction check needs it;
  `oracle` uses it from there, which the dependency rules allow.
- The A0 contracts gain `origin: human` on each example.
- A contract that needs `http` or `$ref` cannot be checked until a later block, and the check
  says so.
