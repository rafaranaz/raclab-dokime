# SDD-EARS: CORE-060 CORE-061 CORE-062 CORE-063 CORE-064 CORE-065 CORE-066
import re

import pytest

from dokime.core.repository import CommitName, RepoPath, TreeName

HEX = "0123456789abcdef0123456789abcdef01234567"


@pytest.mark.parametrize("kind", [CommitName, TreeName])
def test_a_name_of_forty_lowercase_hexadecimal_characters_is_accepted(
    kind: type[CommitName] | type[TreeName],
) -> None:
    assert kind(HEX).text == HEX


@pytest.mark.parametrize("kind", [CommitName, TreeName])
@pytest.mark.parametrize(
    "text",
    [
        "",
        HEX[:-1],
        HEX + "0",
        HEX.upper(),
        HEX[:-1] + "g",
        "0123456789abcdef" * 4,
        " " + HEX[1:],
    ],
)
def test_a_name_that_is_not_forty_lowercase_hexadecimal_characters_is_rejected_quoting_it(
    kind: type[CommitName] | type[TreeName], text: str
) -> None:
    with pytest.raises(ValueError, match=re.escape(repr(text))):
        kind(text)


def test_a_commit_name_is_not_equal_to_a_tree_name_with_the_same_text() -> None:
    commit: object = CommitName(HEX)
    assert commit != TreeName(HEX)


def test_two_names_of_the_same_kind_and_text_are_equal() -> None:
    assert CommitName(HEX) == CommitName(HEX)
    assert TreeName(HEX) == TreeName(HEX)


@pytest.mark.parametrize("text", ["README.md", "src/dokime/core/a.py", "a b/ñ.txt", ".github/x"])
def test_a_relative_path_with_parts_separated_by_slashes_is_accepted(text: str) -> None:
    assert RepoPath(text).text == text


@pytest.mark.parametrize(
    "text",
    ["", "/abs", "dir/", "a//b", "./a", "a/./b", "a/.", "../a", "a/../b", "a/..", "a\0b"],
)
def test_a_path_that_is_not_a_plain_relative_path_is_rejected_quoting_it(text: str) -> None:
    with pytest.raises(ValueError, match=re.escape(repr(text))):
        RepoPath(text)


def test_a_path_made_from_bytes_decodes_them_as_utf8() -> None:
    assert RepoPath.from_bytes("docs/año.md".encode()) == RepoPath("docs/año.md")


def test_a_path_made_from_bytes_follows_the_rules_of_a_path() -> None:
    with pytest.raises(ValueError, match=re.escape(repr("../a"))):
        RepoPath.from_bytes(b"../a")


@pytest.mark.parametrize("raw", [b"a\xff.txt", b"\xc3", "año".encode("latin-1")])
def test_bytes_that_are_not_utf8_are_rejected_quoting_the_bytes(raw: bytes) -> None:
    with pytest.raises(ValueError, match=re.escape(repr(raw))):
        RepoPath.from_bytes(raw)
