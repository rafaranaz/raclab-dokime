# SDD-EARS: INTERFACES-020 INTERFACES-021 INTERFACES-040
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

from dokime.interfaces.cli import main
from tests.contract.contracts import VALID
from tests.interfaces.commands import contract_check


def test_a_file_that_does_not_exist_is_one_error_finding(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_path / "nowhere.yaml"
    code = main(["contract", "check", str(missing)])
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].startswith(f"{missing}: ERROR unreadable-file: ")
    assert lines[1:] == ["ERROR: 1 finding (1 error)"]
    assert code == 2


def test_a_directory_is_one_error_finding(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["contract", "check", str(tmp_path)])
    assert capsys.readouterr().out.splitlines()[0].startswith(f"{tmp_path}: ERROR unreadable-file")
    assert code == 2


def test_a_file_that_is_not_utf_8_text_is_one_error_finding(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "contract.yaml"
    path.write_bytes("story: caf\xe9\n".encode("latin-1"))
    code = main(["contract", "check", str(path)])
    out = capsys.readouterr().out.splitlines()
    assert out[0].startswith(f"{path}: ERROR unreadable-file: ")
    assert "UTF-8" in out[0]
    assert code == 2


@pytest.mark.parametrize(
    "arguments",
    [
        [],
        ["contract"],
        ["contract", "check"],
        ["contract", "check", "a.yaml", "--format", "xml"],
        ["contract", "check", "a.yaml", "--colour"],
        ["contract", "verify", "a.yaml"],
        ["audit"],
    ],
)
def test_a_command_line_that_is_not_valid_writes_the_usage_to_the_error_output_and_exits_with_2(
    arguments: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as stopped:
        main(arguments)
    captured = capsys.readouterr()
    assert stopped.value.code == 2
    assert captured.out == ""
    assert "usage: dokime" in captured.err


def test_running_the_package_as_a_module_behaves_as_the_entry_function(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run = contract_check(VALID.replace("kind: preserve", "kind: keep"), tmp_path, capsys)
    as_module = subprocess.run(
        [sys.executable, "-m", "dokime.interfaces", "contract", "check", run.path],
        capture_output=True,
        text=True,
        check=False,
    )
    assert (as_module.returncode, as_module.stdout, as_module.stderr) == (run.code, run.out, "")


def test_the_module_exits_with_the_code_of_the_entry_function(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    run = contract_check(VALID.replace("y: cli", "y: http"), tmp_path, capsys)
    monkeypatch.setattr(sys, "argv", ["dokime", "contract", "check", run.path])
    with pytest.raises(SystemExit) as stopped:
        runpy.run_module("dokime.interfaces", run_name="__main__")
    assert stopped.value.code == run.code == 2
    assert capsys.readouterr().out == run.out
