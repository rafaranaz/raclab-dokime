# SDD-EARS: CORPUS-120 CORPUS-127 CORPUS-128
"""The check of R2 without the strict-xfail test of mdformat, made after the results, and the
choice of the arms: on the small project of the tests of the command, on the adaptations as they
are, and on the collection of the tests of mdformat at the base of its cases."""

import json
import shlex
import subprocess
import tomllib
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from dokime.platform.sealed_store import AgeSealedStore
from tests.corpus.cases import ACTIVE
from tests.corpus.clones import clone, skip_unless_asked
from tests.corpus.contrast import maintainer
from tests.corpus.contrast.maintainer import Spec, specs, without_strict_xfail
from tests.corpus.contrast.runs import (
    HELD_OUT_CHECK,
    VISIBLE,
    VISIBLE_CHECK,
    XFAIL,
    XFAIL_NODE,
    check_command,
)
from tests.corpus.projects import PROJECTS
from tests.corpus.test_contrast_maintainer import TEST, opened, ran, spec, stand_in
from tests.sandbox.engines import require

__all__ = ["opened", "spec"]
DESELECT = f"--deselect={XFAIL_NODE}"
HERE = Path(__file__).parent


def of(project: str) -> list[Spec]:
    return [found for found in specs() if found.key.partition("/")[0] == project]


def test_the_test_deselected_is_the_one_the_witness_takes_out_of_xfail() -> None:
    path, _, name = XFAIL_NODE.partition("::")
    assert f"{path.removesuffix('.py').replace('/', '.')}::{name}" == XFAIL
    assert "\n" not in XFAIL_NODE
    assert chr(0x2003) not in XFAIL_NODE
    assert "\\n" in XFAIL_NODE
    assert "\\u2003" in XFAIL_NODE


def test_the_command_of_mdformat_deselects_that_test_in_each_check() -> None:
    found = of("mdformat")
    assert len(found) == 8
    for one in found:
        given = str(one.adaptation["test"])
        test = str(without_strict_xfail(one).adaptation["test"])
        words = shlex.split(given)
        assert shlex.split(test) == [*words[:-1], DESELECT, words[-1]]
        swarm = tomllib.loads(without_strict_xfail(one).adaptation["files"]["swarm.toml"])
        assert swarm["checks"]["test"]["command"] == test
        assert shlex.split(check_command(test, [VISIBLE])) == [*words[:-1], DESELECT, VISIBLE]


def test_the_command_of_every_other_project_is_left_as_it_is() -> None:
    found = of("python-semver")
    assert found
    for one in found:
        assert without_strict_xfail(one) == one


def mdformat_like(spec: Spec) -> Spec:
    swarm = f"\n[verify]\nsetup = 'true'\n\n[checks]\ntest = {{ command = {json.dumps(TEST)} }}\n"
    files = {**spec.adaptation["files"], "swarm.toml": swarm}
    return replace(spec, key="mdformat/a-case", adaptation={**spec.adaptation, "files": files})


def main(
    spec: Spec,
    options: list[str],
    opened: tuple[AgeSealedStore, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Run the command on one spec with the options given: the requests the helper got, and the
    entries of the results."""
    helper, log = stand_in(tmp_path, monkeypatch)
    monkeypatch.setattr(maintainer, "specs", lambda clones, cases: [spec])
    identity = tmp_path / "identity" / "identity.age"
    results = tmp_path / "results.toml"
    code = maintainer.main(
        [str(tmp_path / "out"), str(results), *options],
        environ={"DOKIME_CORPUS_IDENTITY": str(identity)},
        passphrase=lambda: "a disposable passphrase",
        helper=helper,
    )
    assert code == 0
    return ran(log), tomllib.loads(results.read_text())["run"]


def commands(record: dict[str, Any]) -> list[str]:
    request = record["request"]
    checks = [*request["checks"], *(request["sealed"] or {"checks": []})["checks"]]
    project = tomllib.loads(record["swarm_toml"])["checks"]["test"]["command"]
    return [project, *(check["command"] for check in checks)]


def test_without_the_strict_xfail_every_check_of_mdformat_deselects_it(
    spec: Spec,
    opened: tuple[AgeSealedStore, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = ["--without-strict-xfail", "--arm", "S2", "--arm", "S1"]
    records, entries = main(mdformat_like(spec), options, opened, tmp_path, monkeypatch)
    assert [entry["arm"] for entry in entries] == ["S1", "S2"]
    assert all(entry["without_strict_xfail"] is True for entry in entries)
    s1, s2 = records
    assert [check["name"] for check in s1["request"]["sealed"]["checks"]] == [HELD_OUT_CHECK]
    assert [check["name"] for check in s2["request"]["checks"]] == [VISIBLE_CHECK]
    assert [check["name"] for check in s2["request"]["sealed"]["checks"]] == [HELD_OUT_CHECK]
    for record in records:
        found = commands(record)
        assert len(found) == 2
        assert all(shlex.split(command).count(DESELECT) == 1 for command in found)


def test_by_default_every_arm_runs_and_no_check_deselects_anything(
    spec: Spec,
    opened: tuple[AgeSealedStore, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    records, entries = main(mdformat_like(spec), [], opened, tmp_path, monkeypatch)
    assert [entry["arm"] for entry in entries] == ["S0", "S1", "S2"]
    assert all(entry["without_strict_xfail"] is False for entry in entries)
    assert all("--deselect" not in command for record in records for command in commands(record))


def test_another_project_with_the_option_runs_its_command_as_it_is(
    spec: Spec,
    opened: tuple[AgeSealedStore, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    other = replace(mdformat_like(spec), key="python-semver/a-case")
    options = ["--without-strict-xfail", "--arm", "S1"]
    records, entries = main(other, options, opened, tmp_path, monkeypatch)
    assert [(entry["arm"], entry["without_strict_xfail"]) for entry in entries] == [("S1", True)]
    assert all("--deselect" not in command for record in records for command in commands(record))


def test_an_arm_that_is_not_one_of_the_three_is_refused(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as refused:
        maintainer.main([str(tmp_path / "out"), str(tmp_path / "results.toml"), "--arm", "S3"])
    assert refused.value.code == 2


def collected(image: str, checkout: Path, *options: str) -> list[str]:
    done = subprocess.run(
        [
            *(require("podman"), "run", "--rm", "--network", "none"),
            *("-v", f"{checkout}:/dokime/project:ro", "-w", "/dokime/project", image),
            *("python", "-m", "pytest", "-p", "no:cacheprovider", "-q", "--collect-only"),
            *(*options, "tests"),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=600,
    )
    return [line for line in done.stdout.splitlines() if "::" in line]


def test_the_deselect_takes_out_that_test_and_no_other_at_the_base_of_mdformat(
    tmp_path: Path,
) -> None:
    skip_unless_asked()
    require("git")
    podman = require("podman")
    (project,) = [p for p in PROJECTS if p.name == "mdformat"]
    (base,) = {str(case.fields["base"]) for case in ACTIVE if case.project == "mdformat"}
    checkout = clone(project, tmp_path / "project")
    subprocess.run(["git", "-C", str(checkout), "checkout", "-q", base], check=True)
    image = subprocess.run(
        [podman, "build", "--quiet", "-f", str(project.directory / "Dockerfile")],
        cwd=project.directory,
        capture_output=True,
        text=True,
        check=True,
        timeout=900,
    ).stdout.strip()
    first = of("mdformat")[0]
    test = shlex.split(str(without_strict_xfail(first).adaptation["test"]))
    options = [word for word in test if word.startswith("--deselect")]
    assert options == [DESELECT]
    every = collected(image, checkout)
    kept = collected(image, checkout, *options)
    assert sorted(set(every) - set(kept)) == [XFAIL_NODE]
    assert set(kept) <= set(every)
    assert len(kept) == len(every) - 1
