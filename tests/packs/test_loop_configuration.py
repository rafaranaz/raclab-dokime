# SDD-EARS: PACKS-037 PACKS-061
from pathlib import Path

from dokime.core.repository import CommitName
from dokime.packs.check import check
from dokime.packs.loop import SelfCheckResult, _read, run_self_check
from dokime.packs.model import Pack
from dokime.packs.sections import section_changed
from tests.packs.doubles import CODE, FakeRepository, FakeRuntime
from tests.packs.loops import PROGRAMS, dockerfile, fixing_commit, root
from tests.packs.packs import VALID

PYPROJECT = b'[project]\nname = "x"\n\n[tool.pytest.ini_options]\naddopts = "-q"\n'


def configured() -> Pack:
    text = VALID.replace(
        '  config: ["pytest.ini"]',
        '  config: ["pytest.ini"]\n  sections:\n'
        "    - file: pyproject.toml\n      format: toml\n      section: tool.pytest.ini_options",
    )
    checked = check(text)
    assert checked.pack is not None
    return checked.pack


def with_files(
    repository: FakeRepository, parent: CommitName, label: str, date: int, files: dict[str, bytes]
) -> CommitName:
    """A fixing commit that also changes some other files."""
    fix = fixing_commit(repository, parent, label, date)
    _, parents, kept = repository.commits.pop(fix)
    return repository.add(label, date, kept | files, *parents)


def checked(tmp_path: Path, repository: FakeRepository, start: CommitName) -> SelfCheckResult:
    return run_self_check(
        configured(), dockerfile(tmp_path), start, repository, FakeRuntime(), PROGRAMS
    )


def started(repository: FakeRepository) -> CommitName:
    first = root(repository)
    files = dict(repository.commits[first][2]) | {
        "pyproject.toml": PYPROJECT,
        "pytest.ini": b"[pytest]\n",
    }
    return repository.add("configured", 150, files, first)


def test_the_parent_side_takes_the_configuration_of_the_commit(tmp_path: Path) -> None:
    repository = FakeRepository()
    fix = with_files(repository, started(repository), "fix", 200, {"pytest.ini": b"[pytest]\n-q\n"})
    (candidate,) = checked(tmp_path, repository, fix).candidates
    parent = repository.trees[candidate.parent_side.tree]
    assert (parent["pytest.ini"], parent[CODE]) == (b"[pytest]\n-q\n", b"root")


def test_a_commit_that_changes_a_section_of_the_pack_is_not_a_candidate(tmp_path: Path) -> None:
    repository = FakeRepository()
    changed = PYPROJECT.replace(b'"-q"', b'"-q --deselect tests/test_root.py"')
    fix = with_files(repository, started(repository), "fix", 200, {"pyproject.toml": changed})
    assert checked(tmp_path, repository, fix).candidates == ()


def test_a_commit_that_changes_a_mixed_file_outside_its_section_is_a_candidate(
    tmp_path: Path,
) -> None:
    repository = FakeRepository()
    changed = PYPROJECT.replace(b'name = "x"', b'name = "y"')
    fix = with_files(repository, started(repository), "fix", 200, {"pyproject.toml": changed})
    (candidate,) = checked(tmp_path, repository, fix).candidates
    assert candidate.commit == fix


def test_a_commit_that_adds_the_section_where_there_was_none_is_not_a_candidate(
    tmp_path: Path,
) -> None:
    repository = FakeRepository()
    first = root(repository)
    plain = dict(repository.commits[first][2]) | {"pyproject.toml": b'[project]\nname = "x"\n'}
    start = repository.add("plain", 150, plain, first)
    fix = with_files(repository, start, "fix", 200, {"pyproject.toml": PYPROJECT})
    assert checked(tmp_path, repository, fix).candidates == ()


def test_a_section_file_reached_through_a_link_counts_as_changed(tmp_path: Path) -> None:
    # The doubles cannot write a link, so the reading of a file of the tree is tested alone.
    (tmp_path / "elsewhere.toml").write_bytes(PYPROJECT)
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / "pyproject.toml").symlink_to(tmp_path / "elsewhere.toml")
    section = configured().sections[0]
    assert section_changed(section, PYPROJECT, _read(tree, "pyproject.toml"))
    assert _read(tree, "absent.toml") is None
