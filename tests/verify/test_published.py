# SDD-EARS: VERIFY-169 VERIFY-170
from dokime.core.repository import CommitName, FileVersion
from dokime.verify.published import example_items, published
from tests.verify.sealed_contracts import HEADER, held

ONE = CommitName("1" * 40)


def version(examples: str, held_out: str = "") -> FileVersion:
    text = HEADER + "examples:\n" + examples + (f"held_out:\n{held_out}" if held_out else "")
    return FileVersion(ONE, text.encode())


def items(*texts: str) -> tuple[dict[str, object], ...]:
    return example_items(HEADER + "examples:\n" + "".join(texts))


def test_the_examples_of_a_contract_are_read_from_its_list_of_examples() -> None:
    read = items(held("E-a1"), held("E-a2"))
    assert [item["id"] for item in read] == ["E-a1", "E-a2"]
    assert read[0]["boundary"] == "function"


def test_a_text_without_a_list_of_examples_has_none() -> None:
    assert example_items("format: 1\nexamples: none\n") == ()
    assert example_items("- just a list\n") == ()


def test_an_example_with_an_id_in_a_version_is_published() -> None:
    other = held("E-a1").replace("args: [", "args: [1, ")
    assert published(items(held("E-a1"), held("E-a2")), [version(other)]) == {"E-a1"}


def test_an_example_with_the_content_of_one_in_a_version_is_published() -> None:
    same = held("E-a1").replace("id: E-a1", "id: E-old")
    assert published(items(held("E-a1"), held("E-a2")), [version(same)]) == {"E-a1"}


def test_an_example_neither_by_id_nor_by_content_in_a_version_is_not_published() -> None:
    assert published(items(held("E-a1")), [version(held("E-b1"))]) == frozenset()


def test_the_entries_of_held_out_of_a_version_do_not_publish_an_example() -> None:
    stub = (
        "  - id: E-a1\n    requirement: R-new\n    case: c\n    digest: sha256:" + "0" * 64 + "\n"
    )
    assert published(items(held("E-a1")), [version(held("E-b1"), stub)]) == frozenset()


def test_every_version_counts() -> None:
    versions = [version(held("E-b1")), version(held("E-a2"))]
    assert published(items(held("E-a1"), held("E-a2")), versions) == {"E-a2"}


def test_an_example_of_a_version_without_an_id_still_publishes_by_content() -> None:
    nameless = held("E-a1").replace("  - id: E-a1\n    requirement", "  - requirement")
    assert published(items(held("E-a1")), [version(nameless)]) == {"E-a1"}
