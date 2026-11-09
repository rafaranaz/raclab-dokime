# SDD-EARS: REPO-010 REPO-011
from pathlib import Path

import pytest

from tests.repo.conftest import GitRunner, write
from tools._common import DEFAULT_ROOT, load_config
from tools.check_scope import check_changes, main, parse_branch

CONFIG = load_config(DEFAULT_ROOT)


def test_parses_a_well_formed_branch_name() -> None:
    assert parse_branch("ci/repo-quality-gates", CONFIG) == ("ci", "repo")


@pytest.mark.parametrize(
    "name",
    [
        "main",
        "feature/repo-gates",
        "ci/unknown-gates",
        "ci/repo",
        "ci/repo-Quality",
        "ci/repo-quality/extra",
    ],
)
def test_rejects_a_malformed_branch_name(name: str) -> None:
    with pytest.raises(ValueError, match="branch"):
        parse_branch(name, CONFIG)


def test_accepts_files_inside_the_scope_or_shared_paths() -> None:
    files = ["tools/check_scope.py", "docs/adr/0001-x.md", "docs/ROADMAP.md", "uv.lock"]
    assert check_changes(files, "repo", CONFIG) == []


def test_lists_every_file_outside_the_scope() -> None:
    files = ["tools/check_scope.py", "docs/architecture/c4.md", "src/dokime/graph/x.py"]
    message = check_changes(files, "repo", CONFIG)
    assert len(message) == 1
    assert "docs/architecture/c4.md" in message[0].message
    assert "src/dokime/graph/x.py" in message[0].message


def test_main_compares_the_branch_against_base(repo: Path, git: GitRunner) -> None:
    git(repo, "checkout", "-q", "-b", "docs/arch-context")
    write(repo, "docs/architecture/context.md", "x")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "docs(arch): add context")
    assert main(["--base", "main", "--branch", "docs/arch-context"], root=repo) == 0

    write(repo, "tools/extra.py", "x")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "docs(arch): sneak a tool in")
    assert main(["--base", "main", "--branch", "docs/arch-context"], root=repo) == 1


def test_main_rejects_an_invalid_branch_name(repo: Path) -> None:
    assert main(["--base", "main", "--branch", "random"], root=repo) == 1
