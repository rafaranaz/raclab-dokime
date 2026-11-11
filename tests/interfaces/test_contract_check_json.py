# SDD-EARS: INTERFACES-030 INTERFACES-031
import json
from pathlib import Path

import pytest

from tests.contract.contracts import VALID, line_of
from tests.interfaces.commands import contract_check


def test_json_is_one_document_with_the_file_the_verdict_and_the_findings(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run = contract_check(VALID, tmp_path, capsys, "--format", "json")
    assert json.loads(run.out) == {"file": run.path, "verdict": "PASS", "findings": []}
    assert run.code == 0


def test_json_gives_the_code_verdict_message_and_lines_of_each_finding(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    text = VALID.replace("  - id: E-0002", "  - id: E-0001").replace("y: cli", "y: http")
    run = contract_check(text, tmp_path, capsys, "--format", "json")
    document = json.loads(run.out)
    assert document["verdict"] == "ERROR"
    assert [sorted(finding) for finding in document["findings"]] == [
        ["code", "lines", "message", "verdict"]
    ] * 2
    duplicate, unsupported = document["findings"]
    assert (duplicate["code"], duplicate["verdict"]) == ("duplicate-id", "FAIL")
    assert duplicate["lines"] == [line_of("  - id: E-0001"), line_of("  - id: E-0002")]
    assert (unsupported["code"], unsupported["verdict"]) == ("not-supported-yet", "ERROR")
    assert isinstance(unsupported["message"], str)
    assert run.code == 2


def test_the_text_format_is_the_default_and_can_be_asked_for(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    default = contract_check(VALID, tmp_path, capsys)
    asked = contract_check(VALID, tmp_path, capsys, "--format", "text")
    assert default.out == asked.out == "PASS: no findings\n"
