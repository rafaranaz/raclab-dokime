# SDD-EARS: CORPUS-103 CORPUS-104 CORPUS-105 CORPUS-106 CORPUS-107
"""The runner and the test file that the conversion of R2 writes, run on a small project of its
own, never on the corpus."""

import os
import stat
import subprocess
import sys
from pathlib import Path

from dokime.sandbox.podman import _request
from dokime.verify.examples import request_of
from tests.corpus.contrast import runner
from tests.corpus.contrast.sample import IDS, converted, examples, project

__all__ = ["converted", "project"]


def run(converted: Path, project: Path, example: str) -> int:
    done = subprocess.run(
        [sys.executable, str(converted / "run.py"), example],
        cwd=project,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    return done.returncode


def test_the_runner_gives_the_request_that_the_podman_adapter_gives() -> None:
    for example in examples().values():
        assert runner.request_json(example) == _request(request_of(example))


def test_an_example_that_holds_exits_0_and_one_that_does_not_exits_1(
    converted: Path, project: Path
) -> None:
    codes = {name: run(converted, project, name) for name in IDS}
    assert codes == {"E-1": 0, "E-2": 1, "E-3": 0, "E-4": 0, "E-5": 0, "E-6": 0}


def interpreter(project: Path, script: str) -> Path:
    path = project / ".venv" / "bin" / "python"
    path.parent.mkdir(parents=True)
    path.write_text(f"#!/bin/sh\n{script}\n")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def test_a_program_that_observes_and_ends_with_an_error_exits_2(
    converted: Path, project: Path
) -> None:
    marker = project / "used"
    interpreter(project, f'touch "{marker}"\nexit 9')
    assert run(converted, project, "E-1") == 2
    assert marker.exists()


def test_the_python_of_the_environment_of_the_project_runs_the_program(
    converted: Path, project: Path
) -> None:
    marker = project / "used"
    interpreter(project, f'touch "{marker}"\nexec "{sys.executable}" "$@"')
    assert run(converted, project, "E-1") == 0
    assert marker.exists()


def test_the_test_file_gives_one_test_for_each_example(converted: Path, project: Path) -> None:
    report = project / "report.json"
    environment = {k: v for k, v in os.environ.items() if not k.startswith("PYTEST")}
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "--rootdir",
            str(project),
            f"--junitxml={report}",
            str(converted / "test_dokime_examples.py"),
        ],
        cwd=project,
        env=environment,
        capture_output=True,
        timeout=300,
        check=False,
    )
    text = report.read_text()
    assert text.count("<testcase ") == len(IDS)
    assert text.count("<failure") == 1
    assert "E-2" in text.split("<failure")[0].rsplit("<testcase ", 1)[1]
