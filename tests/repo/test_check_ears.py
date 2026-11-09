# SDD-EARS: REPO-030 REPO-031 REPO-032 REPO-033
from pathlib import Path

import pytest

from tests.repo.conftest import write
from tools.check_ears import check_file, check_statement, main, parse_requirements


@pytest.mark.parametrize(
    "statement",
    [
        "The ledger shall store every event.",
        "When a gate rejects an attempt, the runner shall route to the state named by the gate.",
        "While a run is paused, the runner shall reject new activities.",
        "While a run is paused, when a human answers, the runner shall resume the run.",
        "If the sandbox has no network, then the runner shall report the missing dependency.",
        "Where mutation testing is enabled, the hardening gate shall report surviving mutants.",
    ],
)
def test_accepts_each_ears_template(statement: str) -> None:
    assert check_statement(statement) == []


@pytest.mark.parametrize(
    "statement",
    [
        "The system must store events.",
        "Store every event.",
        "When a gate rejects an attempt the runner shall retry.",
        "If the sandbox has no network, the runner shall stop.",
        "The ledger shall store every event",
    ],
)
def test_rejects_statements_outside_the_templates(statement: str) -> None:
    errors = check_statement(statement)
    assert any("template" in error for error in errors)


def test_rejects_vague_terms_and_names_them() -> None:
    errors = check_statement("The index shall answer queries quickly.")
    assert any("quickly" in error for error in errors)


def test_ignores_vague_terms_inside_code_spans() -> None:
    assert check_statement("The parser shall reject the `fast` keyword.") == []


def test_rejects_more_than_one_shall() -> None:
    errors = check_statement("The ledger shall store events and shall sign them.")
    assert any("shall" in error for error in errors)


def test_parses_requirement_lines_with_their_line_numbers() -> None:
    text = "# Title\n\n- **CORE-001** The ledger shall store every event.\n"
    assert parse_requirements(text) == [("CORE-001", "The ledger shall store every event.", 3)]


def test_rejects_duplicated_identifiers() -> None:
    text = (
        "- **CORE-001** The ledger shall store every event.\n"
        "- **CORE-001** The ledger shall sign every event.\n"
    )
    findings = check_file("docs/requirements/core.md", text)
    assert any("duplicated" in f.message for f in findings)


def test_rejects_identifiers_with_a_foreign_prefix() -> None:
    findings = check_file(
        "docs/requirements/core.md", "- **GRAPH-001** The ledger shall store every event.\n"
    )
    assert any("CORE-" in f.message for f in findings)


def test_rejects_malformed_requirement_lines() -> None:
    findings = check_file(
        "docs/requirements/core.md", "- **core-1** The ledger shall store every event.\n"
    )
    assert findings


def test_main_checks_every_requirements_file(tmp_path: Path) -> None:
    write(tmp_path, "docs/requirements/core.md", "- **CORE-001** The ledger shall store events.\n")
    assert main([], root=tmp_path) == 0
    write(tmp_path, "docs/requirements/graph.md", "- **GRAPH-001** Index fast.\n")
    assert main([], root=tmp_path) == 1
