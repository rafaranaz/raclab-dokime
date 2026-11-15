"""Helpers to run `env check` over the doubles of the ports and read what it wrote."""

import contextlib
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from dokime.core.repository import CommitName, RefusalError
from dokime.interfaces import env
from dokime.interfaces.cli import main
from tests.packs.doubles import FakeRepository, FakeRuntime
from tests.packs.loops import PROGRAMS
from tests.packs.packs import VALID


@dataclass
class Opened:
    """What the command opened: the project it asked for, and whether opening was refused."""

    projects: list[Path] = field(default_factory=list)
    refuse: RefusalError | None = None


@dataclass(frozen=True)
class Run:
    code: int
    out: str
    err: str

    @property
    def lines(self) -> list[str]:
        return self.out.splitlines()


def write_pack(directory: Path, text: str = VALID, dockerfile: str = "FROM the-pack\n") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "pack.yaml").write_text(text)
    (directory / "Dockerfile").write_text(dockerfile)
    return directory / "pack.yaml"


def use_doubles(
    monkeypatch: pytest.MonkeyPatch, repository: FakeRepository, runtime: FakeRuntime
) -> Opened:
    opened = Opened()

    @contextlib.contextmanager
    def doubles(project: Path) -> Iterator[env.Ports]:
        opened.projects.append(project)
        if opened.refuse is not None:
            raise opened.refuse
        yield env.Ports(repository=repository, runtime=runtime, programs=PROGRAMS)

    monkeypatch.setattr(env, "open_ports", doubles)
    return opened


def env_check(capsys: pytest.CaptureFixture[str], start: CommitName | str, *options: str) -> Run:
    name = start.text if isinstance(start, CommitName) else start
    code = main(["env", "check", "--from", name, *options])
    captured = capsys.readouterr()
    return Run(code=code, out=captured.out, err=captured.err)
