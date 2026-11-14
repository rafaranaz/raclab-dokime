# SDD-EARS: PLATFORM-044 PLATFORM-045 PLATFORM-046
from pathlib import Path

import pytest

from dokime.core.repository import TreeName
from dokime.platform.git import GitRepository
from tests.platform.repos import Project, file, refusal, submodule

ATTRIBUTES = b"""\
tests/test_ignored.py export-ignore
version.py export-subst
*.py eol=crlf
*.txt filter=upper ident
"""


@pytest.fixture
def project(tmp_path: Path) -> Project:
    project = Project(tmp_path / "project")
    project.git("config", "core.autocrlf", "true")
    project.git("config", "filter.upper.smudge", "tr a-z A-Z")
    attributes = tmp_path / "attributes"
    attributes.write_text("* eol=crlf\n")
    project.git("config", "core.attributesFile", str(attributes))
    (project.path / ".git" / "info").mkdir(exist_ok=True)
    (project.path / ".git" / "info" / "attributes").write_text("* eol=crlf text\n")
    return project


@pytest.fixture
def out(tmp_path: Path) -> Path:
    out = tmp_path / "out"
    out.mkdir()
    return out


def hostile_tree(project: Project) -> str:
    """A tree whose attributes, and those of the configuration, would each change an
    extraction."""
    return project.tree_of(
        project.commit(
            [
                file(".gitattributes", ATTRIBUTES),
                file("tests/test_ignored.py", b"def test():\n    pass\n"),
                file("version.py", b"VERSION = '$Format:%H$'\n"),
                file("src/code.py", b"line one\nline two\n"),
                file("notes.txt", b"lower case $Id$\n"),
                file("mixed.bin", b"a\r\nb\nc\r"),
            ]
        )
    )


def test_a_tree_with_a_submodule_is_refused_naming_it_before_writing(
    tmp_path: Path, project: Project, out: Path
) -> None:
    commit = project.commit([file("a", b"0")])
    tree = project.tree([file("a", b"0"), submodule("vendor/lib", commit)])
    repository = GitRepository(project.path)
    finding = refusal(lambda: repository.extract(TreeName(tree), out))
    assert (finding.code, "vendor/lib" in finding.message) == ("submodule-in-tree", True)
    assert list(out.iterdir()) == []


UNKNOWN = "fedcba9876543210" * 2 + "fedcba98"


def test_a_tree_that_cannot_be_read_is_refused_naming_it(
    tmp_path: Path, project: Project, out: Path
) -> None:
    commit = project.commit([file("a", b"0")])
    repository = GitRepository(project.path)
    for text in (UNKNOWN, commit):
        finding = refusal(lambda: repository.extract(TreeName(text), out))  # noqa: B023
        assert (finding.code, text in finding.message) == ("unknown-tree", True)


def test_a_directory_that_is_not_empty_is_rejected(
    tmp_path: Path, project: Project, out: Path
) -> None:
    tree = project.tree([file("a", b"0")])
    (out / "left").write_text("")
    repository = GitRepository(project.path)
    with pytest.raises(ValueError, match=str(out)):
        repository.extract(TreeName(tree), out)


def test_a_directory_that_does_not_exist_is_rejected(tmp_path: Path, project: Project) -> None:
    tree = project.tree([file("a", b"0")])
    missing = tmp_path / "missing"
    repository = GitRepository(project.path)
    with pytest.raises(ValueError, match=str(missing)):
        repository.extract(TreeName(tree), missing)
