"""The inputs of an audit: the contract, the pack and the policy.

They come from the tree of the base commit, extracted into a directory of its own, or from files
given from outside the patch, never from the patch: the contract is the judge of the change, and
the pack says what is protected. A file of an extracted tree is opened part by part without
following a link, and read up to a bound, since a patch or the base can bring a link that points
outside the tree. A file given from outside is the person's, and is read as it is.
"""

import errno
import os
import stat
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from dokime.contract.check import check as check_contract
from dokime.contract.model import Contract
from dokime.core.findings import Finding
from dokime.core.layout import HARNESS, POLICY, contract_path
from dokime.core.policy import Policy, read_policy
from dokime.core.repository import RefusalError
from dokime.core.verdicts import Verdict
from dokime.packs.check import check as check_pack
from dokime.packs.model import Pack

TREE_FILE_BYTES = 1024 * 1024
"""The bytes a file of an extracted tree may have."""
PACK = HARNESS / "pack.yaml"
"""The pack in the tree of a project."""


@dataclass(frozen=True)
class ContractRead:
    """The contract read and its bytes, or none, and the findings of the contract."""

    findings: tuple[Finding, ...]
    contract: Contract | None = None
    text: bytes | None = None


@dataclass(frozen=True)
class PackRead:
    """The pack read, its bytes and those of its Dockerfile, or none, and the findings."""

    findings: tuple[Finding, ...]
    pack: Pack | None = None
    text: bytes | None = None
    dockerfile: bytes | None = None


@dataclass(frozen=True)
class PolicyRead:
    """The effective policy, or none, and the findings of its file."""

    findings: tuple[Finding, ...]
    policy: Policy | None = None


def read_in_tree(tree: Path, path: PurePosixPath) -> bytes:
    """The bytes of a file of an extracted tree, opened without following a link."""
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise RefusalError("path-outside-tree", f"the path {str(path)!r} leaves the tree")
    directory = os.open(tree, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        *parents, name = path.parts
        for part in parents:
            opened = _open_part(part, directory, path, os.O_DIRECTORY)
            os.close(directory)
            directory = opened
        descriptor = _open_part(name, directory, path, os.O_NONBLOCK)
    finally:
        os.close(directory)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise _not_regular(path, "it is not a regular file")
        data = _read_bounded(descriptor)
    finally:
        os.close(descriptor)
    if len(data) > TREE_FILE_BYTES:
        raise RefusalError(
            "file-too-large", f"the file {path} of the tree has more than {TREE_FILE_BYTES} bytes"
        )
    return data


def read_contract(
    tree: Path, *, story: str | None = None, outside: Path | None = None
) -> ContractRead:
    """The contract of the story in the tree, or of the file given from outside the patch."""
    if outside is not None:
        data = _outside(outside)
        directory = outside.parent.name
    else:
        if story is None:
            raise ValueError("a contract is read for a story or from a file, and neither was given")
        try:
            path = contract_path(story)
        except ValueError:
            return ContractRead(
                findings=(
                    _error(
                        "not-a-story",
                        f"the story {story!r} is not a name: letters and digits in words joined"
                        " by hyphens, starting with a letter",
                    ),
                )
            )
        data = _in_tree(tree, PurePosixPath(path))
        directory = story
    if isinstance(data, Finding):
        return ContractRead(findings=(data,))
    text = _text(data)
    if isinstance(text, Finding):
        return ContractRead(findings=(text,))
    checked = check_contract(text)
    contract = checked.contract
    if contract is not None and contract.story != directory:
        mismatch = _error(
            "story-not-directory",
            f"the story of the contract is {contract.story!r} and its directory is {directory!r}",
        )
        return ContractRead(findings=(*checked.findings, mismatch), text=data)
    return ContractRead(findings=checked.findings, contract=contract, text=data)


def read_pack(tree: Path, outside: Path | None = None) -> PackRead:
    """The pack of the tree with its Dockerfile, or those of the file given from outside."""
    beside: Callable[[PurePosixPath], bytes | Finding]
    if outside is None:
        data = _in_tree(tree, PACK)
        beside = lambda name: _in_tree(tree, PACK.parent / name)  # noqa: E731
    else:
        data = _outside(outside)
        beside = lambda name: _outside(outside.parent / name)  # noqa: E731
    if isinstance(data, Finding):
        return PackRead(findings=(data,))
    text = _text(data)
    if isinstance(text, Finding):
        return PackRead(findings=(text,))
    checked = check_pack(text)
    if checked.pack is None:
        return PackRead(findings=checked.findings)
    dockerfile = beside(PurePosixPath(checked.pack.dockerfile))
    if isinstance(dockerfile, Finding):
        return PackRead(findings=(*checked.findings, dockerfile))
    return PackRead(findings=checked.findings, pack=checked.pack, text=data, dockerfile=dockerfile)


def read_tree_policy(tree: Path) -> PolicyRead:
    """The policy of the tree, or its defaults when the tree has no policy file."""
    try:
        data = read_in_tree(tree, PurePosixPath(POLICY))
    except RefusalError as refusal:
        if refusal.finding.code == "file-missing":
            return PolicyRead(findings=(), policy=Policy())
        return PolicyRead(findings=(refusal.finding,))
    text = _text(data)
    if isinstance(text, Finding):
        return PolicyRead(findings=(text,))
    checked = read_policy(text)
    return PolicyRead(findings=checked.findings, policy=checked.policy)


def _open_part(part: str, directory: int, path: PurePosixPath, flags: int) -> int:
    try:
        return os.open(part, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | flags, dir_fd=directory)
    except FileNotFoundError:
        raise RefusalError("file-missing", f"the tree has no file {path}") from None
    except OSError as error:
        if error.errno in (errno.ELOOP, errno.ENOTDIR):
            raise _not_regular(path, f"{part!r} is a link or not a directory") from None
        raise RefusalError(
            "unreadable-file", f"the file {path} of the tree cannot be read: {error.strerror}"
        ) from None


def _not_regular(path: PurePosixPath, why: str) -> RefusalError:
    return RefusalError("file-not-regular", f"the file {path} of the tree is not regular: {why}")


def _read_bounded(descriptor: int) -> bytes:
    chunks: list[bytes] = []
    size = 0
    while size <= TREE_FILE_BYTES:
        chunk = os.read(descriptor, TREE_FILE_BYTES + 1 - size)
        if not chunk:
            break
        chunks.append(chunk)
        size += len(chunk)
    return b"".join(chunks)


def _in_tree(tree: Path, path: PurePosixPath) -> bytes | Finding:
    try:
        return read_in_tree(tree, path)
    except RefusalError as refusal:
        return refusal.finding


def _outside(path: Path) -> bytes | Finding:
    try:
        return path.read_bytes()
    except OSError as error:
        reason = error.strerror or type(error).__name__
        return _error("unreadable-file", f"the file {path} cannot be read: {reason}")


def _text(data: bytes) -> str | Finding:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return _error("unreadable-file", "the file cannot be read: it is not UTF-8 text")


def _error(code: str, message: str) -> Finding:
    return Finding(code=code, message=message, verdict=Verdict.ERROR)
