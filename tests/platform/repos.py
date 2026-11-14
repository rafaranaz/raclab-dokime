"""Repositories built for the tests of the git adapter, with git plumbing and fixed dates."""

import os
import subprocess
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

import pytest

from dokime.core.findings import Finding
from dokime.core.repository import RefusalError

REGULAR = "100644"
EXECUTABLE = "100755"
LINK = "120000"
SUBMODULE = "160000"


@dataclass(frozen=True)
class Entry:
    """One entry of a tree: its path as git stores it, its mode and its blob or commit."""

    path: bytes
    mode: str
    data: bytes


def file(path: str | bytes, data: bytes, mode: str = REGULAR) -> Entry:
    return Entry(path.encode() if isinstance(path, str) else path, mode, data)


def link(path: str, target: str) -> Entry:
    return Entry(path.encode(), LINK, target.encode())


def submodule(path: str, commit: str) -> Entry:
    return Entry(path.encode(), SUBMODULE, commit.encode())


def clean_environment(extra: Mapping[str, str] = {}) -> dict[str, str]:
    """The environment of the person without any variable of git, and without their
    configuration."""
    environment = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    environment |= {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "LC_ALL": "C"}
    return environment | dict(extra)


class Project:
    """A git repository with a working tree, written only through plumbing."""

    def __init__(self, path: Path, *, object_format: str = "sha1") -> None:
        self.path = path
        path.mkdir(parents=True)
        self.git("init", "--quiet", "--initial-branch=main", f"--object-format={object_format}")

    def git(self, *args: str, data: bytes | None = None, env: Mapping[str, str] = {}) -> bytes:
        done = subprocess.run(
            ["git", "-C", str(self.path), *args],
            input=data,
            capture_output=True,
            env=clean_environment(env),
            check=False,
        )
        assert done.returncode == 0, done.stderr.decode(errors="replace")
        return done.stdout

    def text(self, *args: str) -> str:
        return self.git(*args).decode().strip()

    def tree(self, entries: Iterable[Entry]) -> str:
        """Write a tree with these entries and give its name."""
        lines = []
        for entry in entries:
            if entry.mode == SUBMODULE:
                name = entry.data.decode()
            else:
                name = (
                    self.git("hash-object", "-w", "--no-filters", "--stdin", data=entry.data)
                    .decode()
                    .strip()
                )
            lines.append(entry.mode.encode() + b" " + name.encode() + b"\t" + entry.path + b"\0")
        index = {"GIT_INDEX_FILE": str(self.path / ".git" / "test-index")}
        (self.path / ".git" / "test-index").unlink(missing_ok=True)
        self.git("update-index", "-z", "--index-info", data=b"".join(lines), env=index)
        name = self.git("write-tree", "--missing-ok", env=index).decode().strip()
        (self.path / ".git" / "test-index").unlink()
        return name

    def commit(
        self,
        entries: Iterable[Entry],
        *parents: str,
        date: int = 1_700_000_000,
        author_date: int | None = None,
    ) -> str:
        """Write a commit of a tree with these entries and these parents, and point main at it."""
        tree = self.tree(entries)
        dates = {
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.invalid",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@example.invalid",
            "GIT_AUTHOR_DATE": f"@{date if author_date is None else author_date} +0000",
            "GIT_COMMITTER_DATE": f"@{date} +0000",
        }
        arguments = [arg for parent in parents for arg in ("-p", parent)]
        name = self.git("commit-tree", tree, *arguments, "-m", "c", env=dates).decode().strip()
        self.git("update-ref", "refs/heads/main", name)
        return name

    def tree_of(self, commit: str) -> str:
        return self.text("rev-parse", f"{commit}^{{tree}}")

    def entries(self, tree: str) -> set[tuple[str, str, bytes]]:
        """The mode, the object and the path of every entry of a tree, recursively."""
        found = set()
        for record in self.git("ls-tree", "-r", "-z", "--full-tree", tree).split(b"\0"):
            if record:
                head, path = record.split(b"\t", 1)
                mode, _, name = head.decode().split(" ")
                found.add((mode, name, path))
        return found

    def blob(self, name: str) -> bytes:
        return self.git("cat-file", "blob", name)


def refusal(action: Callable[[], object]) -> Finding:
    """The finding of the refusal that an action raises."""
    with pytest.raises(RefusalError) as info:
        action()
    return info.value.finding


def snapshot(directory: Path) -> dict[str, tuple[int, bytes]]:
    """The mode and the bytes of every file under a directory, by relative path."""
    found = {}
    for root, _, names in os.walk(directory):
        for name in names:
            path = Path(root) / name
            relative = str(path.relative_to(directory))
            if path.is_symlink():
                found[relative] = (path.lstat().st_mode, os.readlink(path).encode())
            else:
                found[relative] = (path.stat().st_mode, path.read_bytes())
    return found
