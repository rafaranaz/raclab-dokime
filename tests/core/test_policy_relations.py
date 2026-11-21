# SDD-EARS: CORE-190 CORE-113 CORE-116
import pytest

from dokime.core.policy import DEFAULTS, read_policy


def codes(text: str) -> list[tuple[str, tuple[int, ...]]]:
    return [(finding.code, finding.lines) for finding in read_policy(text).findings]


def test_the_permutations_of_the_relations_are_ten_by_default() -> None:
    assert DEFAULTS.relations_permutations == 10
    read = read_policy("format: 1\nrelations: {}\n").policy
    assert read is not None
    assert read.relations_permutations == 10


@pytest.mark.parametrize("permutations", [1, 3, 120])
def test_the_permutations_of_the_relations_are_read(permutations: int) -> None:
    read = read_policy(f"format: 1\nrelations:\n  permutations: {permutations}\n")
    assert read.findings == ()
    assert read.policy is not None
    assert read.policy.relations_permutations == permutations
    assert read.policy.normalised()["relations"] == {"permutations": permutations}


@pytest.mark.parametrize("permutations", [0, -1])
def test_fewer_than_one_permutation_is_refused_naming_the_field(permutations: int) -> None:
    text = f"format: 1\nrelations:\n  permutations: {permutations}\n"
    assert codes(text) == [("wrong-type", (3,))]
    assert "permutations" in read_policy(text).findings[0].message
    assert read_policy(text).policy is None


@pytest.mark.parametrize(
    ("text", "found"),
    [
        ("format: 1\nrelations: 2\n", [("wrong-type", (2,))]),
        ("format: 1\nrelations:\n  permutations: '3'\n", [("wrong-type", (3,))]),
        ("format: 1\nrelations:\n  permutations: true\n", [("wrong-type", (3,))]),
        ("format: 1\nrelations:\n  permutations: 3\n  seed: 1\n", [("unknown-field", (4,))]),
    ],
    ids=["not-a-mapping", "a-text", "a-boolean", "unknown-field"],
)
def test_a_section_of_relations_out_of_its_table_is_refused(
    text: str, found: list[tuple[str, tuple[int, ...]]]
) -> None:
    assert codes(text) == found
