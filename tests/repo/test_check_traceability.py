# SDD-EARS: REPO-040 REPO-041 REPO-042
from pathlib import Path

from tests.repo.conftest import GitRunner, write
from tools.check_traceability import check, main, read_marker

REQUIREMENTS = {"CORE-001": "docs/requirements/core.md", "CORE-002": "docs/requirements/core.md"}


def test_reads_the_marker_from_the_first_non_empty_line() -> None:
    assert read_marker("\n# SDD-EARS: CORE-001, CORE-002\nimport x\n") == ["CORE-001", "CORE-002"]


def test_returns_none_when_the_first_line_is_not_a_marker() -> None:
    assert read_marker('"""Docstring."""\n# SDD-EARS: CORE-001\n') is None


def test_accepts_full_coverage() -> None:
    tests = {"tests/core/test_a.py": "# SDD-EARS: CORE-001 CORE-002\n"}
    assert check(REQUIREMENTS, tests) == []


def test_reports_uncovered_requirements() -> None:
    findings = check(REQUIREMENTS, {"tests/core/test_a.py": "# SDD-EARS: CORE-001\n"})
    assert [f.message for f in findings] == ["CORE-002 is not covered by any test"]
    assert findings[0].path == "docs/requirements/core.md"


def test_reports_markers_with_unknown_identifiers() -> None:
    tests = {"tests/core/test_a.py": "# SDD-EARS: CORE-001 CORE-002 CORE-999\n"}
    findings = check(REQUIREMENTS, tests)
    assert len(findings) == 1
    assert "CORE-999" in findings[0].message


def test_rejects_test_files_without_marker() -> None:
    tests = {"tests/core/test_a.py": "# SDD-EARS: CORE-001 CORE-002\n", "tests/core/test_b.py": ""}
    findings = check(REQUIREMENTS, tests)
    assert [f.path for f in findings] == ["tests/core/test_b.py"]


def test_main_reads_requirements_and_tracked_tests(repo: Path, git: GitRunner) -> None:
    write(repo, "docs/requirements/core.md", "- **CORE-001** The ledger shall store events.\n")
    write(repo, "tests/core/test_ledger.py", "# SDD-EARS: CORE-001\n")
    write(repo, "tests/core/conftest.py", "")
    git(repo, "add", ".")
    assert main([], root=repo) == 0

    write(
        repo,
        "docs/requirements/core.md",
        "- **CORE-001** The ledger shall store events.\n"
        "- **CORE-002** The ledger shall sign events.\n",
    )
    assert main([], root=repo) == 1
