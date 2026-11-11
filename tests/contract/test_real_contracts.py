# SDD-EARS: CONTRACT-003 CONTRACT-005 CONTRACT-020 CONTRACT-070 CONTRACT-080 CONTRACT-081
from pathlib import Path

import pytest

from dokime.contract.check import check
from dokime.core.verdicts import Verdict

FIXTURES = Path(__file__).parent / "fixtures"
REAL = {
    "clean-pr-description": 15,
    "escape-pipe-in-markdown-tables": 7,
    "naturalsize-carries-to-next-unit": 17,
}


def contract_text(story: str) -> str:
    return (FIXTURES / f"{story}.contract.yaml").read_text(encoding="utf-8")


@pytest.mark.parametrize(("story", "examples"), REAL.items())
def test_a_contract_written_by_hand_for_a_real_change_passes(story: str, examples: int) -> None:
    checked = check(contract_text(story))
    assert checked.findings == ()
    assert checked.verdict is Verdict.PASS
    assert checked.contract is not None
    assert checked.contract.story == story
    assert len(checked.contract.requirements) == 3
    assert len(checked.contract.examples) == examples


def test_every_defect_seeded_in_a_real_contract_is_reported_in_one_run() -> None:
    text = contract_text("naturalsize-carries-to-next-unit")
    first = text[text.index("  - id: E-") : text.index("  - id: E-", text.index("  - id: E-") + 1)]
    seeded = (
        text.replace(
            "naturalsize shall express the size in the next larger unit.",
            "naturalsize expresses the size in the next larger unit.",
        )
        .replace(
            "\nexamples:",
            "  - id: nobody-checks-this\n    kind: new\n"
            "    text: The formatter shall log every size.\n    source: written\n\nexamples:",
        )
        .replace(first, first + first.replace("E-", "E-twin-", 1))
        .replace(
            "relations: []",
            first.replace("E-", "E-other-", 1).replace('"1.0 MB"', '"1000.0 kB"') + "relations: []",
        )
    )
    assert seeded != text
    found = {finding.code for finding in check(seeded).findings}
    assert found == {
        "not-ears",
        "requirement-without-example",
        "duplicate-example",
        "contradictory-examples",
    }
