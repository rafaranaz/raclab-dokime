# SDD-EARS: EVIDENCE-096
import pytest

from dokime.core.verdicts import Verdict
from dokime.evidence.run import FailedOrder, GateRan, RelationsRecord
from dokime.evidence.statement import build
from tests.evidence.runs import RECORD, gates_with, relating, run


def test_a_record_of_relations_on_another_gate_is_refused() -> None:
    other = GateRan("protected-paths", Verdict.PASS, relations=RECORD)
    with pytest.raises(ValueError, match="protected-paths"):
        build(run(gates=gates_with(other)))


@pytest.mark.parametrize(
    ("record", "named"),
    [
        (RelationsRecord(seed=-1), "-1"),
        (RelationsRecord(seed=1, failed=(FailedOrder("L 1", "E-1"),)), "L 1"),
        (RelationsRecord(seed=1, failed=(FailedOrder("L1", "E 1"),)), "E 1"),
        (RelationsRecord(seed=1, failed=(FailedOrder("L1", "E-1", (0, 0)),)), "(0, 0)"),
        (RelationsRecord(seed=1, failed=(FailedOrder("L1", "E-1", (1, 2)),)), "(1, 2)"),
    ],
)
def test_a_record_that_does_not_meet_its_form_is_refused(
    record: RelationsRecord, named: str
) -> None:
    with pytest.raises(ValueError, match=named.replace("(", r"\(").replace(")", r"\)")):
        build(relating(record))
