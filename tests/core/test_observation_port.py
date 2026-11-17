# SDD-EARS: CORE-160 CORE-161 CORE-162 CORE-163 CORE-164 CORE-165 CORE-169 CORE-170 CORE-171
from dataclasses import fields
from pathlib import Path
from typing import get_type_hints

import pytest

from dokime.core.observation import (
    Boundary,
    Ending,
    ExampleObservation,
    ExampleObserver,
    ExampleRequest,
    Exited,
    NotJson,
    ObservationLimits,
    Raised,
    Returned,
    StepObservation,
)
from dokime.core.repository import RefusalError
from dokime.core.runtime import Digest

RAISED = Raised(
    type="TypeError",
    qualified="semver.errors.TypeError",
    classes=(
        "semver.errors.TypeError",
        "builtins.TypeError",
        "builtins.Exception",
        "builtins.BaseException",
        "builtins.object",
    ),
    message="no",
)


def test_the_port_offers_one_operation_that_observes() -> None:
    public = {name for name in vars(ExampleObserver) if not name.startswith("_")}
    assert public == {"observe"}
    hints = get_type_hints(ExampleObserver.observe)
    assert (hints["image"], hints["project"], hints["limits"]) == (Digest, Path, ObservationLimits)
    assert hints["requests"] == tuple[ExampleRequest, ...]
    assert hints["return"] == tuple[ExampleObservation, ...]


def test_a_request_carries_the_inputs_and_nothing_of_what_is_expected() -> None:
    names = {field.name for field in fields(ExampleRequest)}
    assert names == {"example", "boundary", "target", "inputs"}
    assert set(Boundary) == {Boundary.FUNCTION, Boundary.CLI}


def test_an_observation_carries_its_example_and_its_steps_in_order() -> None:
    steps = (Returned(value=1.5), RAISED)
    observed = ExampleObservation(example="E-1", steps=steps)
    assert (observed.example, observed.steps, observed.ending) == ("E-1", steps, Ending.COMPLETED)


def test_a_step_at_function_returns_raises_or_gives_a_value_json_cannot_hold() -> None:
    assert set(StepObservation.__value__.__args__) >= {Returned, Raised, NotJson}
    assert Returned(value={"a": [1, 2.5, None]}).value == {"a": [1, 2.5, None]}
    assert NotJson(type="set").type == "set"


def test_a_step_at_cli_carries_its_exit_its_output_its_error_and_its_files() -> None:
    step = Exited(exit=2, stdout="out", stderr="err", files={"a.txt": "text"})
    assert (step.exit, step.stdout, step.stderr, dict(step.files)) == (
        2,
        "out",
        "err",
        {"a.txt": "text"},
    )


def test_an_example_says_how_it_ended() -> None:
    assert set(Ending) == {Ending.COMPLETED, Ending.TIME_LIMIT, Ending.CRASHED}
    observed = ExampleObservation(
        example="E-2", steps=(Returned(value=0),), ending=Ending.TIME_LIMIT
    )
    assert (observed.ending, len(observed.steps)) == (Ending.TIME_LIMIT, 1)


def test_a_crashed_example_carries_its_signal_or_its_exit_code_when_known() -> None:
    killed = ExampleObservation(example="E-3", steps=(), ending=Ending.CRASHED, signal=9)
    failed = ExampleObservation(example="E-3", steps=(), ending=Ending.CRASHED, exit_code=1)
    unknown = ExampleObservation(example="E-3", steps=(), ending=Ending.CRASHED)
    assert (killed.signal, failed.exit_code, unknown.signal, unknown.exit_code) == (
        9,
        1,
        None,
        None,
    )


@pytest.mark.parametrize("ending", [Ending.COMPLETED, Ending.TIME_LIMIT])
@pytest.mark.parametrize("field_name", ["signal", "exit_code"])
def test_a_signal_or_an_exit_code_without_a_crash_is_rejected_naming_it(
    ending: Ending, field_name: str
) -> None:
    with pytest.raises(ValueError, match=field_name):
        ExampleObservation(example="E-4", steps=(), ending=ending, **{field_name: 1})


def test_an_exception_carries_its_name_its_full_name_and_its_mro() -> None:
    assert (RAISED.type, RAISED.qualified, RAISED.classes) == (
        "TypeError",
        "semver.errors.TypeError",
        (
            "semver.errors.TypeError",
            "builtins.TypeError",
            "builtins.Exception",
            "builtins.BaseException",
            "builtins.object",
        ),
    )


def test_a_refusal_of_the_port_is_the_refusal_of_the_repository_port() -> None:
    assert issubclass(RefusalError, Exception)
    assert (
        RefusalError("observation-unreadable", "the file is cut").finding.verdict.value == "ERROR"
    )
