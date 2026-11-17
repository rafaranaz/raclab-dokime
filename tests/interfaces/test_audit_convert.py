# SDD-EARS: INTERFACES-105 INTERFACES-106
from dataclasses import fields

import pytest

from dokime.core.findings import Finding
from dokime.core.verdicts import Verdict
from dokime.evidence import run as evidence
from dokime.interfaces.audit import CONVERTED, convert
from dokime.verify.aggregate import GateEntry, Status
from dokime.verify.result import Checks, GateResult

FOUND = Finding(code="example-fails", message="m", verdict=Verdict.FAIL, lines=(3,))


def ran(gate: str, unstable: tuple[str, ...]) -> GateEntry:
    result = GateResult(
        gate=gate, findings=(FOUND,), unstable=unstable, checks=(Checks("human", 2),)
    )
    return GateEntry(gate=gate, status=Status.RUN, result=result)


def test_the_conversion_names_every_field_of_the_result_of_a_gate() -> None:
    assert {f.name for f in fields(GateResult)} == CONVERTED
    assert {f.name for f in fields(GateEntry)} == {"gate", "status", "result", "reason"}
    assert {f.name for f in fields(Checks)} == {f.name for f in fields(evidence.Checks)}


def test_every_field_of_a_result_reaches_the_evidence() -> None:
    tests = convert(ran("existing-tests", ("t::a",)))
    assert tests == evidence.GateRan(
        gate="existing-tests",
        verdict=Verdict.FAIL,
        findings=(FOUND,),
        checks=(evidence.Checks("human", 2),),
        unstable_tests=("t::a",),
    )
    examples = convert(ran("baseline", ("E-1",)))
    assert isinstance(examples, evidence.GateRan)
    assert (examples.unstable_examples, examples.unstable_tests) == (("E-1",), ())


def test_a_gate_that_does_not_apply_keeps_its_reason() -> None:
    entry = GateEntry(gate="relations", status=Status.NOT_APPLICABLE, reason="block B")
    assert convert(entry) == evidence.GateNotApplicable("relations", "block B")


def test_unstable_items_of_another_gate_are_refused() -> None:
    with pytest.raises(ValueError, match="visible-examples"):
        convert(ran("visible-examples", ("E-1",)))
