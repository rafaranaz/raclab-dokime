# SDD-EARS: PLATFORM-001 PLATFORM-002 PLATFORM-003 PLATFORM-004 PLATFORM-005
import subprocess
from pathlib import Path

import pytest

from dokime.core.repository import ProjectRepository
from dokime.platform.git import GitRepository
from tests.platform.repos import Project, clean_environment, file, refusal


@pytest.fixture
def project(tmp_path: Path) -> Project:
    project = Project(tmp_path / "project")
    project.commit([file("a.py", b"a\n")])
    return project


def fake_git(tmp_path: Path, version: str) -> str:
    script = tmp_path / "fake-git"
    script.write_text(f"#!/bin/sh\n[ \"$1\" = --version ] || exit 1\necho '{version}'\n")
    script.chmod(0o755)
    return str(script)


def test_the_adapter_opens_on_a_repository_and_is_a_project_repository(
    tmp_path: Path, project: Project
) -> None:
    repository: ProjectRepository = GitRepository(project.path)
    assert isinstance(repository, GitRepository)


def test_a_git_that_cannot_be_run_is_refused(tmp_path: Path, project: Project) -> None:
    missing = str(tmp_path / "no-such-git")
    finding = refusal(lambda: GitRepository(project.path, git=missing))
    assert finding.code == "git-not-found"


def test_a_git_that_is_not_executable_is_refused(tmp_path: Path, project: Project) -> None:
    script = tmp_path / "not-executable"
    script.write_text("#!/bin/sh\n")
    finding = refusal(lambda: GitRepository(project.path, git=str(script)))
    assert finding.code == "git-not-found"


@pytest.mark.parametrize(
    "version", ["git version 2.40.1", "git version 1.99.0", "git version 2.4.0", "not git at all"]
)
def test_a_git_older_than_2_41_or_unreadable_is_refused_quoting_its_version(
    tmp_path: Path, project: Project, version: str
) -> None:
    git = fake_git(tmp_path, version)
    finding = refusal(lambda: GitRepository(project.path, git=git))
    assert finding.code == "git-too-old"
    assert version in finding.message


def test_the_version_of_git_2_41_is_enough(tmp_path: Path) -> None:
    git = fake_git(tmp_path, "git version 2.41.0")
    finding = refusal(lambda: GitRepository(tmp_path, git=git))
    assert finding.code != "git-too-old"


@pytest.mark.parametrize("version", ["git version 2.41.0.windows.1", "git version 3.0.0"])
def test_a_version_with_a_suffix_or_a_new_major_is_enough(tmp_path: Path, version: str) -> None:
    git = fake_git(tmp_path, version)
    finding = refusal(lambda: GitRepository(tmp_path, git=git))
    assert finding.code != "git-too-old"


def test_a_directory_that_is_not_a_repository_is_refused(tmp_path: Path) -> None:
    (tmp_path / "plain").mkdir()
    finding = refusal(lambda: GitRepository(tmp_path / "plain"))
    assert finding.code == "not-a-repository"


def test_a_directory_inside_a_repository_is_not_a_repository(
    tmp_path: Path, project: Project
) -> None:
    (project.path / "inner").mkdir()
    finding = refusal(lambda: GitRepository(project.path / "inner"))
    assert finding.code == "not-a-repository"


def test_a_repository_of_sha256_is_refused(tmp_path: Path) -> None:
    project = Project(tmp_path / "project", object_format="sha256")
    finding = refusal(lambda: GitRepository(project.path))
    assert finding.code == "sha256-repository"


def test_a_shallow_clone_is_refused(tmp_path: Path, project: Project) -> None:
    project.commit([file("a.py", b"b\n")], project.text("rev-parse", "main"))
    subprocess.run(
        ["git", "clone", "--quiet", "--depth", "1", f"file://{project.path}", "shallow"],
        cwd=tmp_path,
        env=clean_environment(),
        check=True,
    )
    finding = refusal(lambda: GitRepository(tmp_path / "shallow"))
    assert finding.code == "shallow-clone"
