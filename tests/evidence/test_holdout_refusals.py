# SDD-EARS: EVIDENCE-049
import dataclasses

import pytest

from dokime.core.verdicts import Verdict
from dokime.evidence.run import GateRan, HeldCase, UnheldCase
from dokime.evidence.statement import build
from tests.evidence.runs import HOLDOUT, gates_with, run, sealed


def test_a_hold_out_on_another_gate_is_refused() -> None:
    other = GateRan("protected-paths", Verdict.PASS, holdout=HOLDOUT)
    with pytest.raises(ValueError, match="protected-paths"):
        build(run(gates=gates_with(other)))


@pytest.mark.parametrize(
    ("changes", "named"),
    [
        ({"held": (HeldCase("R 1", "c1"),)}, "R 1"),
        ({"held": (HeldCase("R-1", "c 1"),)}, "c 1"),
        ({"kept_visible": ("E k1",)}, "E k1"),
        ({"without_holdout": (UnheldCase("R-1", "c-x", "forgotten"),)}, "forgotten"),
        ({"batch": "sha256:short"}, "sha256:short"),
    ],
)
def test_a_hold_out_that_does_not_meet_its_form_is_refused(
    changes: dict[str, object], named: str
) -> None:
    with pytest.raises(ValueError, match=named):
        build(sealed(dataclasses.replace(HOLDOUT, **changes)))  # type: ignore[arg-type]
