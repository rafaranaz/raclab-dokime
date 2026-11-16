# SDD-EARS: PLATFORM-047
"""No program that git could be told to run is run by the adapter.

A project and the person can name programs that git runs: in the configuration of git at the level
of the project, of the person or of the system; in the hooks of the project; and in the attributes
of a tree, through the filters and the diff drivers that the configuration defines. Each of them
here leaves a mark when it runs. The same commands of git that a person runs in the project are the
control: they must leave marks, or the test would prove nothing.
"""

import os
import subprocess
from pathlib import Path

import pytest

from dokime.core.repository import CommitName
from dokime.platform.git import GitRepository
from tests.platform.repos import Project, file

DRIVERS = ("filter.evil.smudge", "filter.evil.clean", "diff.evil.textconv", "diff.evil.command")
PROJECT_KEYS = (
    "core.fsmonitor",
    "core.sshCommand",
    "core.pager",
    "core.editor",
    "core.askPass",
    "credential.helper",
    "diff.external",
    "core.alternateRefsCommand",
    "uploadpack.packObjectsHook",
    "sequence.editor",
)
HOOKS = ("post-checkout", "post-index-change", "pre-commit", "post-commit", "reference-transaction")


def leaves_a_mark(marks: Path, name: str, key: str = "") -> str:
    """A command of git that touches its mark; a filter passes its input, a textconv its file."""
    if key.startswith("filter."):
        return f"sh -c 'touch {marks}/{name}; cat' #"
    if key.endswith(".textconv"):
        return f"sh -c 'touch {marks}/{name}; cat \"$1\"' --"
    return f"sh -c 'touch {marks}/{name}' #"


class Hostile:
    """A project whose settings name programs at one level, and the environment of its person."""

    def __init__(self, root: Path, level: str) -> None:
        self.marks = root / "marks"
        self.marks.mkdir()
        home, system = root / "home", root / "system.gitconfig"
        home.mkdir()
        system.write_text("")
        self.environment = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.environment |= {"HOME": str(home), "GIT_CONFIG_SYSTEM": str(system), "LC_ALL": "C"}
        self.project = Project(root / "project")
        first = self.project.commit([file("f", b"1\n")], date=100)
        attributes = file(".gitattributes", b"* filter=evil diff=evil\n")
        self.project.commit([file("f", b"2\n"), attributes], first, date=200)
        local = self.project.path / ".git" / "config"
        for key in PROJECT_KEYS:
            self.configure(local, key, f"project-{key}")
        defined_in = {"project": local, "global": home / ".gitconfig", "system": system}[level]
        for key in DRIVERS:
            self.configure(defined_in, key, f"{level}-{key}")
        hooks = self.project.path / ".git" / "hooks"
        if level == "project":
            hooks = self.project.path / ".git" / "hooks-of-the-configuration"
            hooks.mkdir()
            self.configure(local, "core.hooksPath", "", value=str(hooks))
            outside = root / "attributes"
            outside.write_text("* filter=evil diff=evil\n")
            self.configure(local, "core.attributesFile", "", value=str(outside))
        for hook in HOOKS:
            program = hooks / hook
            program.write_text(f"#!/bin/sh\ntouch {self.marks}/hook-{hook}\n")
            program.chmod(0o755)

    def configure(self, where: Path, key: str, mark: str, *, value: str | None = None) -> None:
        given = value if value is not None else leaves_a_mark(self.marks, mark, key)
        subprocess.run(["git", "config", "--file", str(where), key, given], check=True)

    def left(self) -> set[str]:
        return {mark.name for mark in self.marks.iterdir()}

    def as_a_person(self, *args: str) -> None:
        subprocess.run(
            ["git", "-C", str(self.project.path), *args],
            env=self.environment,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=True,
            timeout=60,
        )


@pytest.mark.parametrize("level", ["project", "global", "system"])
def test_no_program_that_the_settings_of_git_name_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, level: str
) -> None:
    hostile = Hostile(tmp_path, level)
    for name, value in hostile.environment.items():
        monkeypatch.setenv(name, value)
    commit = CommitName(hostile.project.text("rev-parse", "main"))
    out = tmp_path / "out"
    out.mkdir()
    with GitRepository(hostile.project.path) as repository:
        repository.history(commit)
        parent = repository.change(commit).parent
        tree = repository.compose_with_paths(parent, commit, lambda path: path.text != "f")
        repository.extract(tree, out)
    assert hostile.left() == set()

    hostile.as_a_person("checkout", "--force", "main")
    hostile.as_a_person("status")
    hostile.as_a_person("diff", "main~1", "main")
    assert {
        f"{level}-filter.evil.smudge",
        f"{level}-diff.evil.command",
        "project-core.fsmonitor",
        "hook-post-checkout",
        "hook-post-index-change",
    } <= hostile.left()
