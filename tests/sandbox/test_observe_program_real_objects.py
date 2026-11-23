# SDD-EARS: SANDBOX-120 SANDBOX-121 SANDBOX-123 SANDBOX-125
"""Calls on objects of real code, from the program to the oracle: the classes of the standard
library stand for the project, since the corpus, which has cachetools and semver, runs elsewhere."""

from pathlib import Path

from dokime.contract.check import check
from dokime.core.observation import NotJson, Raised, Returned
from dokime.oracle.compare import compare
from dokime.sandbox.observations import read_observations
from dokime.verify.examples import request_of
from tests.sandbox.observing import function, observe, project

CONTRACT = """\
format: 1
story: s
may_modify_tests: []
requirements:
  - id: r
    kind: new
    text: When a fraction is built, the system shall reduce it.
    source: written
examples:
  - id: E-1
    requirement: r
    case: c
    boundary: function
    target: fractions:Fraction
    origin: human
    steps:
      - input: {args: [2, 6]}
        expect: {returns: {$repr: 'Fraction(1, 3)'}}
      - input: {call: __add__, args: [1]}
        expect: {returns: {$repr: 'Fraction(4, 3)'}}
      - input: {call: limit_denominator, args: [0]}
        expect: {raises: {type: ValueError}}
      - input: {call: __eq__, args: [0.5]}
        expect: {returns: false}
      - input: {call: as_integer_ratio}
        expect: {returns: [1, 3]}
  - id: E-2
    requirement: r
    case: c
    boundary: function
    target: collections:OrderedDict
    origin: human
    steps:
      - input: {}
        expect: {returns: {}}
      - input: {call: __setitem__, args: [a, 1]}
        expect: {returns: null}
      - input: {call: __len__}
        expect: {returns: 1}
"""


def test_calls_on_real_objects_are_observed_and_compared(tmp_path: Path) -> None:
    checked = check(CONTRACT)
    assert checked.findings == ()
    assert checked.contract is not None
    examples = checked.contract.examples
    requests = tuple(request_of(example) for example in examples)
    code = project(tmp_path / "code", {})
    asked = (function(r.example, r.target, *map(dict, r.inputs)) for r in requests)
    run = observe(tmp_path, code, *asked)
    assert run.code == 0
    observed = read_observations(tmp_path / "out", requests, 1_000_000)
    fraction, ordered = observed
    assert fraction.steps[0] == NotJson(type="Fraction", representation="Fraction(1, 3)")
    assert fraction.steps[1] == NotJson(type="Fraction", representation="Fraction(4, 3)")
    assert isinstance(fraction.steps[2], Raised)
    assert fraction.steps[2].qualified == "builtins.ValueError"
    assert fraction.steps[3:] == (Returned(False), Returned([1, 3]))
    assert ordered.steps[1:] == (Returned(None), Returned(1))
    for example, seen in zip(examples, observed, strict=True):
        assert compare(example, seen).holds, compare(example, seen).differences
