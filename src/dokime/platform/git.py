"""The adapter of the project repository that runs the `git` command.

The adapter keeps a bare repository of its own in the work directory. That repository reads the
objects of the project as alternates and holds the objects the adapter writes. Every command but
the few that read facts of the project runs there, with no configuration of the person, so that
neither the attributes nor the configuration of the project change a composition or an extraction.
"""

import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Callable, Iterator, Mapping
from pathlib import Path

from dokime.core.repository import (
    Change,
    CommitName,
    HistoryCommit,
    RefusalError,
    RepoPath,
    TreeName,
)

MINIMUM_VERSION = (2, 41)
"""The first version of git with `--attr-source`."""

_EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
_SUBMODULE = b"160000"
_VERSION = re.compile(r"git version (\d+)\.(\d+)")
_PROTECTIONS = ("-c", "core.protectNTFS=true", "-c", "core.protectHFS=true")
"""The checks of git against names that NTFS or HFS take as `.git`, on whatever their defaults."""

_SETTINGS = (
    "-c",
    "core.autocrlf=false",
    "-c",
    "core.eol=lf",
    "-c",
    "core.symlinks=true",
    f"--attr-source={_EMPTY_TREE}",
)


def _environment(extra: Mapping[str, str]) -> dict[str, str]:
    environment = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    environment |= {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "LC_ALL": "C",
    }
    return environment | dict(extra)


def _is_empty_directory(path: Path) -> bool:
    return path.is_dir() and not path.is_symlink() and next(path.iterdir(), None) is None


def _does_not_apply(said: bytes) -> RefusalError:
    text = said.decode(errors="replace").strip() or "no message"
    return RefusalError("patch-does-not-apply", f"git apply refused the patch: {text}")


def _path(raw: bytes) -> RepoPath:
    try:
        return RepoPath.from_bytes(raw)
    except ValueError:
        raise RefusalError("path-not-utf8", f"the path {raw!r} is not valid UTF-8") from None


class GitRepository:
    """The project repository, read through the `git` command.

    The adapter holds a temporary directory until it is closed; use it in a `with` block.
    """

    def __init__(self, project: Path, *, git: str = "git") -> None:
        found = shutil.which(git)
        if found is None:
            raise RefusalError("git-not-found", f"no executable program {git!r} was found")
        self.git_path = Path(found).resolve()
        """The absolute path of the git that every command runs."""
        self._git = str(self.git_path)
        self.git_version = self._check_version()
        """The version of that git, as it gives it."""
        objects = self._open(project.absolute())
        self._work = Path(tempfile.mkdtemp(prefix="dokime-git-"))
        try:
            self._run(
                "init",
                "--quiet",
                "--bare",
                "--template=",
                "--object-format=sha1",
                str(self._work),
                git_dir=False,
            )
            (self._work / "objects" / "info" / "alternates").write_text(f"{objects}\n")
        except BaseException:
            shutil.rmtree(self._work)
            raise

    def close(self) -> None:
        """Remove the temporary directory of the adapter, with every object it wrote."""
        if self._work.exists():
            shutil.rmtree(self._work)

    def __enter__(self) -> "GitRepository":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def history(self, start: CommitName) -> tuple[HistoryCommit, ...]:
        """Give every commit reachable from `start`, with its committer date and its parents."""
        self._commit(start)
        commits = []
        for line in self._run("log", "--format=%H %ct %P", start.text).decode().splitlines():
            name, date, *parents = line.split()
            commits.append(
                HistoryCommit(
                    name=CommitName(name),
                    date=int(date),
                    parents=tuple(CommitName(parent) for parent in parents),
                )
            )
        return tuple(commits)

    def change(self, commit: CommitName) -> Change:
        """Give the paths that differ between a commit and its one parent, renames as two."""
        self._commit(commit)
        parents = self._run("log", "-1", "--format=%P", commit.text).decode().split()
        if len(parents) != 1:
            raise RefusalError(
                "not-one-parent",
                f"the commit {commit.text} has {len(parents)} parents, not one",
            )
        listed = self._run(
            "diff-tree", "-r", "-z", "--no-renames", "--name-only", parents[0], commit.text
        )
        paths = tuple(_path(raw) for raw in listed.split(b"\0") if raw)
        return Change(commit=commit, parent=CommitName(parents[0]), paths=paths)

    def compose_with_paths(
        self, base: CommitName, source: CommitName, take: Callable[[RepoPath], bool]
    ) -> TreeName:
        """Compose the tree of `base` with, under the paths `take` accepts, the files of
        `source`."""
        self._commit(base)
        self._commit(source)
        return self._compose(base.text, source.text, take)

    def _compose(self, base: str, source: str, take: Callable[[RepoPath], bool]) -> TreeName:
        """The tree of `base` without what `take` accepts, and with that of `source`."""
        kept = [record for path, record in self._records(base) if not take(path)]
        taken = [record for path, record in self._records(source) if take(path)]
        with self._index() as index:
            self._run("update-index", "-z", "--index-info", data=b"".join(kept + taken), env=index)
            name = self._run("write-tree", env=index).decode().strip()
        return TreeName(name)

    def compose_tree_with_paths(
        self, tree: TreeName, source: CommitName, take: Callable[[RepoPath], bool]
    ) -> TreeName:
        """Compose `tree` with the paths of `source` that `take` accepts (ADR-0058).

        The region the rule takes is replaced, not overlaid: a file of `tree` under it that
        `source` does not have, such as a `conftest.py` that a patch added, is not in the result.
        """
        kind = self._try("cat-file", "-t", tree.text)
        if kind is None or kind.strip() != b"tree":
            raise RefusalError("unknown-tree", f"the tree {tree.text} cannot be read")
        self._commit(source)
        return self._compose(tree.text, source.text, take)

    def compose_with_patch(self, base: CommitName, patch: bytes) -> TreeName:
        """Compose the tree of `base` with a patch applied, in the repository of the adapter.

        The patch is applied to an index of its own, never to a working tree, and a path with a
        part `.git` in any case of letters is refused before anything is applied.
        """
        self._commit(base)
        for path in self._patched_paths(patch):
            if any(part.casefold() == ".git" for part in path.split("/")):
                raise RefusalError(
                    "patch-touches-git", f"the patch names the path {path!r}, which is under .git"
                )
        with self._index() as index:
            self._run("read-tree", base.text, env=index)
            applied = self._call((*_PROTECTIONS, "apply", "--cached", "-"), True, patch, index)
            if applied.returncode != 0:
                raise _does_not_apply(applied.stderr)
            name = self._run("write-tree", env=index).decode().strip()
        return TreeName(name)

    def _patched_paths(self, patch: bytes) -> list[str]:
        """The paths a patch writes, as git reads them; for a rename, git gives the new path.

        The old path of a rename or a deletion is a path of the base, which a tree of git never
        holds under `.git`.
        """
        listed = self._call(("apply", "--numstat", "-z", "-"), True, patch, {})
        if listed.returncode != 0:
            raise _does_not_apply(listed.stderr)
        records = (record for record in listed.stdout.split(b"\0") if record)
        return [record.split(b"\t", 2)[2].decode("utf-8", errors="replace") for record in records]

    def extract(self, tree: TreeName, directory: Path) -> None:
        """Write the tree to an empty directory, each file with the bytes of its blob."""
        if not _is_empty_directory(directory):
            raise ValueError(f"the directory {directory} is not an empty directory")
        kind = self._try("cat-file", "-t", tree.text)
        if kind is None or kind.strip() != b"tree":
            raise RefusalError("unknown-tree", f"the tree {tree.text} cannot be read")
        for record in self._listing(tree.text):
            if record.startswith(_SUBMODULE + b" "):
                path = record.split(b"\t", 1)[1]
                raise RefusalError(
                    "submodule-in-tree", f"the tree {tree.text} holds the submodule {path!r}"
                )
        with self._index() as index:
            self._run("read-tree", tree.text, env=index)
            work_tree = {"GIT_WORK_TREE": str(directory.absolute())}
            self._run("checkout-index", "--all", env=index | work_tree)

    def _check_version(self) -> str:
        try:
            done = subprocess.run(
                [self._git, "--version"], capture_output=True, env=_environment({}), check=False
            )
        except OSError as error:
            raise RefusalError("git-not-found", f"git cannot be run: {error}") from None
        version = done.stdout.decode(errors="replace").strip()
        found = _VERSION.match(version)
        if not found or (int(found[1]), int(found[2])) < MINIMUM_VERSION:
            raise RefusalError(
                "git-too-old", f"git gave the version {version!r}; it needs 2.41 or later"
            )
        return version.removeprefix("git version ")

    def _open(self, project: Path) -> str:
        """Check the facts of the project and give the absolute path of its objects."""
        facts = {"GIT_CEILING_DIRECTORIES": str(project.parent)}

        def ask(*args: str) -> str | None:
            found = self._try("-C", str(project), "rev-parse", *args, git_dir=False, env=facts)
            return None if found is None else found.decode().strip()

        top = ask("--show-toplevel")
        if top is None or Path(top) != project.resolve():
            raise RefusalError("not-a-repository", f"{project} is not a git repository")
        if ask("--show-object-format") != "sha1":
            raise RefusalError(
                "sha256-repository", f"the repository {project} does not name its objects in SHA-1"
            )
        if ask("--is-shallow-repository") != "false":
            raise RefusalError("shallow-clone", f"the repository {project} is a shallow clone")
        objects = ask("--path-format=absolute", "--git-path", "objects")
        if objects is None:
            raise RefusalError("not-a-repository", f"{project} has no objects directory")
        return objects

    def _commit(self, commit: CommitName) -> None:
        if self._try("rev-parse", "--verify", "--quiet", f"{commit.text}^{{commit}}") is None:
            raise RefusalError("unknown-commit", f"{commit.text} is not a commit of the project")

    def _listing(self, treeish: str) -> list[bytes]:
        listed = self._run("ls-tree", "-r", "-z", "--full-tree", treeish)
        return [record for record in listed.split(b"\0") if record]

    def _records(self, treeish: str) -> Iterator[tuple[RepoPath, bytes]]:
        """Each entry of a tree with its path, as a record that `update-index` reads."""
        for record in self._listing(treeish):
            yield _path(record.split(b"\t", 1)[1]), record + b"\0"

    def _index(self) -> "_Index":
        return _Index(self._work)

    def _try(
        self,
        *args: str,
        git_dir: bool = True,
        data: bytes | None = None,
        env: Mapping[str, str] = {},
    ) -> bytes | None:
        done = self._call(args, git_dir, data, env)
        return done.stdout if done.returncode == 0 else None

    def _run(
        self,
        *args: str,
        git_dir: bool = True,
        data: bytes | None = None,
        env: Mapping[str, str] = {},
    ) -> bytes:
        done = self._call(args, git_dir, data, env)
        if done.returncode != 0:
            said = done.stderr.decode(errors="replace").strip()
            raise RefusalError("git-failed", f"git {args[0]} failed: {said or 'no message'}")
        return done.stdout

    def _call(
        self, args: tuple[str, ...], git_dir: bool, data: bytes | None, extra: Mapping[str, str]
    ) -> subprocess.CompletedProcess[bytes]:
        place = {"GIT_DIR": str(self._work)} if git_dir else {}
        return subprocess.run(
            [self._git, *_SETTINGS, *args],
            input=data,
            capture_output=True,
            env=_environment(place | dict(extra)),
            check=False,
        )


class _Index:
    """A throwaway index file in the work directory, removed on exit."""

    def __init__(self, work: Path) -> None:
        self._work = work

    def __enter__(self) -> dict[str, str]:
        descriptor, name = tempfile.mkstemp(prefix="index-", dir=self._work)
        os.close(descriptor)
        os.unlink(name)
        self._name = name
        return {"GIT_INDEX_FILE": name}

    def __exit__(self, *_: object) -> None:
        Path(self._name).unlink(missing_ok=True)
        Path(f"{self._name}.lock").unlink(missing_ok=True)
