"""A small project and a contract on it, for the tests of the conversion of R2; never the corpus."""

from pathlib import Path

import pytest

from dokime.contract.check import check
from dokime.contract.model import Example
from tests.corpus.contrast.convert import convert

SOURCE = Path(__file__).parents[3] / "src" / "dokime"
CONTRAST = Path(__file__).parent

PROJECT = """
import uuid


class Thing:
    def __repr__(self):
        return "Thing()"


def add(a, b):
    return a + b


def shapes():
    return {"a": 0.1004, "b": [2, 1], "c": "hello", "d": "hello", "e": str(uuid.uuid4())}


def thing():
    return Thing()


def as_json():
    return '{"a": 1}'
"""

CONTRACT = """\
format: 1
story: contrast
may_modify_tests: []

requirements:
  - id: adds
    kind: new
    text: When the function is called with two numbers, the function shall return their sum.
    source: written

examples:
  - id: E-1
    requirement: adds
    case: sum
    boundary: function
    target: proj:add
    origin: human
    steps:
      - input: {args: [2, 3]}
        expect: {returns: 5}
  - id: E-2
    requirement: adds
    case: sum
    boundary: function
    target: proj:add
    origin: human
    steps:
      - input: {args: [2, 2]}
        expect: {returns: 5}
  - id: E-3
    requirement: adds
    case: command
    boundary: cli
    target: python -c 'print(1)'
    origin: human
    steps:
      - input: {args: []}
        expect: {exit: 0, stdout: "1\\n"}
  - id: E-4
    requirement: adds
    case: matchers
    boundary: function
    target: proj:shapes
    origin: human
    steps:
      - input: {args: []}
        expect:
          returns:
            a: {$approx: 0.1, tolerance: 0.01}
            b: {$unordered: [1, 2]}
            c: {$contains: ell}
            d: {$fullmatch: "h.*o"}
            e: {$any: uuid}
  - id: E-5
    requirement: adds
    case: repr
    boundary: function
    target: proj:thing
    origin: human
    steps:
      - input: {args: []}
        expect: {returns: {$repr: "Thing()"}}
  - id: E-6
    requirement: adds
    case: json
    boundary: function
    target: proj:as_json
    origin: model
    steps:
      - input: {args: []}
        expect: {returns: {$json: {a: 1}}}
"""
IDS = ["E-1", "E-2", "E-3", "E-4", "E-5", "E-6"]


def examples() -> dict[str, Example]:
    contract = check(CONTRACT).contract
    assert contract is not None
    return {example.id: example for example in contract.examples}


@pytest.fixture
def project(tmp_path: Path) -> Path:
    directory = tmp_path / "project"
    directory.mkdir()
    (directory / "proj.py").write_text(PROJECT)
    return directory


@pytest.fixture
def converted(project: Path) -> Path:
    out = project / "tests" / "dokime_examples"
    convert(CONTRACT, IDS, out)
    return out
