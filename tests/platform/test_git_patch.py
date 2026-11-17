# SDD-EARS: PLATFORM-032 PLATFORM-033 PLATFORM-034 PLATFORM-035
from pathlib import Path

import pytest

from dokime.core.repository import CommitName, TreeName
from dokime.platform.git import GitRepository
from tests.platform.repos import EXECUTABLE, Project, file, link, refusal, snapshot


@pytest.fixture
def project(tmp_path: Path) -> Project:
    return Project(tmp_path / "project")


def patch_between(project: Project, base: str, target: str) -> bytes:
    """The patch that git writes from one commit to another, binary files and modes included."""
    return project.git("diff", "--binary", "--full-index", "-M", base, target)


def files(project: Project, tree: TreeName) -> dict[bytes, tuple[str, bytes]]:
    """The mode and the bytes of every file of a tree, by its path."""
    return {path: (mode, project.blob(name)) for mode, name, path in project.entries(tree.text)}


BASE = [
    file("src/a.py", b"one\ntwo\nthree\n"),
    file("src/gone.py", b"gone\n"),
    file("src/moved.py", b"moved\n" * 20),
    file("run.sh", b"echo\n"),
    file("keep.txt", b"kept\n"),
]


def test_the_patch_gives_each_file_it_touches_its_bytes_and_its_mode(project: Project) -> None:
    base = project.commit(BASE)
    target = project.commit(
        [
            file("src/a.py", b"one\nTWO\nthree\n"),
            file("src/new.py", b"new\n"),
            file("src/renamed.py", b"moved\n" * 20),
            file("run.sh", b"echo\n", mode=EXECUTABLE),
            file("data.bin", bytes(range(256))),
            link("current", "src/a.py"),
            file("keep.txt", b"kept\n"),
        ],
        base,
    )
    repository = GitRepository(project.path)
    tree = repository.compose_with_patch(CommitName(base), patch_between(project, base, target))
    assert tree == TreeName(project.tree_of(target))


def test_the_files_the_patch_does_not_touch_are_kept(project: Project) -> None:
    base = project.commit(BASE)
    target = project.commit([*BASE[:4], file("keep.txt", b"kept\n"), file("b", b"b\n")], base)
    repository = GitRepository(project.path)
    tree = repository.compose_with_patch(CommitName(base), patch_between(project, base, target))
    assert files(project, tree)[b"keep.txt"] == ("100644", b"kept\n")
    assert project.entries(tree.text) >= project.entries(project.tree_of(base))


@pytest.mark.parametrize(
    "patch",
    [
        b"diff --git a/src/a.py b/src/a.py\n--- a/src/a.py\n+++ b/src/a.py\n"
        b"@@ -1,3 +1,3 @@\n one\n-zwei\n+two\n three\n",
        b"",
        b"not a patch at all\n",
    ],
    ids=["wrong-context", "empty", "not-a-patch"],
)
def test_a_patch_that_does_not_apply_is_refused_quoting_git(project: Project, patch: bytes) -> None:
    base = project.commit(BASE)
    repository = GitRepository(project.path)
    finding = refusal(lambda: repository.compose_with_patch(CommitName(base), patch))
    assert (finding.code, "git apply" in finding.message) == ("patch-does-not-apply", True)


def new_file(path: str) -> bytes:
    return (
        f"diff --git a/{path} b/{path}\nnew file mode 100644\n--- /dev/null\n+++ b/{path}\n"
        "@@ -0,0 +1 @@\n+echo\n"
    ).encode()


@pytest.mark.parametrize("path", [".git/config", "sub/.GIT/hooks/x", ".Git/x", "a/.gIT"])
def test_a_patch_that_names_a_path_under_git_in_any_case_is_refused_naming_it(
    project: Project, path: str
) -> None:
    base = project.commit(BASE)
    before = snapshot(project.path / ".git")
    repository = GitRepository(project.path)
    finding = refusal(lambda: repository.compose_with_patch(CommitName(base), new_file(path)))
    assert (finding.code, path in finding.message) == ("patch-touches-git", True)
    assert snapshot(project.path / ".git") == before


def test_a_rename_into_git_is_refused_naming_the_new_path(project: Project) -> None:
    base = project.commit(BASE)
    patch = (
        b"diff --git a/keep.txt b/.GIT/keep.txt\nsimilarity index 100%\n"
        b"rename from keep.txt\nrename to .GIT/keep.txt\n"
    )
    repository = GitRepository(project.path)
    finding = refusal(lambda: repository.compose_with_patch(CommitName(base), patch))
    assert (finding.code, ".GIT/keep.txt" in finding.message) == ("patch-touches-git", True)


def test_a_path_that_only_contains_git_in_a_name_is_applied(
    project: Project, tmp_path: Path
) -> None:
    base = project.commit(BASE)
    repository = GitRepository(project.path)
    tree = repository.compose_with_patch(CommitName(base), new_file("docs/.gitignore-notes"))
    out = tmp_path / "out"
    out.mkdir()
    repository.extract(tree, out)
    assert (out / "docs" / ".gitignore-notes").read_bytes() == b"echo\n"
