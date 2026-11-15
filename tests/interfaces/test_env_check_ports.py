# SDD-EARS: INTERFACES-055 INTERFACES-056 INTERFACES-057 INTERFACES-058
from pathlib import Path

import pytest

from dokime.core.repository import RefusalError
from tests.interfaces.envs import env_check, use_doubles, write_pack
from tests.packs.doubles import FakeRepository, FakeRuntime
from tests.packs.loops import fixing_commit, root


def test_the_dockerfile_is_read_from_the_directory_of_the_pack(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "project"
    write_pack(project / ".dokime", dockerfile="FROM beside-the-pack\n")
    (project / "Dockerfile").parent.mkdir(exist_ok=True)
    (project / "Dockerfile").write_text("FROM the-project-root\n")
    repository = FakeRepository()
    one = fixing_commit(repository, root(repository), "one", 200)
    runtime = FakeRuntime()
    use_doubles(monkeypatch, repository, runtime)
    env_check(capsys, one, "--project", str(project))
    assert {text for text, _, _ in runtime.builds} == {"FROM beside-the-pack\n"}


def test_the_programs_of_the_ports_are_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "project"
    write_pack(project / ".dokime")
    repository = FakeRepository()
    one = fixing_commit(repository, root(repository), "one", 200)
    use_doubles(monkeypatch, repository, FakeRuntime())
    run = env_check(capsys, one, "--project", str(project))
    assert run.lines[:2] == [
        "program git /usr/bin/git 2.47.3",
        "program podman /usr/bin/podman 5.4.2",
    ]


def test_an_adapter_that_refuses_to_open_is_reported_and_nothing_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "project"
    write_pack(project / ".dokime")
    repository, runtime = FakeRepository(), FakeRuntime()
    opened = use_doubles(monkeypatch, repository, runtime)
    opened.refuse = RefusalError("podman-not-found", "no executable program 'podman' was found")
    run = env_check(capsys, "a" * 40, "--project", str(project))
    assert run.code == 2
    assert "ERROR podman-not-found" in run.out
    assert (repository.calls, runtime.builds) == ([], [])


@pytest.mark.parametrize("data", [b"\xff\xfe not utf-8", None])
def test_a_pack_file_that_cannot_be_read_is_reported(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    data: bytes | None,
) -> None:
    project = tmp_path / "project"
    (project / ".dokime").mkdir(parents=True)
    if data is not None:
        (project / ".dokime" / "pack.yaml").write_bytes(data)
    opened = use_doubles(monkeypatch, FakeRepository(), FakeRuntime())
    run = env_check(capsys, "a" * 40, "--project", str(project))
    assert run.code == 2
    assert [line.split(": ")[1] for line in run.lines[:-1]] == ["ERROR unreadable-file"]
    assert opened.projects == []
