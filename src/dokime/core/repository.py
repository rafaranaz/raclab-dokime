"""The port of the project repository and the values it exchanges.

`core` defines what the port gives and takes; it runs no `git`. What an adapter does with a real
repository, and when it refuses, belongs to the adapters.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from dokime.core.findings import Finding
from dokime.core.verdicts import Verdict

_NAME = re.compile(r"[0-9a-f]{40}")


def _check_name(text: str) -> None:
    if not _NAME.fullmatch(text):
        raise ValueError(f"the name {text!r} is not 40 lowercase hexadecimal characters")


@dataclass(frozen=True)
class CommitName:
    """The name of a commit: its SHA-1 as 40 lowercase hexadecimal characters."""

    text: str

    def __post_init__(self) -> None:
        _check_name(self.text)


@dataclass(frozen=True)
class TreeName:
    """The name of a tree: its SHA-1 as 40 lowercase hexadecimal characters.

    It is never equal to a commit name, even with the same text.
    """

    text: str

    def __post_init__(self) -> None:
        _check_name(self.text)


@dataclass(frozen=True)
class RepoPath:
    """A path inside the repository: relative, its parts separated by `/`."""

    text: str

    def __post_init__(self) -> None:
        parts = self.text.split("/")
        if "\0" in self.text or any(part in ("", ".", "..") for part in parts):
            raise ValueError(
                f"the path {self.text!r} is not a relative path of non-empty parts other than"
                " '.' and '..', without NUL"
            )

    @classmethod
    def from_bytes(cls, raw: bytes) -> "RepoPath":
        """Make a path from the bytes a repository stores, decoded as UTF-8."""
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError(f"the path {raw!r} is not valid UTF-8") from None
        return cls(text)


@dataclass(frozen=True)
class HistoryCommit:
    """A commit of the history: its date in whole seconds and its parents in the order it names
    them."""

    name: CommitName
    date: int
    parents: tuple[CommitName, ...]


@dataclass(frozen=True)
class Change:
    """What a commit with one parent changed: the paths that differ from that parent."""

    commit: CommitName
    parent: CommitName
    paths: tuple[RepoPath, ...]


class RefusalError(Exception):
    """An adapter cannot do an operation. It carries a finding with the verdict `ERROR`.

    The code and the message are checked as those of any finding.
    """

    def __init__(self, code: str, message: str) -> None:
        self.finding = Finding(code=code, message=message, verdict=Verdict.ERROR)
        super().__init__(message)


class ProjectRepository(Protocol):
    """The port of the project repository. Every operation may raise a `RefusalError`."""

    def history(self, start: CommitName) -> tuple[HistoryCommit, ...]:
        """Give every commit reachable from `start`."""
        ...

    def change(self, commit: CommitName) -> Change:
        """Give the change of a commit against its one parent."""
        ...

    def compose_with_paths(
        self, base: CommitName, source: CommitName, take: Callable[[RepoPath], bool]
    ) -> TreeName:
        """Compose the tree of `base` with the paths of `source` that `take` accepts."""
        ...

    def compose_with_patch(self, base: CommitName, patch: bytes) -> TreeName:
        """Compose the tree of `base` with a patch applied."""
        ...

    def extract(self, tree: TreeName, directory: Path) -> None:
        """Write the tree to a directory, byte for byte."""
        ...
