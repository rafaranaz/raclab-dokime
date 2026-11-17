# SDD-EARS: SANDBOX-112 SANDBOX-113 SANDBOX-114 SANDBOX-115 SANDBOX-116 SANDBOX-118
import json
from pathlib import Path

import pytest

from dokime.core.observation import (
    Boundary,
    Ending,
    ExampleObservation,
    ExampleRequest,
    Exited,
    NotJson,
    Raised,
    Returned,
)
from dokime.sandbox.observations import read_observations
from tests.sandbox.engines import refusal

REQUESTS = (
    ExampleRequest(example="E-1", boundary=Boundary.FUNCTION, target="m:f", inputs=({},) * 4),
    ExampleRequest(example="E-2", boundary=Boundary.CLI, target="cmd", inputs=({},)),
)
RAISED = {
    "type": "BadPart",
    "qualified": "m.BadPart",
    "classes": ["m.BadPart", "builtins.TypeError", "builtins.object"],
    "message": "bad",
}
WRITTEN = {
    "examples": [
        {
            "example": "E-1",
            "ending": "crashed",
            "signal": 9,
            "steps": [
                {"returned": {"a": [1, 2.5, None]}},
                {"raised": RAISED},
                {"not_json": "set"},
            ],
        },
        {
            "example": "E-2",
            "ending": "completed",
            "steps": [{"exit": 1, "stdout": "o", "stderr": "e", "files": {"a.md": "x"}}],
        },
    ]
}


def written(tmp_path: Path, data: object) -> Path:
    text = data if isinstance(data, str) else json.dumps(data)
    (tmp_path / "observations.json").write_text(text)
    return tmp_path


def test_the_observations_are_given_as_the_types_of_the_port(tmp_path: Path) -> None:
    assert read_observations(written(tmp_path, WRITTEN), REQUESTS, 10_000) == (
        ExampleObservation(
            example="E-1",
            steps=(
                Returned(value={"a": [1, 2.5, None]}),
                Raised(
                    type="BadPart",
                    qualified="m.BadPart",
                    classes=("m.BadPart", "builtins.TypeError", "builtins.object"),
                    message="bad",
                ),
                NotJson(type="set"),
            ),
            ending=Ending.CRASHED,
            signal=9,
        ),
        ExampleObservation(
            example="E-2",
            steps=(Exited(exit=1, stdout="o", stderr="e", files={"a.md": "x"}),),
        ),
    )


def test_a_decimal_returned_is_kept(tmp_path: Path) -> None:
    data = {"examples": [{"example": "E-1", "ending": "completed", "steps": [{"returned": 0.1}]}]}
    (observed,) = read_observations(written(tmp_path, data), REQUESTS[:1], 10_000)
    assert observed.steps == (Returned(value=0.1),)


def test_missing_observations_are_refused(tmp_path: Path) -> None:
    assert refusal(lambda: read_observations(tmp_path, REQUESTS, 10_000)).code == (
        "observations-missing"
    )


def test_observations_larger_than_their_bytes_are_refused(tmp_path: Path) -> None:
    out = written(tmp_path, WRITTEN)
    size = (out / "observations.json").stat().st_size
    assert read_observations(out, REQUESTS, size)
    finding = refusal(lambda: read_observations(out, REQUESTS, size - 1))
    assert finding.code == "observations-too-large"


def test_observations_reached_through_a_link_are_not_followed(tmp_path: Path) -> None:
    elsewhere = tmp_path / "elsewhere.json"
    elsewhere.write_text(json.dumps(WRITTEN))
    out = tmp_path / "out"
    out.mkdir()
    (out / "observations.json").symlink_to(elsewhere)
    assert refusal(lambda: read_observations(out, REQUESTS, 10_000)).code == (
        "observations-unreadable"
    )


ONE = '{{"examples": [{{"example": "E-1", "ending": "completed", "steps": [{step}]}}]}}'


def deep(levels: int) -> str:
    value = "1"
    for _ in range(levels):
        value = "[" + value + "]"
    return (
        '{"examples": [{"example": "E-1", "ending": "completed", "steps": [{"returned": '
        + value
        + "}]}]}"
    )


@pytest.mark.parametrize(
    "text",
    [
        "not json",
        '{"examples": [], "examples": []}',
        '{"examples": [{"example": "E-1", "ending": "completed", "steps": [{"returned": NaN}]}]}',
        ONE.format(step='{"returned": Infinity}'),
        deep(130),
        deep(100_000),
        '{"examples": [{"example": "E-1", "ending": "paused", "steps": []}]}',
        '{"examples": [{"example": "E-1", "ending": "completed"}]}',
        '{"examples": [{"example": "E-1", "ending": "completed", "steps": [{"what": 1}]}]}',
        ONE.format(step='{"raised": {"type": 1}}'),
        '{"examples": [{"example": "E-1", "ending": "completed", "signal": 9, "steps": []}]}',
    ],
    ids=[
        "not-json",
        "a-repeated-key",
        "nan",
        "infinity",
        "too-deep",
        "far-too-deep",
        "an-unknown-ending",
        "no-steps",
        "an-unknown-step",
        "a-raised-of-the-wrong-shape",
        "a-signal-without-a-crash",
    ],
)
def test_observations_that_cannot_be_read_are_refused(tmp_path: Path, text: str) -> None:
    out = written(tmp_path, text)
    finding = refusal(lambda: read_observations(out, REQUESTS[:1], 10_000_000))
    assert finding.code == "observations-unreadable"


@pytest.mark.parametrize("names", [["E-2", "E-1"], ["E-1"], ["E-1", "E-2", "E-3"], ["E-1", "E-9"]])
def test_observations_of_other_examples_or_in_another_order_are_refused(
    tmp_path: Path, names: list[str]
) -> None:
    data = {"examples": [{"example": n, "ending": "completed", "steps": []} for n in names]}
    finding = refusal(lambda: read_observations(written(tmp_path, data), REQUESTS, 10_000))
    assert finding.code == "observations-unreadable"
