# SDD-EARS: INTERFACES-010 INTERFACES-011 INTERFACES-012 INTERFACES-013
from pathlib import Path

import pytest

from tests.contract.contracts import VALID
from tests.interfaces.commands import contract_check
from tests.interfaces.test_contract_check_output import WITH_A_QUESTION


def test_pass_exits_with_0(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert contract_check(VALID, tmp_path, capsys).code == 0


def test_fail_exits_with_1(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert contract_check(VALID.replace("kind: preserve", "kind: keep"), tmp_path, capsys).code == 1


def test_error_exits_with_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert contract_check(VALID.replace("y: cli", "y: http"), tmp_path, capsys).code == 2


def test_ask_exits_with_3(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert contract_check(WITH_A_QUESTION, tmp_path, capsys).code == 3


def test_a_failure_with_a_question_exits_as_a_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    text = WITH_A_QUESTION.replace("kind: preserve", "kind: keep")
    assert contract_check(text, tmp_path, capsys).code == 1
