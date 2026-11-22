# ADR-0079 · An example at function may call the methods of an object

**Status:** accepted

## Context

[ADR-0039](0039-what-a-contract-of-the-first-version-may-say.md) lets an example at `function` call
one target `module:function` with values of JSON at each step, and expect a value of JSON or an
exception. Of the 41 witnesses of the corpus, 21 are not expressible so. B3c read those 21 twice
against four options, fixed before the readings, and the maintainer resolved the six pairs that the
readings labelled apart (#206, `tests/corpus/boundary/`). Of the 18 witnesses that both new readers
of B3a label isolated, 9 are expressible today; each option would make them:

| Option | Isolated witnesses expressible, of 18 | Among the 9 not expressible today |
|---|---|---|
| (a) calls on an object | 11 | W07, W34 |
| (b) a session of Python | 17 | all but W15 |
| (c) fixtures of the pack | 13 | W07, W32, W34, W39 |
| (d) not widened | 9 | — |

W07 and W34 are fixes of python-semver that a contract cannot hold today: the comparison operators
of a `Version` with a malformed collection, and `Version.next_version` with a token of its own.
Both need an object built by one call and a method of it called after. Today each step of an example
at `function` calls the same target, and a value that is not JSON is recorded only by the name of its
type.

## Decision

This amends ADR-0039 in what an example at `function` may say; the rest of it stands.

**An example at `function` may call the methods of the object that its first step returns:**

- **A later step may name a method** with `call` in its input: it calls that method, by its name,
  on what the first step returned, with `args` and `kwargs` of JSON. A dunder method is a method,
  so `__eq__`, `__getitem__` or `__len__` can be called. A step without `call` calls the target, as
  today; the first step never has `call`.
- **`call` names a public method**: `contract check` refuses, with the verdict `FAIL`, a name that
  starts with an underscore, unless it starts and ends with two, as a dunder method does.
- **Each step with `call` is run whatever the steps before it gave**, as doctest runs each example
  of a docstring: a call that raises gives its exception to its own expectation, and the next calls
  run on the same object.
- **A value that is not JSON can be expected by its `repr`**, with the matcher `$repr` in
  `returns`: it holds when the value observed is not a value of JSON and its `repr` is the text
  given. A value of JSON is compared as a value of JSON, never by its `repr`.
- **`contract check` refuses a `$repr` that holds a memory address**, a text with ` at 0x`, with
  the verdict `FAIL`, since it would differ in each run, and a `$repr` longer than the 1,000
  characters of a `repr` that an observation keeps.
- **A `repr` observed longer than 1,000 characters** is kept cut, with a mark that it was cut; it is
  then longer than any text that a `$repr` may give, so `$repr` does not hold, and the step fails
  as any expectation that does not hold. It is neither `ERROR` nor `ASK`: what was observed is known
  to differ from what the contract expects, so nothing is left undecided, and the contract was not
  wrong to expect it.
- **When the first step does not return**, because it raises, the later steps that name a method
  are not run, and the example is observed with the steps it ran.
- **No code of whoever writes the contract**: no class, function, decorator or mock is defined in
  an example; its inputs stay values of JSON.

## Basis

Verified: the count of #206, which a test of the corpus recomputes from the two readings and the
resolution.

Looked for outside, and how each tool writes examples that build an object and call its methods:
doctest runs the examples of a docstring in one shallow copy of the globals of the module, so a
name bound by one example is seen by the next
([doctest](https://docs.python.org/3/library/doctest.html)); Hypothesis writes stateful tests as a
machine whose rules are calls on the system under test, with its state kept on the machine or in
bundles ([stateful tests](https://hypothesis.readthedocs.io/en/latest/stateful.html)); FitNesse's
ActionFixture builds an object with `start` and calls its methods by name with `enter`, `press`
and `check`, from a table that stays data, while the code it needs is written apart in fixtures
([ActionFixture](https://fitnesse.org/FitNesse/UserGuide/FixtureGallery/BasicFitFixtures/ActionFixture.html));
FitNesse says that DoFixture has replaced it
([DoFixture](https://fitnesse.org/FitNesse/UserGuide/FixtureGallery/FitLibraryFixtures/DoFixture.html)).
Option a is the table of ActionFixture without fixtures; option c would add them; option b is
doctest. No study was found that compares the cost of reviewing examples written as code with that
of examples written as data.

Reasoning only, not measured: the cost in pull requests, and that reviewing code costs the
maintainer more than reviewing data; the review of the contracts of B0, about 4 minutes each, was
of examples that are data.

## Alternatives considered

- **(b) A session of Python.** Discarded: it lets 17 of the 18 isolated witnesses in, but an example
  becomes code that the maintainer reviews as a test, against a contract made of data.
- **(c) Fixtures of the pack.** Not now: it adds W32 and W39, both of cachetools, at the cost of a
  module of code in the pack and two or three more pull requests. It stays a possible widening on
  top of this one if the cases of B3d ask for it, with the rule already decided of what a fixture
  holds: only what someone who uses the library would define to use it, never logic of checking.
- **(d) Not widened.** Discarded: half of the isolated witnesses stay out.

## Consequences

- **W07 and W34 can be good cases** of the boundary `function` in B3d, and so can W13 and W14,
  which ADR-0074 does not label isolated.
- **The format of the contract is tied more to Python** at `function`: dunder methods and `repr`.
  The boundary `function` was already of Python; `cli`, the boundary of the probe of a second
  language that the close of block B decides, does not change.
- **A `repr` may change between versions of the project**, so an example that expects one can fail
  for a change that is not a regression; it is a limit, and `$repr` is for values that JSON cannot
  hold.
- **The words for the agent** keep giving no value: a step that fails a `$repr` says that the value
  differs, not the text.
- **A call acts always on what the first step returned**, never on what a call before it returned:
  calls are not chained, so a method of an object that a call returns cannot be called; it is a
  limit.
- **A relation still runs only on sources of one step**, so an example with calls is never a source
  ([ADR-0076](0076-a-relation-runs-on-the-visible-examples-of-its-requirement.md)).
- **On the acceptance** of this ADR, ADR-0039 is marked amended by it.
