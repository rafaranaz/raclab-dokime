# SDD-EARS: REPO-001 REPO-002 REPO-003 REPO-004 REPO-005 REPO-006
from pathlib import Path

import pytest

from tests.repo.conftest import GitRunner, write
from tools._common import DEFAULT_ROOT, load_config
from tools.check_commits import Commit, check_commit, main

CONFIG = load_config(DEFAULT_ROOT)
TRAILERS = "Co-Authored-By: Someone <someone@example.com>\nClaude-Session: https://example.com/s"


def commit(message: str, parents: int = 1) -> Commit:
    return Commit(sha="abc1234", parents=tuple(f"p{i}" for i in range(parents)), message=message)


def test_accepts_a_well_formed_commit_with_body_and_trailers() -> None:
    message = f"fix(repo): reject empty scope\n\nThe scope was optional.\n\n{TRAILERS}"
    assert check_commit(commit(message), CONFIG, branch_scope="repo") == []


@pytest.mark.parametrize(
    "header",
    [
        "fixed the thing",
        "feature(repo): add check",
        "fix(repo) missing colon",
        "fix(repo):missing space",
        "fix(Repo): uppercase scope",
    ],
)
def test_rejects_a_header_that_does_not_follow_the_format(header: str) -> None:
    errors = check_commit(commit(f"{header}\n\nBody."), CONFIG, branch_scope=None)
    assert errors
    assert header in errors[0]


def test_rejects_a_header_without_scope() -> None:
    assert check_commit(commit("docs: explain"), CONFIG, branch_scope=None)


def test_rejects_an_undeclared_scope() -> None:
    errors = check_commit(commit("docs(nonexistent): explain"), CONFIG, branch_scope=None)
    assert any("nonexistent" in error for error in errors)


def test_rejects_a_scope_different_from_the_branch_scope() -> None:
    errors = check_commit(commit("docs(arch): explain"), CONFIG, branch_scope="repo")
    assert any("branch scope" in error for error in errors)


@pytest.mark.parametrize("kind", ["feat", "fix", "refactor", "perf"])
def test_rejects_a_body_less_commit_for_types_that_need_a_reason(kind: str) -> None:
    errors = check_commit(commit(f"{kind}(repo): change it"), CONFIG, branch_scope=None)
    assert any("body" in error for error in errors)


def test_trailers_alone_do_not_count_as_body() -> None:
    errors = check_commit(commit(f"feat(repo): change it\n\n{TRAILERS}"), CONFIG, branch_scope=None)
    assert any("body" in error for error in errors)


def test_does_not_require_a_body_for_documentation() -> None:
    assert check_commit(commit("docs(repo): fix a typo"), CONFIG, branch_scope=None) == []


def test_rejects_a_header_longer_than_72_characters() -> None:
    header = "docs(repo): " + "x" * 61
    assert len(header) == 73
    errors = check_commit(commit(header), CONFIG, branch_scope=None)
    assert any("72" in error for error in errors)


def test_rejects_a_merge_commit() -> None:
    errors = check_commit(commit("docs(repo): merge", parents=2), CONFIG, branch_scope=None)
    assert any("merge" in error for error in errors)


def test_main_checks_every_commit_after_base(repo: Path, git: GitRunner) -> None:
    git(repo, "checkout", "-q", "-b", "docs/repo-example")
    write(repo, "a.md", "a")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "docs(repo): add a")
    assert main(["--base", "main", "--branch", "docs/repo-example"], root=repo) == 0

    write(repo, "b.md", "b")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "added b")
    assert main(["--base", "main", "--branch", "docs/repo-example"], root=repo) == 1


def test_main_without_branch_skips_the_branch_scope_rule(repo: Path, git: GitRunner) -> None:
    git(repo, "checkout", "-q", "-b", "work")
    write(repo, "a.md", "a")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "docs(arch): add a")
    assert main(["--base", "main"], root=repo) == 0
