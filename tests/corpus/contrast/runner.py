"""Run one example of a dokime contract as a black box, and the JSON that carries the example.

The conversion copies this file as `run.py` beside a copy of the modules of dokime, so it imports
only the standard library and `dokime`; `python run.py` puts its own directory first on the path,
so `dokime` is that copy. Run from the root of a project,

    python run.py EXAMPLE_ID

it observes the example with the program that observes of dokime, in a process of its own, and
compares the observation with the oracle of dokime: 0 when it holds, 1 when it does not, and 2
when the program that observes ended with an error. The comparison happens in this process; the
code of the project runs only in the child of the program that observes.
"""

import dataclasses
import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from dokime.contract.expectations import (
    AnyValue,
    Approx,
    Contains,
    FullMatch,
    Json,
    Repr,
    Unordered,
)
from dokime.contract.model import Example, Step
from dokime.core.observation import Boundary, ExampleRequest, ObservationLimits
from dokime.oracle.compare import compare
from dokime.sandbox.observations import read_observations

HERE = Path(__file__).resolve().parent
TAG = "$dokime"
"""The key that names the type of a value in the JSON; no key of a contract begins with `$`
outside its directives, and none is this one."""
MATCHERS: dict[str, type] = {
    kind.__name__: kind for kind in (Contains, FullMatch, Approx, Unordered, AnyValue, Json, Repr)
}


def encode(example: Example) -> dict[str, Any]:
    """The example as JSON values, each matcher and tuple named by its type."""
    return {
        field.name: _encoded(getattr(example, field.name))
        for field in dataclasses.fields(example)
        if field.name != "steps"
    } | {
        "steps": [
            {"input": _encoded(dict(step.input)), "expect": _encoded(dict(step.expect))}
            for step in example.steps
        ]
    }


def _encoded(value: Any) -> Any:
    if type(value).__name__ in MATCHERS and dataclasses.is_dataclass(value):
        fields = {f.name: _encoded(getattr(value, f.name)) for f in dataclasses.fields(value)}
        return {TAG: type(value).__name__, **fields}
    if isinstance(value, tuple):
        return {TAG: "tuple", "items": [_encoded(item) for item in value]}
    if isinstance(value, list):
        return [_encoded(item) for item in value]
    if isinstance(value, Mapping):
        return {key: _encoded(item) for key, item in value.items()}
    return value


def decode(data: dict[str, Any]) -> Example:
    """The example that `encode` gave, rebuilt with the types of dokime; nothing is run."""
    steps = tuple(
        Step(input=_decoded(step["input"]), expect=_decoded(step["expect"]))
        for step in data["steps"]
    )
    fields = {key: value for key, value in data.items() if key != "steps"}
    return Example(**fields, steps=steps)


def _decoded(value: Any) -> Any:
    if isinstance(value, dict) and TAG in value:
        kind = value[TAG]
        if kind == "tuple":
            return tuple(_decoded(item) for item in value["items"])
        fields = {key: _decoded(item) for key, item in value.items() if key != TAG}
        return MATCHERS[kind](**fields)
    if isinstance(value, list):
        return [_decoded(item) for item in value]
    if isinstance(value, dict):
        return {key: _decoded(item) for key, item in value.items()}
    return value


def request_of(example: Example) -> ExampleRequest:
    """The request of an example, as `request_of` of `verify` gives it."""
    return ExampleRequest(
        example=example.id,
        boundary=Boundary(example.boundary),
        target=example.target,
        inputs=tuple(dict(step.input) for step in example.steps),
    )


def request_json(example: Example) -> dict[str, object]:
    """The request of an example as the podman adapter writes it into `requests.json`."""
    request = request_of(example)
    return {
        "example": request.example,
        "boundary": str(request.boundary),
        "target": request.target,
        "inputs": [dict(step) for step in request.inputs],
    }


def main(argv: list[str]) -> int:
    """Observe one example from the root of the project and say whether it holds."""
    name = argv[1]
    example = decode(json.loads((HERE / "examples" / f"{name}.json").read_text(encoding="utf-8")))
    limits = ObservationLimits()
    project = Path.cwd()
    interpreter = project / ".venv" / "bin" / "python"
    python = str(interpreter) if interpreter.exists() else sys.executable
    with tempfile.TemporaryDirectory(prefix="dokime-check-") as work:
        probe, out = Path(work) / "probe", Path(work) / "out"
        probe.mkdir()
        out.mkdir()
        requests = {
            "example_seconds": limits.example_seconds,
            "example_bytes": limits.observations_bytes,
            "examples": [request_json(example)],
        }
        (probe / "requests.json").write_text(json.dumps(requests), encoding="utf-8")
        path = os.pathsep.join([str(project / "src"), str(project)])
        ended = subprocess.run(
            [python, "-I", "-S", str(HERE / "observe_program.py"), str(probe), str(out)],
            cwd=project,
            env={**os.environ, "PYTHONPATH": path},
            check=False,
        )
        if ended.returncode != 0:
            print(f"dokime-check {name}: the program that observes ended with {ended.returncode}")
            return 2
        (observation,) = read_observations(out, (request_of(example),), limits.observations_bytes)
    holds = compare(example, observation).holds
    print(f"dokime-check {name}: {'holds' if holds else 'does not hold'}")
    return 0 if holds else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
