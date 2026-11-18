# SDD-EARS: INTERFACES-154 INTERFACES-155
import importlib.metadata
import subprocess
import sys

import pytest

from dokime.interfaces.cli import main

DISTRIBUTION = "raclab-dokime"


def test_version_prints_dokime_and_the_installed_version(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as ended:
        main(["--version"])
    assert ended.value.code == 0
    written = capsys.readouterr()
    assert written.out == f"dokime {importlib.metadata.version(DISTRIBUTION)}\n"
    assert written.err == ""


def test_version_from_the_command_line() -> None:
    done = subprocess.run(
        [sys.executable, "-m", "dokime.interfaces", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0
    assert done.stdout == f"dokime {importlib.metadata.version(DISTRIBUTION)}\n"


def test_version_without_the_distribution_is_unversioned(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    asked: list[str] = []

    def missing(name: str) -> str:
        asked.append(name)
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, "version", missing)
    with pytest.raises(SystemExit) as ended:
        main(["--version"])
    assert ended.value.code == 0
    assert capsys.readouterr().out == "dokime unversioned\n"
    assert asked == [DISTRIBUTION]


def test_no_area_is_still_a_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as ended:
        main([])
    assert ended.value.code == 2
    assert capsys.readouterr().out == ""
