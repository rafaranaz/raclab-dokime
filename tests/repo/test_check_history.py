# SDD-EARS: REPO-020 REPO-021
from pathlib import Path

import pytest

from tests.repo.conftest import GitRunner, write
from tools.check_history import main, scan_source

EXISTING = frozenset({"docs/ROADMAP.md", "CONTRIBUTING.md"})


@pytest.mark.parametrize(
    "comment",
    [
        "# fixed in T6.4 after review",
        "# see DT-82 for the background",
        "# behaviour changed in v0.88.150",
        "# decided on 2026-09-21",
        "# this used to call the old engine",
        "# real root cause of the crash",
    ],
)
def test_reports_history_markers_in_comments(comment: str) -> None:
    findings = scan_source(f"x = 1\n{comment}\n", "src/a.py", EXISTING)
    assert len(findings) == 1
    assert findings[0].line == 2
    assert findings[0].path == "src/a.py"


def test_reports_history_markers_in_docstrings() -> None:
    source = 'def f() -> None:\n    """Return nothing.\n\n    Added in v1.2.\n    """\n'
    findings = scan_source(source, "src/a.py", EXISTING)
    assert [f.line for f in findings] == [4]
    assert "v1.2" in findings[0].message


def test_ignores_markers_in_ordinary_strings_and_code() -> None:
    source = 'VERSION = "v1.2.3"\nDATE = "2026-01-01"\nname = "T6.4"\n'
    assert scan_source(source, "src/a.py", EXISTING) == []


def test_ignores_strings_split_across_lines_inside_brackets() -> None:
    source = 'call(\n    "first part "\n    "see v1.2 and missing.md"\n)\n'
    assert scan_source(source, "tests/test_a.py", EXISTING) == []


def test_accepts_requirement_identifiers_and_plain_explanations() -> None:
    source = "# SDD-EARS: REPO-020 REPO-021\n# Rejects headers longer than the limit.\n"
    assert scan_source(source, "tests/test_a.py", EXISTING) == []


def test_reports_references_to_missing_markdown_files() -> None:
    source = "# See docs/ROADMAP.md and docs/definicion/20_DISENO.md for details.\n"
    findings = scan_source(source, "src/a.py", EXISTING)
    assert len(findings) == 1
    assert "docs/definicion/20_DISENO.md" in findings[0].message


def test_ignores_bare_extensions_after_placeholders() -> None:
    source = "# Translations live next to the source as `<name>.es.md`.\n"
    assert scan_source(source, "tools/a.py", EXISTING) == []


def test_resolves_references_relative_to_the_file() -> None:
    source = "# See ../ROADMAP.md.\n"
    assert scan_source(source, "docs/adr/a.py", EXISTING | {"docs/ROADMAP.md"}) == []


def test_main_scans_tracked_python_files(repo: Path, git: GitRunner) -> None:
    write(repo, "src/ok.py", "# Explains what it does.\nx = 1\n")
    write(repo, "notes/ignored.py", "# T1.1 outside the scanned folders\n")
    git(repo, "add", ".")
    assert main([], root=repo) == 0

    write(repo, "tools/bad.py", "# Changed in T1.1.\n")
    git(repo, "add", ".")
    assert main([], root=repo) == 1


def test_reports_files_it_cannot_tokenize() -> None:
    findings = scan_source('"""never closed\n', "src/a.py", EXISTING)
    assert len(findings) == 1
    assert "tokenize" in findings[0].message
