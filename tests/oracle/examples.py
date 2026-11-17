"""Examples of a contract and their observations, built for the tests of the oracle."""

from collections.abc import Mapping

from dokime.contract.expectations import Expected
from dokime.contract.model import Example, Step
from dokime.core.observation import Ending, ExampleObservation, Raised, StepObservation


def example(boundary: str, *expects: Mapping[str, Expected], name: str = "E-1") -> Example:
    steps = tuple(Step(input={}, expect=dict(expect)) for expect in expects)
    return Example(
        id=name,
        requirement="r",
        case="c",
        boundary=boundary,
        target="m:f" if boundary == "function" else "cmd",
        description=None,
        origin="human",
        steps=steps,
        line=1,
    )


def observed(
    *steps: StepObservation,
    name: str = "E-1",
    ending: Ending = Ending.COMPLETED,
    signal: int | None = None,
    exit_code: int | None = None,
) -> ExampleObservation:
    return ExampleObservation(
        example=name, steps=steps, ending=ending, signal=signal, exit_code=exit_code
    )


def raised(module: str, name: str, *bases: str, message: str = "it failed") -> Raised:
    own = f"{module}.{name}"
    return Raised(
        type=name,
        qualified=own,
        classes=(own, *bases, "builtins.BaseException", "builtins.object"),
        message=message,
    )
