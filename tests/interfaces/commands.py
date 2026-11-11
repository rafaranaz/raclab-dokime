"""Helpers to run `contract check` on a text and read what it wrote."""

from dataclasses import dataclass
from pathlib import Path

import pytest

from dokime.interfaces.cli import main


@dataclass(frozen=True)
class Run:
    code: int
    out: str
    err: str
    path: str

    @property
    def lines(self) -> list[str]:
        return self.out.splitlines()


def contract_check(
    text: str, tmp_path: Path, capsys: pytest.CaptureFixture[str], *options: str
) -> Run:
    """Write the text to a contract file and run `contract check` on it."""
    path = tmp_path / "contract.yaml"
    path.write_text(text, encoding="utf-8")
    code = main(["contract", "check", str(path), *options])
    captured = capsys.readouterr()
    return Run(code=code, out=captured.out, err=captured.err, path=str(path))
