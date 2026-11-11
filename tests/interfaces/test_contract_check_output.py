# SDD-EARS: INTERFACES-001 INTERFACES-002 INTERFACES-003 INTERFACES-004 INTERFACES-005
from pathlib import Path

import pytest

from tests.contract.contracts import VALID, line_of
from tests.interfaces.commands import contract_check

REAL = Path(__file__).parent.parent / "contract" / "fixtures"
THIRD = "  - id: no-examples-yet\n    kind: new\n    text: The system shall log every total.\n"
WITH_A_QUESTION = VALID.replace("\nexamples:", THIRD + "    source: written\n\nexamples:")


def test_a_valid_contract_writes_only_the_summary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run = contract_check(VALID, tmp_path, capsys)
    assert run.lines == ["PASS: no findings"]
    assert run.err == ""


def test_each_finding_is_one_line_in_the_order_of_the_check(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    text = WITH_A_QUESTION.replace("kind: preserve", "kind: keep").replace("story: i", "story: 7 i")
    run = contract_check(text, tmp_path, capsys)
    assert [line.split(" ")[2].rstrip(":") for line in run.lines[:-1]] == [
        "wrong-type",
        "unknown-value",
        "requirement-without-example",
    ]


def test_a_finding_is_written_with_its_path_line_verdict_code_and_message(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run = contract_check(VALID.replace("kind: preserve", "kind: keep"), tmp_path, capsys)
    line = line_of("kind: preserve")
    assert run.lines[0] == (
        f"{run.path}:{line}: FAIL unknown-value: 'kind' is one of: new, change, preserve"
    )


def test_the_other_lines_of_a_finding_are_named_at_the_end_of_its_message(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    two = VALID.replace("  - id: E-0002", "  - id: E-0001")
    first, second, third = (line_of(f"  - id: E-000{n}") for n in (1, 2, 3))
    run = contract_check(two, tmp_path, capsys)
    assert run.lines[0].startswith(f"{run.path}:{first}: FAIL duplicate-id: ")
    assert run.lines[0].endswith(f" (also line {second})")
    three = two.replace("  - id: E-0003", "  - id: E-0001")
    run = contract_check(three, tmp_path, capsys)
    assert run.lines[0].endswith(f" (also lines {second}, {third})")


def test_a_finding_without_a_line_is_written_with_the_path_alone(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run = contract_check("a: 1\n---\nb: 2\n", tmp_path, capsys)
    assert run.lines[0].startswith(f"{run.path}: FAIL not-one-document: ")


@pytest.mark.parametrize(
    ("text", "summary"),
    [
        (VALID.replace("kind: preserve", "kind: keep"), "FAIL: 1 finding (1 fail)"),
        (WITH_A_QUESTION, "ASK: 1 finding (1 ask)"),
        (
            WITH_A_QUESTION.replace("kind: preserve", "kind: keep").replace("y: cli", "y: http"),
            "ERROR: 3 findings (1 fail, 1 ask, 1 error)",
        ),
    ],
)
def test_the_last_line_gives_the_verdict_and_the_counts(
    text: str, summary: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert contract_check(text, tmp_path, capsys).lines[-1] == summary


def test_the_defects_seeded_in_a_real_contract_are_all_shown(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    text = (REAL / "naturalsize-carries-to-next-unit.contract.yaml").read_text(encoding="utf-8")
    first = text[text.index("  - id: E-") : text.index("  - id: E-", text.index("  - id: E-") + 1)]
    seeded = (
        text.replace("naturalsize shall express the size", "naturalsize expresses the size")
        .replace("\nexamples:", THIRD + "    source: written\n\nexamples:")
        .replace(first, first + first.replace("E-", "E-twin-", 1))
        .replace(
            "relations: []",
            first.replace("E-", "E-other-", 1).replace('"1.0 MB"', '"1000.0 kB"') + "relations: []",
        )
    )
    run = contract_check(seeded, tmp_path, capsys)
    shown = {line.split(" ")[2].rstrip(":") for line in run.lines[:-1]}
    assert shown == {
        "not-ears",
        "requirement-without-example",
        "duplicate-example",
        "contradictory-examples",
    }
    assert run.lines[-1].startswith("FAIL: ")
    assert run.code == 1
