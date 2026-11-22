"""The parts of the job corpus (ADR-0078): a pytest plugin that keeps the tests of one part.

Loaded with `-p tools.corpus_parts`, it gives each test of `tests/corpus` a part from its node id
and, with `--corpus-part`, deselects every test of another part. Part `d` is every test that `a`,
`b` and `c` do not take, so a new test falls into `d` unless a rule here takes it.
"""

from pathlib import PurePosixPath

import pytest

PARTS = ("a", "b", "c", "d")
AUDIT = "test_corpus_audit.py"
PROJECTS = {"mdformat": "a", "python-semver": "b", "cachetools": "b"}
MODULES = {"test_corpus_holdout_by_hand.py": "c", "test_corpus_sealed_run.py": "c"}
OPTION = "--corpus-part"


def part_of(nodeid: str) -> str:
    """The part of a test of the corpus, from its node id."""
    path, _, name = nodeid.partition("::")
    module = PurePosixPath(path).name
    if module == AUDIT and "[" in name:
        project = name.split("[", 1)[1].split("/", 1)[0]
        return PROJECTS.get(project, "d")
    return MODULES.get(module, "d")


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(OPTION, help="the part of the corpus to run: a, b, c or d")


def pytest_configure(config: pytest.Config) -> None:
    part = config.getoption(OPTION)
    if part is not None and part not in PARTS:
        raise pytest.UsageError(f"{OPTION} {part!r} names no part; the parts are a, b, c and d")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    part = config.getoption(OPTION)
    if part is None:
        return
    kept = [item for item in items if part_of(item.nodeid) == part]
    deselected = [item for item in items if part_of(item.nodeid) != part]
    if deselected:
        config.hook.pytest_deselected(items=deselected)
    items[:] = kept
