# SDD-EARS: SANDBOX-125
import json
from pathlib import Path

from dokime.core.observation import REPR_LIMIT, Boundary, ExampleRequest, NotJson
from dokime.sandbox.observations import read_observations

REQUEST = (ExampleRequest(example="E-1", boundary=Boundary.FUNCTION, target="m:f", inputs=({},)),)


def read(tmp_path: Path, written: object) -> object:
    data = {"examples": [{"example": "E-1", "ending": "completed", "steps": [written]}]}
    (tmp_path / "observations.json").write_text(json.dumps(data))
    ((step,),) = (o.steps for o in read_observations(tmp_path, REQUEST, 1_000_000))
    return step


def test_a_repr_within_the_limit_is_kept_whole(tmp_path: Path) -> None:
    seen = read(tmp_path, {"not_json": {"type": "V", "repr": "V(1)"}})
    assert seen == NotJson(type="V", representation="V(1)")


def test_a_repr_past_the_limit_is_kept_cut_and_marked(tmp_path: Path) -> None:
    seen = read(tmp_path, {"not_json": {"type": "V", "repr": "x" * (REPR_LIMIT + 1)}})
    assert seen == NotJson(type="V", representation="x" * REPR_LIMIT, cut=True)


def test_a_value_without_a_repr_is_kept_without_one(tmp_path: Path) -> None:
    assert read(tmp_path, {"not_json": {"type": "V"}}) == NotJson(type="V")
