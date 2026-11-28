# SDD-EARS: CORPUS-127
"""The check without the strict-xfail test of mdformat as swarm-verify runs it: each command of the
option through the `reportPlan` of swarm-verify 3.1.0, which attaches the reporter of pytest only to
a command with no syntax of the shell, and the command of S1 so attached, run with `/bin/sh -c` in
the image of the adaptation at the local copy of a good case with the witness file laid in it; a
command with no reporter runs as it is declared, as swarm-verify runs it (`per-test.js:44`)."""

import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from tests.corpus.cases import ACTIVE
from tests.corpus.clones import CLONES, asked_for, clone, skip_unless_asked
from tests.corpus.contrast import maintainer
from tests.corpus.contrast.maintainer import Spec, specs, without_strict_xfail
from tests.corpus.contrast.runs import HELD_OUT, VISIBLE, XFAIL, check_command, witness_tests
from tests.corpus.projects import PROJECTS
from tests.sandbox.engines import require

CONTRAST = Path(maintainer.__file__).parent
PLAN = CONTRAST / "node_modules" / "swarm-verify" / "dist" / "verify" / "report-plan.js"
CASE = "mdformat/drops-a-blank-paragraph-after-any-block"
REPORT = "/dokime/report.xml"
DEFAULT = "/dokime/default.xml"
PRINT_PLAN = """
const { reportPlan } = await import(process.argv[1]);
const plan = reportPlan(process.argv[2], {});
process.stdout.write(JSON.stringify(plan === null ? null : plan.command(process.argv[3])));
"""


def swarm_verify() -> None:
    """The package of the contrast installed, with `npm ci` where the corpus is asked for."""
    if PLAN.is_file():
        return
    if not asked_for():
        pytest.skip("swarm-verify is not installed in tests/corpus/contrast")
    subprocess.run([require("npm"), "ci", "--no-audit", "--no-fund"], cwd=CONTRAST, check=True)


def reported(command: str, report: str = REPORT) -> str | None:
    """The command as swarm-verify runs it, with the reporter of its runner, or None without one."""
    done = subprocess.run(
        [require("node"), "--input-type=module", "-e", PRINT_PLAN, PLAN.as_uri(), command, report],
        capture_output=True,
        text=True,
        check=True,
    )
    found: str | None = json.loads(done.stdout)
    return found


def mdformat_spec(clones: Path | None = None) -> Spec:
    (found,) = specs(clones, [case for case in ACTIVE if case.key == CASE])
    return without_strict_xfail(found)


def test_every_check_of_the_option_keeps_the_reporter_of_pytest() -> None:
    swarm_verify()
    test = str(mdformat_spec().adaptation["test"])
    for command in (test, check_command(test, [VISIBLE]), check_command(test, [HELD_OUT])):
        assert reported(command) is not None, command


def outcomes(report: Path) -> dict[str, str]:
    """Each test of a JUnit report of pytest, by the id swarm-verify gives it, and its outcome;
    none where the command wrote no report."""
    found: dict[str, str] = {}
    if not report.is_file():
        return found
    tree = ET.parse(report)  # noqa: S314 - written by pytest in the container of this test
    for case in tree.getroot().iter("testcase"):
        tags = {child.tag for child in case}
        outcome = "fail" if tags & {"failure", "error"} else "skip" if "skipped" in tags else "pass"
        found[f"{case.get('classname')}::{case.get('name')}"] = outcome
    return found


def test_in_s1_the_witness_test_runs_and_the_deselected_test_does_not(tmp_path: Path) -> None:
    skip_unless_asked()
    swarm_verify()
    require("git")
    podman = require("podman")
    (project,) = [p for p in PROJECTS if p.name == "mdformat"]
    clones = tmp_path / "clones"
    given = os.environ.get(CLONES)
    if given and (Path(given) / "mdformat").is_dir():
        clones = Path(given)
    else:
        clone(project, clones / "mdformat")
    spec = mdformat_spec(clones)
    (tmp_path / "work").mkdir()
    repository, base, _ = maintainer._mount(spec, tmp_path / "work", {})
    files, moved = maintainer._witness_files(spec, repository, base)
    for path, content in files.items():
        (repository / path).write_text(content)
    (witness,) = witness_tests(spec.turned_green, moved)
    test = str(spec.adaptation["test"])
    command = reported(test) or test
    default = str(
        specs(clones, [case for case in ACTIVE if case.key == CASE])[0].adaptation["test"]
    )
    every = reported(default, DEFAULT)
    assert every is not None
    script = f"{spec.adaptation['setup']} && {{ {every}; }}; {{ {command}; }}; true"
    subprocess.run(
        [
            *(podman, "run", "--rm", "-v", f"{repository}:/dokime", "-w", "/dokime"),
            *(str(spec.adaptation["image"]), "/bin/sh", "-c", script),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=1200,
    )
    ran = outcomes(repository / "report.xml")
    assert ran.get(witness) == "pass"
    assert XFAIL not in ran
    assert len(ran) > 4000
    run_by_default = outcomes(repository / "default.xml")
    assert XFAIL in run_by_default
    assert set(run_by_default) - set(ran) == {XFAIL}
    assert set(ran) <= set(run_by_default)
    shutil.rmtree(tmp_path / "work", ignore_errors=True)
