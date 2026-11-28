# SDD-EARS: CORPUS-120 CORPUS-127 CORPUS-128
"""The check of R2 without the strict-xfail test of mdformat, made after the results, and the
choice of the arms: on the small project of the tests of the command, on the adaptations as they
are, and on the plugin of pytest that deselects that test."""

import json
import os
import shlex
import subprocess
import sys
import tomllib
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from dokime.platform.sealed_store import AgeSealedStore
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
from tests.corpus.test_contrast_maintainer import TEST, opened, ran, spec, stand_in

__all__ = ["opened", "spec"]
PLUGIN = "dokime_strict_xfail"
"""The module of the plugin of pytest that the option lays in `.contrast/` and loads with `-p`."""
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
        assert words[0] == "PYTHONPATH=src"
        loaded = ["PYTHONPATH=src:.contrast", *words[1:-1], "-p", PLUGIN]
        assert shlex.split(test) == [*loaded, words[-1]]
        files = without_strict_xfail(one).adaptation["files"]
        assert f".contrast/{PLUGIN}.py" in files
        assert tomllib.loads(files["swarm.toml"])["checks"]["test"]["command"] == test
        assert shlex.split(check_command(test, [VISIBLE])) == [*loaded, VISIBLE]


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


def loads(command: str) -> int:
    """How many times the command loads the plugin."""
    words = shlex.split(command)
    return sum(1 for at, word in enumerate(words[:-1]) if (word, words[at + 1]) == ("-p", PLUGIN))


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
    assert [len(commands(record)) for record in records] == [2, 3]
    for record in records:
        assert all(loads(command) == 1 for command in commands(record))


def test_by_default_every_arm_runs_and_no_check_deselects_anything(
    spec: Spec,
    opened: tuple[AgeSealedStore, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    records, entries = main(mdformat_like(spec), [], opened, tmp_path, monkeypatch)
    assert [entry["arm"] for entry in entries] == ["S0", "S1", "S2"]
    assert all(entry["without_strict_xfail"] is False for entry in entries)
    assert all(PLUGIN not in command for record in records for command in commands(record))


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
    assert all(PLUGIN not in command for record in records for command in commands(record))


def test_an_arm_that_is_not_one_of_the_three_is_refused(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as refused:
        maintainer.main([str(tmp_path / "out"), str(tmp_path / "results.toml"), "--arm", "S3"])
    assert refused.value.code == 2


PARAMETERS = ["```\na\n```\n" + chr(0x2003) + "\n# A\n", "```\na\n```\n"]
"""The parameter of the strict-xfail test, and one that its node id begins the same way."""
TESTS = (
    f"import pytest\n\n\n@pytest.mark.parametrize('text', {PARAMETERS!r})\n"
    "def test_output_is_equal(text):\n    pass\n"
)


def test_the_plugin_deselects_that_test_and_no_other(tmp_path: Path) -> None:
    (first,) = of("mdformat")[:1]
    files = without_strict_xfail(first).adaptation["files"]
    (tmp_path / ".contrast").mkdir()
    (tmp_path / ".contrast" / f"{PLUGIN}.py").write_text(files[f".contrast/{PLUGIN}.py"])
    (tmp_path / "tests").mkdir()
    for name in ("test_api.py", "test_api_witness.py"):
        (tmp_path / "tests" / name).write_text(TESTS)

    def collected(*options: str) -> set[str]:
        done = subprocess.run(
            [
                *(sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q"),
                *("--collect-only", *options, "tests"),
            ],
            cwd=tmp_path,
            env={**os.environ, "PYTHONPATH": ".contrast"},
            capture_output=True,
            text=True,
            check=False,
        )
        return {line for line in done.stdout.splitlines() if "::" in line}

    every = collected()
    assert len(every) == 4
    assert set(every) - collected("-p", PLUGIN) == {XFAIL_NODE}
