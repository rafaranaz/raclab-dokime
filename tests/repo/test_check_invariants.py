# SDD-EARS: REPO-178 REPO-179 REPO-180 REPO-181 REPO-182 REPO-183 REPO-184 REPO-185 REPO-186
from pathlib import Path

from tools._common import DEFAULT_ROOT
from tools.check_invariants import README_PATH, check, main

FIXTURES = Path(__file__).parent / "fixtures"
HEADER = "| Id | Invariant | Enforced today by | Not yet |\n|---|---|---|---|\n"
ROADMAP = (
    "| Block | What |\n|---|---|\n"
    "| A · Audit | x |\n| B · Hold out | x |\n| C · Launch | x |\n\n"
    "| Milestone | What |\n|---|---|\n"
    "| A1 Contract | x |\n| R2b Sentinel | x |\n| R6 Course | x |\n\n"
    "**A1 is done.** Text.\n\n"
    "**B4 closed on 2026-11-25, and block B with it**, with version 0.2.0.\n"
)
REQUIREMENTS = frozenset({"CORE-001", "VERIFY-003"})


def readme(*rows: str) -> str:
    table = HEADER + "\n".join(rows)
    return "# Architecture\n\n## Invariants\n\nText.\n\n" + table + "\n\n## Next\n"


def messages(text: str, roadmap: str = ROADMAP) -> list[str]:
    return [finding.message for finding in check(text, roadmap, REQUIREMENTS)]


def test_accepts_rows_with_a_requirement_or_an_open_target() -> None:
    text = readme(
        "| INV-1 | One | CORE-001: what it makes hold | The rest, R6 |",
        "| INV-2 | Two | VERIFY-003, CORE-001 | — |",
        "| INV-3 | Three | Nothing | A test, block C, and a search, R2b |",
    )
    assert messages(text) == []


def test_reports_the_table_with_one_column_of_enforcement() -> None:
    text = "# Architecture\n\n" + (FIXTURES / "invariants-one-column.txt").read_text("utf-8")
    assert messages(text) == [
        "no table under '## Invariants' with the columns "
        "Id | Invariant | Enforced today by | Not yet"
    ]


def test_reports_a_file_without_the_heading() -> None:
    assert len(messages("# Architecture\n\n" + HEADER)) == 1


def test_reports_an_id_in_two_rows() -> None:
    text = readme("| INV-1 | One | CORE-001 | — |", "| INV-1 | Again | CORE-001 | — |")
    assert messages(text) == ["INV-1: appears in 2 rows"]


def test_reports_a_row_with_neither_a_requirement_nor_a_target() -> None:
    text = readme("| INV-1 | One | Nothing | — |")
    assert messages(text) == ["INV-1: names no requirement and its 'Not yet' is '—'"]


def test_reports_a_requirement_that_no_file_defines() -> None:
    text = readme("| INV-1 | One | CORE-001, CORE-999 | — |")
    assert messages(text) == ["INV-1: names CORE-999, which no file of docs/requirements/ defines"]


def test_does_not_take_decisions_or_invariants_for_requirements() -> None:
    text = readme("| INV-1 | One | CORE-001, as ADR-0067 says, with INV-2 | — |")
    assert messages(text) == []


def test_reports_a_not_yet_without_a_target() -> None:
    text = readme("| INV-1 | One | CORE-001 | A replay command, some day |")
    assert messages(text) == ["INV-1: 'Not yet' names no block and no milestone"]


def test_reports_a_block_that_the_roadmap_does_not_hold() -> None:
    text = readme("| INV-1 | One | CORE-001 | A thing, block Z |")
    assert messages(text) == ["INV-1: names block Z, which docs/ROADMAP.md does not hold"]


def test_reports_a_milestone_that_the_roadmap_does_not_hold() -> None:
    text = readme("| INV-1 | One | CORE-001 | A thing, R9 |")
    assert messages(text) == ["INV-1: names R9, which docs/ROADMAP.md does not hold"]


def test_reports_a_milestone_that_is_done() -> None:
    text = readme("| INV-1 | One | CORE-001 | A thing, A1 |")
    assert messages(text) == ["INV-1: points to A1, which is closed"]


def test_reports_a_block_closed_with_its_last_milestone() -> None:
    text = readme("| INV-1 | One | CORE-001 | A thing, block B |")
    assert messages(text) == ["INV-1: points to block B, which is closed"]


def test_reports_a_block_closed_by_its_own_text() -> None:
    roadmap = ROADMAP + "\n**Block A closed on 2026-11-18**, with version 0.1.0.\n"
    text = readme("| INV-1 | One | CORE-001 | A thing, block A |")
    assert messages(text, roadmap) == ["INV-1: points to block A, which is closed"]


def test_reports_a_milestone_closed_on_a_date() -> None:
    roadmap = ROADMAP + "\n**R2b closed on 2026-12-01.** Text.\n"
    text = readme("| INV-2 | Two | Nothing | A search, R2b |")
    assert messages(text, roadmap) == ["INV-2: points to R2b, which is closed"]


def test_an_open_milestone_is_not_closed_by_a_mention() -> None:
    roadmap = ROADMAP + "\nThe search of **R2b** comes before R3.\n"
    text = readme("| INV-2 | Two | Nothing | A search, R2b |")
    assert messages(text, roadmap) == []


def test_the_table_of_this_repository_passes() -> None:
    assert main([], DEFAULT_ROOT) == 0
    assert (DEFAULT_ROOT / README_PATH).is_file()
