# SDD-EARS: EVIDENCE-050
import dataclasses

from dokime.core.findings import Finding
from dokime.core.verdicts import Verdict
from dokime.evidence.statement import build
from tests.evidence.runs import CONTRACT, sealed

HELD_ID = "E-h1"
STEPS = "input: {args: [714212]}"
STUB = (
    f"held_out:\n  - id: {HELD_ID}\n    requirement: R-1\n    case: c1\n"
    "    digest: sha256:" + "9" * 64 + "\n"
)


def test_a_whole_sealed_evidence_holds_no_id_of_a_held_out_example_nor_a_value() -> None:
    failed = Finding(
        code="sealed-example-fails",
        message="the requirement R-1 fails a held-out example: returns",
        verdict=Verdict.FAIL,
        lines=(40,),
    )
    given = sealed(verdict=Verdict.FAIL, findings=(failed,))
    whole = dataclasses.replace(
        given,
        verdict=Verdict.FAIL,
        contract=dataclasses.replace(CONTRACT, text=CONTRACT.text + STUB.encode()),
    )
    data = build(whole).data
    assert HELD_ID.encode() not in data
    assert b"9" * 64 not in data
    assert STEPS.encode() not in data
    assert b"714212" not in data
    assert b"case-without-holdout" in data
