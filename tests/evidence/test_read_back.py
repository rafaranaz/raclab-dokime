# SDD-EARS: EVIDENCE-080 EVIDENCE-081 EVIDENCE-082 EVIDENCE-085
import json

import pytest

from dokime.core.ledger import Head
from dokime.core.verdicts import Verdict
from dokime.evidence.run import GateNotApplicable
from dokime.evidence.schema import read_back
from dokime.evidence.statement import build
from tests.evidence.runs import inputs, run, statement


@pytest.mark.parametrize(
    "given",
    [
        run(),
        run(contract=None),
        run(inputs=inputs(image=None, pack=None, probe=None)),
        run(ledger=Head(hash=None, events=0), gates=()),
        run(verdict=Verdict.PASS, harness="0.0.0-ñ"),
    ],
)
def test_the_bytes_of_a_run_read_back_without_a_finding(given: object) -> None:
    assert read_back(build(given).data) == ()  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "data",
    [
        b"not json",
        b"\xff\xfe",
        b'{"a":1,"a":2}',
        b'{"a":1.5}',
        b'{"a":1e3}',
        b'{"a":NaN}',
        b'{"a":-Infinity}',
    ],
)
def test_bytes_that_are_not_json_of_whole_numbers_are_refused(data: bytes) -> None:
    (found,) = read_back(data)
    assert (found.code, found.verdict) == ("evidence-not-json", Verdict.ERROR)


@pytest.mark.parametrize(
    "data",
    [
        json.dumps(statement(), indent=2).encode(),
        b'{"a":"\\ud800"}',
        b'{"a":9007199254740993}',
    ],
)
def test_bytes_that_are_not_the_canonical_form_are_refused(data: bytes) -> None:
    (found,) = read_back(data)
    assert (found.code, found.verdict) == ("evidence-not-canonical", Verdict.ERROR)


@pytest.mark.parametrize(
    ("given", "named"),
    [
        (run(harness=""), "harness"),
        (run(gates=(GateNotApplicable("sealed-examples", ""),)), "reason"),
    ],
)
def test_a_run_whose_bytes_do_not_read_back_is_refused(given: object, named: str) -> None:
    with pytest.raises(ValueError, match="evidence-schema") as raised:
        build(given)  # type: ignore[arg-type]
    assert named in str(raised.value)
