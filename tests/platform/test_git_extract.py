# SDD-EARS: PLATFORM-040 PLATFORM-041 PLATFORM-042 PLATFORM-043
import os
from pathlib import Path

import pytest

from dokime.core.repository import TreeName
from dokime.platform.git import GitRepository
from tests.platform.repos import EXECUTABLE, Project, file, link

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


def test_each_file_is_written_with_the_bytes_of_its_blob(
    tmp_path: Path, project: Project, out: Path
) -> None:
    tree = hostile_tree(project)
    GitRepository(project.path).extract(TreeName(tree), out)
    for mode, blob, path in project.entries(tree):
        assert (out / os.fsdecode(path)).read_bytes() == project.blob(blob), (mode, path)


def test_an_executable_file_is_written_as_executable(
    tmp_path: Path, project: Project, out: Path
) -> None:
    tree = project.tree([file("run.sh", b"#!/bin/sh\n", mode=EXECUTABLE), file("data", b"d")])
    GitRepository(project.path).extract(TreeName(tree), out)
    assert os.access(out / "run.sh", os.X_OK)
    assert not os.access(out / "data", os.X_OK)


def test_a_symbolic_link_is_written_as_a_link_to_its_target(
    tmp_path: Path, project: Project, out: Path
) -> None:
    tree = project.tree([file("src/real.py", b"r"), link("alias.py", "src/real.py")])
    GitRepository(project.path).extract(TreeName(tree), out)
    assert (out / "alias.py").is_symlink()
    assert os.readlink(out / "alias.py") == "src/real.py"


def test_nothing_that_is_not_in_the_tree_is_written(
    tmp_path: Path, project: Project, out: Path
) -> None:
    tree = hostile_tree(project)
    GitRepository(project.path).extract(TreeName(tree), out)
    written = {
        str((Path(root) / name).relative_to(out))
        for root, _, names in os.walk(out)
        for name in names
    }
    assert written == {os.fsdecode(path) for _, _, path in project.entries(tree)}
