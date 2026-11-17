# SDD-EARS: CORE-099
"""The double of the audited repository follows the rule of the port: a composition over a tree
replaces the region that the rule takes, so that the tests of verify cannot pass on a double that
overlays it."""

from dokime.core.repository import AuditedRepository, RepoPath
from tests.verify.doubles import AuditedDouble, patch


def in_tests(path: RepoPath) -> bool:
    return path.text.startswith("tests/")


def test_the_double_replaces_the_region_of_the_rule_and_keeps_the_rest() -> None:
    repository: AuditedRepository = AuditedDouble()
    double = repository
    assert isinstance(double, AuditedDouble)
    base = double.add({"src/a.py": b"old", "tests/test_a.py": b"base"})
    patched = double.compose_with_patch(
        base, patch({"src/a.py": "new", "tests/test_a.py": "edited", "tests/conftest.py": "added"})
    )
    composed = double.compose_tree_with_paths(patched, base, in_tests)
    assert double.trees[composed] == {"src/a.py": b"new", "tests/test_a.py": b"base"}
