# SDD-EARS: CORPUS-040 CORPUS-041
"""Each patch of the corpus applies on its base, in a clone of its project."""

import subprocess
from pathlib import Path

import pytest

from tests.corpus.cases import CASES, Case
from tests.corpus.clones import clone, skip_unless_asked
from tests.corpus.projects import PROJECTS


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.key)
def test_the_patch_of_a_case_applies_on_its_base(tmp_path: Path, case: Case) -> None:
    skip_unless_asked()
    (project,) = [p for p in PROJECTS if p.name == case.project]
    checkout = clone(project, tmp_path / "project")
    base = str(case.fields["base"])
    subprocess.run(
        ["git", "-C", str(checkout), "checkout", "--quiet", "--detach", base],
        capture_output=True,
        check=True,
    )
    patch = case.directory / str(case.fields["patch"])
    done = subprocess.run(
        ["git", "-C", str(checkout), "apply", "--check", str(patch)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, f"the patch of {case.key} does not apply: {done.stderr.strip()}"
