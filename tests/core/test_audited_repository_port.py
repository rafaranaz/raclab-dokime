# SDD-EARS: CORE-096 CORE-097 CORE-098 CORE-099
from collections.abc import Callable
from typing import get_type_hints

from dokime.core.repository import (
    AuditedRepository,
    CommitName,
    ProjectRepository,
    RepoPath,
    TreeName,
)


def operations(port: type) -> set[str]:
    return {
        name
        for klass in port.__mro__
        if klass not in (object,) and getattr(klass, "_is_protocol", False)
        for name in vars(klass)
        if not name.startswith("_")
    }


def test_the_audited_port_offers_the_operations_of_the_project_port_and_one_more() -> None:
    assert ProjectRepository in AuditedRepository.__mro__
    assert operations(AuditedRepository) - operations(ProjectRepository) == {
        "compose_tree_with_paths"
    }


def test_the_composition_over_a_tree_receives_the_tree_the_commit_and_the_rule() -> None:
    hints = get_type_hints(AuditedRepository.compose_tree_with_paths)
    assert (hints["tree"], hints["source"], hints["take"]) == (
        TreeName,
        CommitName,
        Callable[[RepoPath], bool],
    )


def test_the_composition_over_a_tree_returns_the_name_of_the_tree() -> None:
    assert get_type_hints(AuditedRepository.compose_tree_with_paths)["return"] is TreeName


def test_the_composition_over_a_tree_says_that_it_replaces_the_region_of_the_rule() -> None:
    said = " ".join((AuditedRepository.compose_tree_with_paths.__doc__ or "").split())
    assert "exactly the files of `source`" in said
    assert "elsewhere exactly the files of `tree`" in said
