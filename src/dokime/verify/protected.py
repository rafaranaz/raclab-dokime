"""The gate `protected-paths` (ADR-0016, ADR-0056, ADR-0059).

A change that arrives already made is a patch on a base commit. The gate composes the tree of the
base and the tree of the base with the patch, extracts both, and compares them path by path: a file
by its bytes and whether it is executable, a link by its target, never by what it points to. A path
that differs is protected when it is a test of the pack, the configuration of its tests, or under
the directory of the harness; a mixed file only when its section differs. The contract authorises
a path of the tests or of their configuration by naming it exactly; nothing authorises the
directory of the harness.
"""

import hashlib
import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from dokime.contract.model import Contract
from dokime.core.findings import Finding
from dokime.core.repository import AuditedRepository, CommitName, RefusalError, RepoPath
from dokime.core.verdicts import Verdict
from dokime.packs.model import Pack, Section
from dokime.packs.sections import section_changed
from dokime.verify.result import GateResult

GATE = "protected-paths"
HARNESS = ".dokime"
_CHUNK = 1024 * 1024


@dataclass(frozen=True)
class _Entry:
    """A path of an extracted tree: a link and its target, or a file, its digest and its mode."""

    link: str | None
    digest: str = ""
    executable: bool = False


def protected_paths(
    pack: Pack, contract: Contract, base: CommitName, patch: bytes, repository: AuditedRepository
) -> GateResult:
    """Check that the patch touches no protected path that the contract does not authorise."""
    try:
        before_tree = repository.compose_with_paths(base, base, _nothing)
        after_tree = repository.compose_with_patch(base, patch)
    except RefusalError as refusal:
        return GateResult(gate=GATE, findings=(refusal.finding,))
    with tempfile.TemporaryDirectory(prefix="dokime-protected-") as work:
        before, after = Path(work) / "before", Path(work) / "after"
        before.mkdir()
        after.mkdir()
        repository.extract(before_tree, before)
        repository.extract(after_tree, after)
        old, new = _entries(before), _entries(after)
        changed = sorted(path for path in old.keys() | new.keys() if old.get(path) != new.get(path))
        sections = {section.file: section for section in pack.sections}
        findings = []
        for path in changed:
            why = _why(pack, contract, sections, path, before, after, old, new)
            if why:
                findings.append(
                    Finding(code="protected-path", message=f"{path} {why}", verdict=Verdict.FAIL)
                )
    return GateResult(gate=GATE, findings=tuple(findings))


def _nothing(path: RepoPath) -> bool:
    return False


def _why(
    pack: Pack,
    contract: Contract,
    sections: dict[str, Section],
    path: str,
    before: Path,
    after: Path,
    old: dict[str, _Entry],
    new: dict[str, _Entry],
) -> str:
    """Why a changed path is protected, or nothing when it is not or the contract authorises it."""
    if PurePosixPath(path).parts[0] == HARNESS:
        return "is in the directory of the harness, which no contract authorises to change"
    if path in contract.may_modify_tests:
        return ""
    if path in sections:
        section = sections[path]
        if any(
            entry is not None and entry.link is not None for entry in (old.get(path), new.get(path))
        ):
            return f"is a link where the section {section.name} of the tests is configured"
        if section_changed(section, _bytes(before, path, old), _bytes(after, path, new)):
            return f"changes the section {section.name}, which configures the tests"
        return ""
    if pack.is_test(path):
        return "is a test of the pack, and the contract does not authorise it to change"
    if pack.is_config(path):
        return "is the configuration of the tests, and the contract does not authorise it to change"
    return ""


def _entries(root: Path) -> dict[str, _Entry]:
    """Every file and link of an extracted tree, by its path, without following a link."""
    found: dict[str, _Entry] = {}
    for directory, directories, files in os.walk(root, followlinks=False):
        for name in (*directories, *files):
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                found[relative] = _Entry(link=os.readlink(path))
            elif stat.S_ISREG(mode):
                found[relative] = _Entry(
                    link=None, digest=_digest(path), executable=bool(mode & stat.S_IXUSR)
                )
    return found


def _open(path: Path) -> int:
    return os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with os.fdopen(_open(path), "rb") as handle:
        while chunk := handle.read(_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def _bytes(root: Path, path: str, entries: dict[str, _Entry]) -> bytes | None:
    if path not in entries:
        return None
    with os.fdopen(_open(root / path), "rb") as handle:
        return handle.read()
