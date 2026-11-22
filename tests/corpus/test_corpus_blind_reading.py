# SDD-EARS: CORPUS-076 CORPUS-077 CORPUS-078 CORPUS-079
"""The blind reading of the witnesses (ADR-0074, B3a), recomputed from what was recorded."""

import hashlib
import random
import re
import tomllib
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent
BLIND = HERE / "blind"
READERS = ("A", "B")
LABEL = re.compile(r"(W\d\d) \| (isolated|not-isolated|undecidable) \| ([-1-4]) \|")
Labels = dict[str, tuple[str, str]]


def toml(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text()) if path.exists() else {}


def draw() -> dict[str, Any]:
    return toml(BLIND / "draw.toml")


def witnesses() -> dict[str, Any]:
    return toml(HERE / "witnesses.toml")


def batches() -> list[list[str]]:
    """The ids of each batch, in the order of the draw."""
    ids = [w["id"] for w in draw()["witness"]]
    found, start = [], 0
    for batch in draw()["batch"]:
        found.append(ids[start : start + batch["witnesses"]])
        start += batch["witnesses"]
    return found


def answer(reader: str, batch: int) -> Labels:
    """The label of each witness in one answer: the last, when a reader corrects itself."""
    text = (BLIND / "answers" / f"{reader}-{batch}.txt").read_text()
    return {w: (label, condition) for w, label, condition in LABEL.findall(text)}


def labels(reader: str) -> Labels:
    return {w: found for n in range(1, 5) for w, found in answer(reader, n).items()}


def disputed() -> list[str]:
    """The ids of the eight witnesses that the two readings of block A labelled apart."""
    read = witnesses()
    apart = {
        (first["project"], first["commit"])
        for first, second in zip(read["label"], read["second_reading"]["label"], strict=True)
        if first["isolated"] != second["isolated"]
    }
    return [w["id"] for w in draw()["witness"] if (w["project"], w["commit"]) in apart]


def agreement(ids: list[str]) -> dict[str, object]:
    """Kappa of Cohen and the raw agreement on isolated, an undecidable counted as not isolated."""
    a, b = ([labels(r)[w][0] == "isolated" for w in ids] for r in READERS)
    n = len(ids)
    alike = sum(x == y for x, y in zip(a, b, strict=True))
    expected = (sum(a) * sum(b) + (n - sum(a)) * (n - sum(b))) / n**2
    kappa: object = (
        "undefined" if expected == 1 else round((alike / n - expected) / (1 - expected), 4)
    )
    return {"witnesses": n, "alike": alike, "kappa": kappa}


def result() -> dict[str, Any]:
    return toml(BLIND / "result.toml")


def test_the_draw_is_the_one_its_seed_gives() -> None:
    order = sorted((w["project"], w["commit"]) for w in witnesses()["label"])
    random.Random(draw()["seed"]).shuffle(order)  # noqa: S311 - a draw anyone can repeat
    drawn = [(w["project"], w["commit"]) for w in draw()["witness"]]
    assert drawn == order
    assert [w["id"] for w in draw()["witness"]] == [f"W{n:02d}" for n in range(1, 42)]


def test_each_batch_is_the_file_that_was_given() -> None:
    for batch in draw()["batch"]:
        digest = hashlib.sha256((BLIND / batch["file"]).read_bytes()).hexdigest()
        assert digest == batch["sha256"], batch["file"]


def test_each_answer_labels_each_witness_of_its_batch_and_no_other() -> None:
    for reader in READERS:
        for number, ids in enumerate(batches(), 1):
            assert sorted(answer(reader, number)) == ids, (reader, number)


def test_a_reader_that_corrects_itself_counts_with_its_last_label() -> None:
    assert answer("A", 3)["W28"] == ("isolated", "-")


def test_the_result_on_the_41_and_on_the_eight_is_the_one_recomputed() -> None:
    ids = [w["id"] for w in draw()["witness"]]
    assert len(disputed()) == 8
    assert result().get("all") == agreement(ids)
    assert result().get("eight") == agreement(disputed())


def test_what_decides_nothing_is_the_one_recomputed() -> None:
    undecidable = [
        {"reader": r, "witness": w, "condition": int(found[1])}
        for r in READERS
        for w, found in sorted(labels(r).items())
        if found[0] == "undecidable"
    ]
    excluded = {u["witness"] for u in undecidable}
    decided = [w["id"] for w in draw()["witness"] if w["id"] not in excluded]
    assert result().get("undecidable") == undecidable
    assert result().get("decided") == agreement(decided)
