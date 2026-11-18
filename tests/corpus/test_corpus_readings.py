# SDD-EARS: CORPUS-060 CORPUS-061
"""The second reading of the witnesses of ADR-0057, and its agreement with the first."""

import tomllib
from pathlib import Path
from typing import Any

FIXTURE: dict[str, Any] = tomllib.loads((Path(__file__).parent / "witnesses.toml").read_text())
LABELS: list[dict[str, Any]] = FIXTURE.get("label", [])
SECOND: dict[str, Any] = FIXTURE.get("second_reading", {})


def test_the_second_reading_reads_every_witness_classified() -> None:
    read = [(r["project"], r["commit"]) for r in SECOND.get("label", [])]
    assert sorted(read) == sorted((label["project"], label["commit"]) for label in LABELS)
    for reading in SECOND.get("label", []):
        assert isinstance(reading["isolated"], bool), reading["commit"]
        assert isinstance(reading["expressible"], bool), reading["commit"]
        assert reading["reason"].strip(), reading["commit"]


def test_the_agreement_is_the_one_the_two_readings_give() -> None:
    second = {(r["project"], r["commit"]): r for r in SECOND.get("label", [])}
    pairs = [(label, second.get((label["project"], label["commit"]))) for label in LABELS]
    alike = {
        "isolated": sum(o is not None and m["isolated"] == o["isolated"] for m, o in pairs),
        "expressible": sum(
            o is not None and m["expressible"] == o["expressible"] for m, o in pairs
        ),
        "fits": sum(
            o is not None
            and (m["isolated"] and m["expressible"]) == (o["isolated"] and o["expressible"])
            for m, o in pairs
        ),
    }
    assert SECOND.get("alike") == alike
