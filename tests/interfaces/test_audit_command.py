# SDD-EARS: INTERFACES-120 INTERFACES-121 INTERFACES-122 INTERFACES-123 INTERFACES-124
from pathlib import Path

import pytest

from dokime.interfaces.cli import main


def run(capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, list[str]]:
    code = main(["audit", *args])
    return code, capsys.readouterr().out.splitlines()


def arguments(tmp_path: Path, **changes: str) -> list[str]:
    patch = tmp_path / "change.patch"
    patch.write_text("diff\n")
    given = {
        "--project": str(tmp_path / "project"),
        "--base": "a" * 40,
        "--patch": str(patch),
        "--story": "add-one",
        "--out": str(tmp_path / "out"),
        **changes,
    }
    return [part for name, value in given.items() if value for part in (name, value)]


@pytest.mark.parametrize("both", [True, False])
def test_exactly_one_of_story_and_contract_is_given(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], both: bool
) -> None:
    given = arguments(
        tmp_path, **({"--contract": str(tmp_path / "c.yaml")} if both else {"--story": ""})
    )
    with pytest.raises(SystemExit) as raised:
        main(["audit", *given])
    assert raised.value.code == 2
    assert "story" in capsys.readouterr().err


def test_a_base_that_is_not_a_full_name_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, lines = run(capsys, *arguments(tmp_path, **{"--base": "HEAD~1"}))
    assert code == 2
    assert [line for line in lines if "ERROR" in line and "not-a-commit-name" in line]
    assert lines[-1] == "ERROR: 1 finding (1 error)"


def test_a_patch_that_cannot_be_read_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, lines = run(capsys, *arguments(tmp_path, **{"--patch": str(tmp_path / "absent")}))
    assert code == 2
    assert [line for line in lines if "ERROR unreadable-file" in line]


def test_an_out_that_is_not_empty_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "out"
    out.mkdir()
    (out / "left.txt").write_text("x")
    code, lines = run(capsys, *arguments(tmp_path))
    assert code == 2
    assert [line for line in lines if "ERROR out-not-empty" in line]
    assert sorted(p.name for p in out.iterdir()) == ["left.txt"]


@pytest.mark.parametrize("inside", ["", "results", "a/b"])
def test_an_out_in_the_project_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], inside: str
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    code, lines = run(capsys, *arguments(tmp_path, **{"--out": str(project / inside)}))
    assert code == 2
    assert [line for line in lines if "ERROR out-inside-project" in line]
    assert sorted(p.name for p in project.iterdir()) == []
