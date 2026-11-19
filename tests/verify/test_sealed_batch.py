# SDD-EARS: VERIFY-150 VERIFY-151 VERIFY-152
import dataclasses
import json
import random

import pytest

from dokime.core.canonical import canonical
from dokime.core.repository import RefusalError
from dokime.verify.sealed import Canary, batch_bytes, make_canary, read_batch
from tests.verify.sealed_contracts import IMPOSSIBLE, batch_of, held, split


def test_a_batch_is_the_canonical_form_of_its_mapping() -> None:
    contract, sealed = split(("E-h1", held("E-h1")))
    batch = batch_of(contract, sealed)
    expected = {
        "format": 1,
        "story": "S-1",
        "seed": 7,
        "order": ["E-p0", "E-h1", "E-s1", "E-q1", "E-q2"],
        "kept_visible": ["E-p0", "E-q1", "E-q2"],
        "examples": [{"id": "E-h1", "salt": sealed[0].salt.hex(), "text": sealed[0].text}],
        "without_holdout": [
            {"requirement": "R-new", "case": "c-single", "reason": "single-example"},
            {"requirement": "R-new", "case": "c-pub", "reason": "all-published"},
        ],
        "canary": {"id": "E-cana", "of": "E-h1", "expected": IMPOSSIBLE},
    }
    assert batch_bytes(batch) == canonical(expected).encode()


def test_a_batch_reads_back_as_it_was_made() -> None:
    contract, sealed = split(("E-h1", held("E-h1")), ("E-h2", held("E-h2")))
    batch = batch_of(contract, sealed)
    assert read_batch(batch_bytes(batch)) == batch


def test_the_canary_copies_the_held_out_example_the_seed_chooses() -> None:
    names = ("E-h1", "E-h2", "E-h3")
    contract, _ = split(*((name, held(name)) for name in names))
    chosen = random.Random(11).choice(names)  # noqa: S311 - a draw anyone can repeat
    assert make_canary(contract, 11, "E-cana", IMPOSSIBLE) == Canary("E-cana", chosen, IMPOSSIBLE)


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"not json",
        b'{"format": 1}',
        json.dumps({"format": 2, "story": "S", "seed": 1, "examples": [], "canary": {}}).encode(),
    ],
)
def test_content_that_is_not_a_batch_is_refused(content: bytes) -> None:
    with pytest.raises(RefusalError) as refused:
        read_batch(content)
    assert refused.value.finding.code == "unreadable-batch"


def test_a_batch_that_is_not_in_canonical_form_is_refused() -> None:
    contract, sealed = split(("E-h1", held("E-h1")))
    loose = json.dumps(json.loads(batch_bytes(batch_of(contract, sealed))), indent=2)
    with pytest.raises(RefusalError) as refused:
        read_batch(loose.encode())
    assert refused.value.finding.code == "unreadable-batch"


@pytest.mark.parametrize("expected", ["", "0123", "z" * 32, IMPOSSIBLE.upper()])
def test_a_canary_without_32_hexadecimal_digits_is_refused(expected: str) -> None:
    contract, sealed = split(("E-h1", held("E-h1")))
    batch = batch_of(contract, sealed)
    wrong = dataclasses.replace(batch, canary=Canary("E-cana", "E-h1", expected))
    with pytest.raises(RefusalError) as refused:
        read_batch(batch_bytes(wrong))
    assert refused.value.finding.code == "unreadable-batch"


@pytest.mark.parametrize(
    ("field", "value"),
    [("story", 5), ("seed", -1), ("seed", True), ("salt", "zz"), ("text", 3), ("expected", 7)],
)
def test_a_batch_with_a_field_of_the_wrong_kind_is_refused(field: str, value: object) -> None:
    contract, sealed = split(("E-h1", held("E-h1")))
    data = json.loads(batch_bytes(batch_of(contract, sealed)))
    if field in ("story", "seed"):
        data[field] = value
    elif field == "expected":
        data["canary"][field] = value
    else:
        data["examples"][0][field] = value
    with pytest.raises(RefusalError) as refused:
        read_batch(canonical(data).encode())
    assert refused.value.finding.code == "unreadable-batch"


@pytest.mark.parametrize(("key", "value"), [("format", 2), ("extra", "field")])
def test_a_whole_batch_of_another_format_or_with_another_field_is_refused(
    key: str, value: object
) -> None:
    contract, sealed = split(("E-h1", held("E-h1")))
    data = json.loads(batch_bytes(batch_of(contract, sealed)))
    data[key] = value
    with pytest.raises(RefusalError) as refused:
        read_batch(canonical(data).encode())
    assert refused.value.finding.code == "unreadable-batch"


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("order",), ["E-p0", 3]),
        (("kept_visible",), "E-p0"),
        (("without_holdout", 0, "reason"), "no-reason"),
        (("without_holdout", 0, "case"), 4),
    ],
)
def test_a_batch_whose_split_fields_are_of_the_wrong_kind_is_refused(
    path: tuple[object, ...], value: object
) -> None:
    contract, sealed = split(("E-h1", held("E-h1")))
    data = json.loads(batch_bytes(batch_of(contract, sealed)))
    place = data
    for step in path[:-1]:
        place = place[step]
    place[path[-1]] = value
    with pytest.raises(RefusalError) as refused:
        read_batch(canonical(data).encode())
    assert refused.value.finding.code == "unreadable-batch"
