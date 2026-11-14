"""Every temporary directory of the adapter goes under the directory of the test."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def temporary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    directory = tmp_path / "temporary"
    directory.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(directory))
    return directory
