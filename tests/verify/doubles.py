"""A double of the port of the audited repository, held in memory, for the tests of verify.

A file is its bytes, an executable file `("x", bytes)` and a link `("->", target)`. A patch is the
JSON of the files it sets and the paths it removes, since the double reads no patch of git.
"""

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from dokime.core.repository import (
    Change,
    CommitName,
    HistoryCommit,
    RefusalError,
    RepoPath,
    TreeName,
)

Entry = bytes | tuple[str, bytes] | tuple[str, str]
Files = dict[str, Entry]


def _name(files: Files) -> str:
    text = json.dumps(sorted((path, repr(entry)) for path, entry in files.items()))
    return hashlib.sha1(text.encode(), usedforsecurity=False).hexdigest()


def patch(
    sets: dict[str, str | tuple[str, str]] | None = None, removes: list[str] | None = None
) -> bytes:
    """The patch of the double: the files it sets, as texts, and the paths it removes."""
    return json.dumps({"set": sets or {}, "remove": removes or []}).encode()


@dataclass
class AuditedDouble:
    """The audited repository in memory."""

    commits: dict[CommitName, Files] = field(default_factory=dict)
    trees: dict[TreeName, Files] = field(default_factory=dict)

    def add(self, files: Files) -> CommitName:
        name = CommitName(_name(files))
        self.commits[name] = dict(files)
        return name

    def _tree(self, files: Files) -> TreeName:
        name = TreeName(_name({**files, "\0tree": b""}))
        self.trees[name] = dict(files)
        return name

    def history(self, start: CommitName) -> tuple[HistoryCommit, ...]:
        raise NotImplementedError

    def change(self, commit: CommitName) -> Change:
        raise NotImplementedError

    def compose_with_paths(
        self, base: CommitName, source: CommitName, take: Callable[[RepoPath], bool]
    ) -> TreeName:
        kept = {p: e for p, e in self.commits[base].items() if not take(RepoPath(p))}
        taken = {p: e for p, e in self.commits[source].items() if take(RepoPath(p))}
        return self._tree(kept | taken)

    def compose_with_patch(self, base: CommitName, patch: bytes) -> TreeName:
        given = json.loads(patch)
        files = dict(self.commits[base])
        for path in given["remove"]:
            if path not in files:
                raise RefusalError("patch-does-not-apply", f"{path} is not in the base")
            del files[path]
        for path, entry in given["set"].items():
            files[path] = tuple(entry) if isinstance(entry, list) else entry.encode()
        return self._tree(files)

    def compose_tree_with_paths(
        self, tree: TreeName, source: CommitName, take: Callable[[RepoPath], bool]
    ) -> TreeName:
        kept = {p: e for p, e in self.trees[tree].items() if not take(RepoPath(p))}
        taken = {p: e for p, e in self.commits[source].items() if take(RepoPath(p))}
        return self._tree(kept | taken)

    def extract(self, tree: TreeName, directory: Path) -> None:
        for path, entry in self.trees[tree].items():
            target = directory / PurePosixPath(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(entry, tuple) and entry[0] == "->":
                target.symlink_to(str(entry[1]))
            elif isinstance(entry, tuple):
                target.write_bytes(entry[1] if isinstance(entry[1], bytes) else entry[1].encode())
                target.chmod(0o755)
            else:
                target.write_bytes(entry)
