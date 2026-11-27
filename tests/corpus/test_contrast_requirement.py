# SDD-EARS: CORPUS-124 CORPUS-125
"""The requirement that S1 and S2 give swarm-verify, and the directory of the work of a run; on the
small project of the tests of the command, never on the corpus."""

from pathlib import Path

import pytest

from dokime.platform.sealed_store import AgeSealedStore
from tests.corpus.contrast import maintainer
from tests.corpus.contrast.maintainer import Spec, run_arm
from tests.corpus.contrast.runs import VISIBLE
from tests.corpus.test_contrast_maintainer import opened, ran, run, spec, stand_in

__all__ = ["opened", "spec"]
VISIBLE_IDS = ["E-1", "E-2", "E-3", "E-4", "E-5", "E-6"]
TEXT = "When the function is called with two numbers, the function shall return their sum."


def requirement(evidence: list[str]) -> dict[str, object]:
    return {
        "id": "R1",
        "text": TEXT,
        "source": "user",
        "kind": "fix",
        "required": True,
        "evidence": {"tests": [{"name": name} for name in evidence]},
    }


def test_s0_gives_no_requirement(
    spec: Spec,
    opened: tuple[AgeSealedStore, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert run(spec, "S0", opened, tmp_path, monkeypatch)["request"]["requirements"] == []


def test_s1_gives_one_required_fix_with_the_sealed_check_bound_to_it(
    spec: Spec,
    opened: tuple[AgeSealedStore, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = run(spec, "S1", opened, tmp_path, monkeypatch)["request"]
    assert request["requirements"] == [requirement([])]
    assert [check["requirements"] for check in request["sealed"]["checks"]] == [["R1"]]


def test_s2_gives_one_required_fix_with_the_visible_tests_as_its_evidence(
    spec: Spec,
    opened: tuple[AgeSealedStore, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = run(spec, "S2", opened, tmp_path, monkeypatch)["request"]
    module = VISIBLE.replace("/", ".") + ".test_dokime_examples"
    names = [f"{module}::test_dokime_example[{name}]" for name in VISIBLE_IDS]
    assert request["requirements"] == [requirement(names)]
    assert [check["requirements"] for check in request["sealed"]["checks"]] == [["R1"]]


def test_the_work_of_a_run_is_made_in_the_directory_given(
    spec: Spec,
    opened: tuple[AgeSealedStore, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper, log = stand_in(tmp_path, monkeypatch)
    work = tmp_path / "work"
    work.mkdir()
    entry = run_arm(spec, "S1", opened[0].open, tmp_path / "out", helper, work=work)
    assert entry.failure == ""
    (record,) = ran(log)
    assert Path(record["request"]["repository"]).is_relative_to(work)
    assert Path(record["home"]).is_relative_to(work)
    assert list(work.iterdir()) == []


def test_a_work_directory_that_does_not_exist_is_created(
    opened: tuple[AgeSealedStore, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    helper, log = stand_in(tmp_path, monkeypatch)
    identity = tmp_path / "identity" / "identity.age"
    work = tmp_path / "missing" / "work"
    code = maintainer.main(
        [
            *(str(tmp_path / "out"), str(tmp_path / "results.toml")),
            *("--work", str(work), "--case", "no/such-case"),
        ],
        environ={"DOKIME_CORPUS_IDENTITY": str(identity)},
        passphrase=lambda: "a disposable passphrase",
        helper=helper,
    )
    assert code == 0
    assert work.is_dir()
    assert ran(log) == []
