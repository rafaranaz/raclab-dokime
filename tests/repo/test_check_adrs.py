# SDD-EARS: REPO-090 REPO-091 REPO-092
from pathlib import Path

from tests.repo.conftest import GitRunner, write
from tools.check_adrs import check_records, main

INDEX = (
    "| No. | Decision | Status |\n|---|---|---|\n"
    "| [0002](0002-old.md) | Old | Superseded by 0008 |\n"
    "| [0008](0008-new.md) | New | Accepted |\n"
)
OLD = "# ADR-0002 · Old\n\n**Status:** superseded by [ADR-0008](0008-new.md)\n\n## Context\nx\n"
NEW = (
    "# ADR-0008 · New\n\n**Status:** accepted\n\n## Decision\nx\n\n"
    "## Basis\nA study.\n\n## Consequences\ny\n"
)


def messages(records: dict[str, str], index: str = INDEX) -> list[tuple[str, str]]:
    return [(f.path, f.message) for f in check_records(records, index)]


def test_accepts_records_that_state_their_basis_and_match_the_index() -> None:
    records = {"docs/adr/0002-old.md": OLD, "docs/adr/0008-new.md": NEW}
    assert messages(records) == []


def test_reports_a_record_from_0008_on_without_a_basis_section() -> None:
    text = NEW.replace("## Basis\nA study.\n\n", "")
    assert messages({"docs/adr/0008-new.md": text}) == [
        ("docs/adr/0008-new.md", "no Basis section with text")
    ]


def test_reports_a_basis_section_without_text() -> None:
    text = NEW.replace("A study.\n", "")
    assert messages({"docs/adr/0008-new.md": text}) == [
        ("docs/adr/0008-new.md", "no Basis section with text")
    ]


def test_does_not_require_a_basis_before_0008() -> None:
    assert messages({"docs/adr/0002-old.md": OLD}) == []


def test_ignores_files_that_are_not_decision_records() -> None:
    assert messages({"docs/adr/README.md": INDEX}) == []


def test_reports_a_record_without_a_row_in_the_index() -> None:
    text = NEW.replace("ADR-0008", "ADR-0009")
    assert messages({"docs/adr/0009-other.md": text}) == [
        ("docs/adr/0009-other.md", "no row in the index docs/adr/README.md")
    ]


def test_reports_both_statuses_when_they_differ() -> None:
    text = NEW.replace("accepted", "proposed")
    assert messages({"docs/adr/0008-new.md": text}) == [
        ("docs/adr/0008-new.md", "status 'proposed' differs from the index, which says 'accepted'")
    ]


def test_reports_a_record_without_a_status_line() -> None:
    text = NEW.replace("**Status:** accepted\n\n", "")
    assert messages({"docs/adr/0008-new.md": text}) == [
        ("docs/adr/0008-new.md", "status 'none' differs from the index, which says 'accepted'")
    ]


def test_main_reads_english_records_and_skips_translations(repo: Path, git: GitRunner) -> None:
    write(repo, "docs/adr/README.md", INDEX)
    write(repo, "docs/adr/0002-old.md", OLD)
    write(repo, "docs/adr/0008-new.md", NEW)
    write(repo, "docs/adr/0008-new.es.md", "# ADR-0008\n\n**Estado:** aceptada\n")
    git(repo, "add", ".")
    assert main([], root=repo) == 0
    write(repo, "docs/adr/0008-new.md", NEW.replace("accepted", "proposed"))
    assert main([], root=repo) == 1
