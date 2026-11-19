# SDD-EARS: CORE-186 CORE-187 CORE-188 CORE-189
from dataclasses import fields
from typing import get_type_hints

from dokime.core.repository import CommitName, FileHistory, FileVersion, RepoPath


def test_the_port_offers_one_operation_the_versions_of_a_path() -> None:
    public = {name for name in vars(FileHistory) if not name.startswith("_")}
    assert public == {"versions"}


def test_the_versions_receive_the_commit_to_start_from_and_the_path() -> None:
    hints = get_type_hints(FileHistory.versions)
    assert (hints["start"], hints["path"]) == (CommitName, RepoPath)
    assert hints["return"] == tuple[FileVersion, ...]


def test_a_version_carries_the_commit_and_the_bytes_of_the_file() -> None:
    assert {f.name: f.type for f in fields(FileVersion)} == {
        "commit": CommitName,
        "content": bytes,
    }
    version = FileVersion(CommitName("a" * 40), b"format: 1\n")
    assert (version.commit.text, version.content) == ("a" * 40, b"format: 1\n")


def test_the_operation_says_the_order_and_what_it_leaves_out() -> None:
    said = " ".join((FileHistory.versions.__doc__ or "").split())
    assert "newest first" in said
    assert "every commit reachable from `start` that changes the path" in said
    assert "renames are not followed" in said
    assert "a commit where the path is absent gives no version" in said
