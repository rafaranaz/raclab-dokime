# SDD-EARS: CORE-160 CORE-161 CORE-162 CORE-163 CORE-164 CORE-165 CORE-169
from dataclasses import fields
from pathlib import Path
from typing import get_type_hints

from dokime.core.observation import (
    Boundary,
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
    steps = (Returned(value=1.5), Raised(type="TypeError", message="no"))
    observed = ExampleObservation(example="E-1", steps=steps)
    assert (observed.example, observed.steps, observed.time_limit) == ("E-1", steps, False)


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


def test_an_example_that_reached_its_limit_says_so_with_the_steps_before() -> None:
    observed = ExampleObservation(example="E-2", steps=(Returned(value=0),), time_limit=True)
    assert (observed.time_limit, len(observed.steps)) == (True, 1)


def test_a_refusal_of_the_port_is_the_refusal_of_the_repository_port() -> None:
    assert issubclass(RefusalError, Exception)
    assert (
        RefusalError("observation-unreadable", "the file is cut").finding.verdict.value == "ERROR"
    )
