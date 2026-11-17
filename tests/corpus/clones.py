"""The clones of the projects of the corpus, and whether the tests of the corpus are asked for.

The tests that need the network run only when `DOKIME_CORPUS=1` asks for them, which the job
`corpus` of CI does (ADR-0052).
"""

import os
import subprocess
from pathlib import Path

import pytest

from tests.corpus.projects import Project

ASKED = "DOKIME_CORPUS"
CLONES = "DOKIME_CORPUS_CLONES"
"""The directory where the job corpus has cloned each project once, under its name."""


def asked_for() -> bool:
    return os.environ.get(ASKED) == "1"


def skip_unless_asked() -> None:
    if not asked_for():
        pytest.skip(
            f"the tests of the corpus that need the network run when {ASKED}=1 asks for them"
        )


def clone(project: Project, into: Path) -> Path:
    """Clone the repository of a project with its whole history, from the clone of the job when
    there is one."""
    address = project.source["repository"]
    clones = os.environ.get(CLONES)
    if clones and (Path(clones) / project.name).is_dir():
        address = str(Path(clones) / project.name)
    done = subprocess.run(
        ["git", "clone", "--quiet", address, str(into)],
        capture_output=True,
        text=True,
        check=False,
        timeout=600,
    )
    if done.returncode != 0:
        pytest.fail(f"network: cloning {address} failed: {done.stderr.strip()}")
    return into
