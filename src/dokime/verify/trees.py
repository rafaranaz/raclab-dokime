"""The trees that the gates compare or observe: the base, and the tree of the change.

The tree of the change is the base with the patch applied, with the paths of the tests and of the
configuration of the tests taken from the base, except those that the contract authorises
(ADR-0058): the code of the patch runs against the tests of the base, and what the patch does to
the tests is the business of `protected-paths`.
"""

from dokime.contract.model import Contract
from dokime.core.repository import AuditedRepository, CommitName, RepoPath, TreeName
from dokime.packs.model import Pack


def base_tree(repository: AuditedRepository, base: CommitName) -> TreeName:
    """The tree of the base commit, composed as every other tree is."""
    return repository.compose_with_paths(base, base, _nothing)


def _nothing(path: RepoPath) -> bool:
    return False


def change_tree(
    pack: Pack, contract: Contract, base: CommitName, patch: bytes, repository: AuditedRepository
) -> TreeName:
    """The base with the patch, with the tests and their configuration of the base."""
    authorised = set(contract.may_modify_tests)

    def of_the_base(path: RepoPath) -> bool:
        protected = pack.is_test(path.text) or pack.is_config(path.text)
        return protected and path.text not in authorised

    return repository.compose_tree_with_paths(
        repository.compose_with_patch(base, patch), base, of_the_base
    )
