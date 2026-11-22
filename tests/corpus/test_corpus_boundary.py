# SDD-EARS: CORPUS-080 CORPUS-081 CORPUS-082 CORPUS-083
"""The reading of the boundary of B3c, recomputed from what was recorded."""

import hashlib
import re
import tomllib
from pathlib import Path
from typing import Any

from tests.corpus.test_corpus_blind_reading import draw, labels

HERE = Path(__file__).parent
BOUNDARY = HERE / "boundary"
READINGS = ("first-reading.txt", "second-reading.txt")
LABEL = re.compile(r"^(W\d\d) \| ([a-z]) \| (fits|does-not-fit|undecidable) \|", re.M)
Labels = dict[tuple[str, str], str]


def toml(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text()) if path.exists() else {}


def options() -> list[str]:
    return [o["id"] for o in toml(BOUNDARY / "options.toml")["option"]]


def not_expressible() -> list[str]:
    ids = {(w["project"], w["commit"]): w["id"] for w in draw()["witness"]}
    read = toml(HERE / "witnesses.toml")
    return sorted(
        ids[(label["project"], label["commit"])]
        for label in read["label"]
        if not label["expressible"]
    )


def reading(name: str) -> Labels:
    found = LABEL.findall((BOUNDARY / name).read_text())
    return {(w, o): label for w, o, label in found}


def resolution() -> Labels:
    resolved = toml(BOUNDARY / "resolution.toml").get("resolved", [])
    return {(r["witness"], r["option"]): r["label"] for r in resolved}


def final() -> Labels:
    first, second = (reading(r) for r in READINGS)
    return {k: first[k] if first[k] == second[k] else resolution()[k] for k in first}


def isolated() -> set[str]:
    """The witnesses that both new readers of B3a label isolated."""
    a, b = labels("A"), labels("B")
    return {w for w in a if a[w][0] == "isolated" and b[w][0] == "isolated"}


def computed() -> dict[str, Any]:
    labelled = final()
    today = {w["id"] for w in draw()["witness"]} - set(not_expressible())
    found: dict[str, Any] = {}
    for option in options():
        fits = sorted(w for (w, o), label in labelled.items() if o == option and label == "fits")
        found[option] = {
            "fits": fits,
            "isolated": sorted(set(fits) & isolated()),
            "expressible_isolated": len((today | set(fits)) & isolated()),
            "isolated_of_41": len(isolated()),
        }
    return found


def test_each_batch_is_the_file_that_was_given() -> None:
    batches = toml(BOUNDARY / "batches.toml")["batch"]
    assert sorted(w for b in batches for w in b["witnesses"]) == not_expressible()
    for batch in batches:
        digest = hashlib.sha256((BOUNDARY / batch["file"]).read_bytes()).hexdigest()
        assert digest == batch["sha256"], batch["file"]


def test_each_reading_labels_each_witness_once_for_each_option() -> None:
    wanted = {(w, o) for w in not_expressible() for o in options()}
    for name in READINGS:
        text = (BOUNDARY / name).read_text()
        assert len(LABEL.findall(text)) == len(wanted), name
        assert set(reading(name)) == wanted, name


def test_the_resolution_covers_the_pairs_read_apart_and_no_other() -> None:
    first, second = (reading(r) for r in READINGS)
    apart = {k for k in first if first[k] != second[k]}
    precisions = {p["id"] for p in toml(BOUNDARY / "options.toml")["precision"]}
    resolved = toml(BOUNDARY / "resolution.toml").get("resolved", [])
    assert set(resolution()) == apart
    assert all(r["precision"] in precisions and r["label"] != "undecidable" for r in resolved)


def test_the_result_is_the_one_recomputed() -> None:
    assert toml(BOUNDARY / "result.toml").get("option") == computed()
