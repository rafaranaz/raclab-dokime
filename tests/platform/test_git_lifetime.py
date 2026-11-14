# SDD-EARS: PLATFORM-006 PLATFORM-007 PLATFORM-016 PLATFORM-017
import shutil
from pathlib import Path

import pytest

from dokime.core.repository import CommitName
from dokime.platform.git import GitRepository
from tests.platform.repos import Project, file, refusal


@pytest.fixture
def project(tmp_path: Path) -> Project:
    project = Project(tmp_path / "project")
    project.commit([file("a.py", b"a\n")])
    return project


def test_git_is_resolved_once_to_an_absolute_path_that_every_command_runs(
    tmp_path: Path, project: Project, monkeypatch: pytest.MonkeyPatch
) -> None:
    real = shutil.which("git")
    assert real is not None
    main = CommitName(project.text("rev-parse", "main"))
    with GitRepository(project.path) as repository:
        assert repository.git_path == Path(real).resolve()
        monkeypatch.setenv("PATH", str(tmp_path / "nowhere"))
        assert len(repository.history(main)) == 1


def test_a_git_named_by_its_path_is_run_by_that_path(tmp_path: Path, project: Project) -> None:
    real = shutil.which("git")
    assert real is not None
    with GitRepository(project.path, git=real) as repository:
        assert repository.git_path == Path(real).resolve()


def test_the_adapter_gives_the_version_of_the_git_it_runs(project: Project) -> None:
    said = project.text("--version").removeprefix("git version ")
    with GitRepository(project.path) as repository:
        assert repository.git_version == said


def test_closing_the_adapter_removes_its_temporary_directory(
    project: Project, temporary: Path
) -> None:
    with GitRepository(project.path):
        assert len(list(temporary.iterdir())) == 1
    assert list(temporary.iterdir()) == []


def test_closing_twice_is_harmless(project: Project, temporary: Path) -> None:
    repository = GitRepository(project.path)
    repository.close()
    repository.close()
    assert list(temporary.iterdir()) == []


def test_a_refused_opening_leaves_no_temporary_directory(tmp_path: Path, temporary: Path) -> None:
    project = Project(tmp_path / "project", object_format="sha256")
    refusal(lambda: GitRepository(project.path))
    assert list(temporary.iterdir()) == []
