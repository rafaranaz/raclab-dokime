"""One pytest test for each converted example of a dokime contract.

The conversion copies this file as `test_dokime_examples.py`; each test runs `run.py` on its
example in a process of its own, from the working directory of pytest, the root of the project,
and passes only when it exits with 0.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
IDS = sorted(path.stem for path in (HERE / "examples").glob("*.json"))


@pytest.mark.parametrize("example", IDS)
def test_dokime_example(example: str) -> None:
    ended = subprocess.run(
        [sys.executable, str(HERE / "run.py"), example],
        cwd=os.getcwd(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert ended.returncode == 0, ended.stdout + ended.stderr
