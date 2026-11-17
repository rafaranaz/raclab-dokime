"""The trees that the gates compare or observe: the base, and the base with the patch."""

from dokime.core.repository import AuditedRepository, CommitName, RepoPath, TreeName


def base_tree(repository: AuditedRepository, base: CommitName) -> TreeName:
    """The tree of the base commit, composed as every other tree is."""
    return repository.compose_with_paths(base, base, _nothing)


def _nothing(path: RepoPath) -> bool:
    return False
