# SDD-EARS: PLATFORM-010 PLATFORM-011 PLATFORM-012 PLATFORM-013 PLATFORM-014 PLATFORM-015
import subprocess
from pathlib import Path

import pytest

from dokime.core.repository import CommitName, RepoPath
from dokime.platform.git import GitRepository
from tests.platform.repos import Project, file, refusal, snapshot


def in_tests(path: RepoPath) -> bool:
    return path.text.startswith("tests/")


@pytest.fixture
def project(tmp_path: Path) -> Project:
    project = Project(tmp_path / "project")
    first = project.commit([file("src/a.py", b"a\n"), file("tests/t.py", b"t1\n")], date=100)
    project.commit([file("src/a.py", b"b\n"), file("tests/t.py", b"t2\n")], first, date=200)
    return project


def head(project: Project) -> CommitName:
    return CommitName(project.text("rev-parse", "main"))


def every_operation(repository: GitRepository, project: Project, out: Path) -> None:
    commit = head(project)
    parent = repository.change(commit).parent
    repository.history(commit)
    tree = repository.compose_with_paths(parent, commit, in_tests)
    out.mkdir()
    repository.extract(tree, out)


def test_no_file_of_the_git_directory_of_the_project_changes(
    tmp_path: Path, project: Project
) -> None:
    before = snapshot(project.path / ".git")
    every_operation(GitRepository(project.path), project, tmp_path / "out")
    assert snapshot(project.path / ".git") == before


def test_a_composed_tree_is_written_in_the_temporary_directory_and_not_in_the_project(
    project: Project, temporary: Path
) -> None:
    repository = GitRepository(project.path)
    commit = head(project)
    tree = repository.compose_with_paths(repository.change(commit).parent, commit, in_tests)
    loose = Path(tree.text[:2]) / tree.text[2:]
    (own,) = temporary.iterdir()
    assert (own / "objects" / loose).is_file()
    exists = subprocess.run(["git", "-C", str(project.path), "cat-file", "-e", tree.text])
    assert exists.returncode != 0


def test_the_variables_of_git_in_the_environment_do_not_reach_git(
    tmp_path: Path, project: Project, monkeypatch: pytest.MonkeyPatch
) -> None:
    elsewhere = Project(tmp_path / "elsewhere")
    elsewhere.commit([file("x", b"x\n")])
    before = snapshot(project.path / ".git")
    monkeypatch.setenv("GIT_DIR", str(elsewhere.path / ".git"))
    monkeypatch.setenv("GIT_INDEX_FILE", str(project.path / ".git" / "index"))
    monkeypatch.setenv("GIT_OBJECT_DIRECTORY", str(project.path / ".git" / "objects"))
    monkeypatch.setenv("GIT_WORK_TREE", str(project.path))
    repository = GitRepository(project.path)
    every_operation(repository, project, tmp_path / "out")
    assert (tmp_path / "out" / "tests" / "t.py").read_bytes() == b"t2\n"
    assert snapshot(project.path / ".git") == before


def test_the_configuration_of_the_person_is_not_read(
    tmp_path: Path, project: Project, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "home"
    (home / ".config" / "git").mkdir(parents=True)
    hostile = "[core]\n\tautocrlf = true\n\teol = crlf\n"
    (home / ".gitconfig").write_text(hostile)
    (home / ".config" / "git" / "config").write_text(hostile)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    every_operation(GitRepository(project.path), project, tmp_path / "out")
    assert (tmp_path / "out" / "src" / "a.py").read_bytes() == b"a\n"


def test_the_replace_objects_of_the_project_are_ignored(tmp_path: Path, project: Project) -> None:
    """A replacement lives in the references of the project, under `refs/replace/`. The
    repository of the adapter reads the objects of the project as alternates, and alternates
    share objects, not references, so the graft below is not seen. The adapter also runs git
    with `GIT_NO_REPLACE_OBJECTS`, so that a replacement written in its own repository would be
    ignored as well."""
    commit = head(project)
    project.git("replace", "--graft", commit.text)
    repository = GitRepository(project.path)
    assert len(repository.history(commit)) == 2
    assert len(repository.change(commit).paths) == 2


def test_an_error_of_git_that_nothing_else_names_is_refused_with_what_git_wrote(
    project: Project, temporary: Path
) -> None:
    repository = GitRepository(project.path)
    commit = head(project)
    parent = repository.change(commit).parent
    (own,) = temporary.iterdir()
    for fanout in range(256):
        (own / "objects" / f"{fanout:02x}").write_bytes(b"")
    finding = refusal(lambda: repository.compose_with_paths(parent, commit, in_tests))
    assert finding.code == "git-failed"
    assert "unable to create temporary file" in finding.message
