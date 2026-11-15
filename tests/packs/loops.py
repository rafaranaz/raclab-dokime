"""Histories built for the tests of the loop of the self-check, over the doubles of the ports."""

from pathlib import Path

from dokime.core.repository import CommitName
from dokime.packs.loop import Program, SelfCheckResult, run_self_check
from tests.packs.doubles import CODE, FakeRepository, FakeRuntime, fixing_commit, pack

PROGRAMS = (
    Program(name="git", path="/usr/bin/git", version="2.47.3"),
    Program(name="podman", path="/usr/bin/podman", version="5.4.2"),
)


def root(repository: FakeRepository) -> CommitName:
    return repository.add(
        "root", 100, {CODE: b"root", "tests/test_root.py": b"expects:root", "README": b"r"}
    )


def not_a_witness(
    repository: FakeRepository, parent: CommitName, label: str, date: int
) -> CommitName:
    """A candidate whose new test fails on both sides."""
    files = dict(repository.commits[parent][2])
    files[CODE] = label.encode()
    files[f"tests/test_{label}.py"] = b"expects:never"
    return repository.add(label, date, files, parent)


def only_documentation(
    repository: FakeRepository, parent: CommitName, label: str, date: int
) -> CommitName:
    files = dict(repository.commits[parent][2])
    files["README"] = label.encode()
    return repository.add(label, date, files, parent)


def dockerfile(tmp_path: Path) -> Path:
    path = tmp_path / "pack" / "Dockerfile"
    path.parent.mkdir(exist_ok=True)
    path.write_text("FROM the-working-copy\n")
    return path


def self_check(
    tmp_path: Path, repository: FakeRepository, runtime: FakeRuntime, start: CommitName
) -> SelfCheckResult:
    return run_self_check(pack(), dockerfile(tmp_path), start, repository, runtime, PROGRAMS)


__all__ = ["fixing_commit"]
