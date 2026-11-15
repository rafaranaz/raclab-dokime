# SDD-EARS: INTERFACES-050 INTERFACES-051 INTERFACES-052 INTERFACES-053 INTERFACES-054
from pathlib import Path

import pytest

from tests.interfaces.envs import env_check, use_doubles, write_pack
from tests.packs.doubles import FakeRepository, FakeRuntime
from tests.packs.loops import fixing_commit, root


@pytest.fixture
def repository() -> FakeRepository:
    return FakeRepository()


def test_the_pack_of_the_project_is_used_when_none_is_given(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repository: FakeRepository,
) -> None:
    project = tmp_path / "project"
    write_pack(project / ".dokime", dockerfile="FROM the-pack-of-the-project\n")
    one = fixing_commit(repository, root(repository), "one", 200)
    runtime = FakeRuntime()
    use_doubles(monkeypatch, repository, runtime)
    env_check(capsys, one, "--project", str(project))
    assert {text for text, _, _ in runtime.builds} == {"FROM the-pack-of-the-project\n"}


def test_a_pack_given_with_pack_is_used(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repository: FakeRepository,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    pack = write_pack(tmp_path / "elsewhere", dockerfile="FROM given-with-pack\n")
    one = fixing_commit(repository, root(repository), "one", 200)
    runtime = FakeRuntime()
    use_doubles(monkeypatch, repository, runtime)
    env_check(capsys, one, "--project", str(project), "--pack", str(pack))
    assert {text for text, _, _ in runtime.builds} == {"FROM given-with-pack\n"}


def test_the_project_is_the_current_directory_or_the_one_given(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repository: FakeRepository,
) -> None:
    here, there = tmp_path / "here", tmp_path / "there"
    write_pack(here / ".dokime")
    write_pack(there / ".dokime")
    one = fixing_commit(repository, root(repository), "one", 200)
    opened = use_doubles(monkeypatch, repository, FakeRuntime())
    monkeypatch.chdir(here)
    env_check(capsys, one)
    env_check(capsys, one, "--project", str(there))
    assert [path.resolve() for path in opened.projects] == [here.resolve(), there.resolve()]


def test_the_self_check_starts_from_the_commit_given(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repository: FakeRepository,
) -> None:
    project = tmp_path / "project"
    write_pack(project / ".dokime")
    one = fixing_commit(repository, root(repository), "one", 200)
    two = fixing_commit(repository, one, "two", 300)
    use_doubles(monkeypatch, repository, FakeRuntime())
    run = env_check(capsys, one, "--project", str(project))
    assert one.text in run.out
    assert two.text not in run.out


@pytest.mark.parametrize("name", ["HEAD", "main", "abc123", "A" * 40, "0" * 39, "0" * 41, "g" * 40])
def test_a_name_that_is_not_a_full_commit_name_is_refused(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repository: FakeRepository,
    name: str,
) -> None:
    project = tmp_path / "project"
    write_pack(project / ".dokime")
    opened = use_doubles(monkeypatch, repository, FakeRuntime())
    run = env_check(capsys, name, "--project", str(project))
    assert run.code == 2
    assert [line.split(": ")[1] for line in run.lines[:-1]] == ["ERROR not-a-commit-name"]
    assert opened.projects == []


def test_a_pack_with_a_finding_is_reported_and_nothing_runs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repository: FakeRepository,
) -> None:
    project = tmp_path / "project"
    write_pack(project / ".dokime", text="format: 1\nname: x\n")
    one = fixing_commit(repository, root(repository), "one", 200)
    opened = use_doubles(monkeypatch, repository, FakeRuntime())
    run = env_check(capsys, one, "--project", str(project))
    assert run.code == 1
    assert "missing-field" in run.out
    assert opened.projects == []
