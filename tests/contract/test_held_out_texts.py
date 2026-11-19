# SDD-EARS: CONTRACT-092 CONTRACT-093 CONTRACT-094
import hashlib
import json

import pytest

from dokime.contract.check import check
from dokime.contract.held_out import example_texts, held_out_digest
from tests.contract.contracts import VALID

SALT = bytes(range(16))


def test_the_digest_is_that_of_the_salt_and_the_text_in_canonical_form() -> None:
    text = "  - id: E-0001\n    requirement: r\n"
    canonical = json.dumps(
        {"salt": SALT.hex(), "text": text}, separators=(",", ":"), sort_keys=True
    )
    expected = "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()
    assert held_out_digest(SALT, text) == expected


def test_another_salt_gives_another_digest_for_the_same_text() -> None:
    text = "  - id: E-0001\n"
    assert held_out_digest(SALT, text) != held_out_digest(bytes(16), text)


@pytest.mark.parametrize("salt", [b"", bytes(15), bytes(17), bytes(32)])
def test_a_salt_that_is_not_16_bytes_is_refused(salt: bytes) -> None:
    with pytest.raises(ValueError, match="16 bytes"):
        held_out_digest(salt, "  - id: E-0001\n")


HEADER = VALID[: VALID.index("examples:")]


def test_each_example_reads_back_alone_from_its_text() -> None:
    texts = example_texts(VALID)
    checked = check(VALID)
    assert checked.contract is not None
    assert sorted(texts) == ["E-0001", "E-0002", "E-0003"]
    for example in checked.contract.examples:
        alone = check(HEADER + "examples:\n" + texts[example.id])
        assert {f.code for f in alone.findings} <= {"requirement-without-example"}, example.id
        assert alone.contract is not None
        (read,) = alone.contract.examples
        assert (read.id, read.steps, read.target, read.case) == (
            example.id,
            example.steps,
            example.target,
            example.case,
        )


def test_the_text_of_an_example_is_its_lines_as_written() -> None:
    texts = example_texts(VALID)
    assert (
        texts["E-0003"]
        == VALID[VALID.index("  - id: E-0003") : VALID.index("\nrelations:")].rstrip("\n") + "\n"
    )
    assert texts["E-0002"].startswith("  - id: E-0002\n")
    assert "E-0003" not in texts["E-0002"]


@pytest.mark.parametrize("text", ["- not a contract\n", "format: 1\nexamples: none\n", "a: [\n"])
def test_a_text_without_a_list_of_examples_gives_no_texts(text: str) -> None:
    assert example_texts(text) == {}


def test_an_example_without_an_id_gives_no_text() -> None:
    text = VALID.replace("  - id: E-0003\n", "  - name: E-0003\n")
    assert sorted(example_texts(text)) == ["E-0001", "E-0002"]
