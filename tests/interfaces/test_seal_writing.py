# SDD-EARS: INTERFACES-160 INTERFACES-161 INTERFACES-162 INTERFACES-163 INTERFACES-172
from pathlib import Path

import pytest

from dokime.contract.check import check
from dokime.core.layout import contract_path, sealed_path
from tests.interfaces.seals import HELD, STORY, contract, git, opened, place, seal
from tests.sandbox.engines import require


@pytest.fixture(autouse=True)
def needs_git() -> None:
    require("git")


def test_the_tree_receives_only_the_visible_contract_and_the_batch(tmp_path: Path) -> None:
    where = place(tmp_path)
    assert seal(where) == 0
    changed = git(where.project, "status", "--porcelain", "--untracked-files=all").splitlines()
    assert sorted(line[3:] for line in changed) == sorted(
        [str(contract_path(STORY)), str(sealed_path(STORY))]
    )
    written = check((where.project / str(contract_path(STORY))).read_text())
    assert written.contract is not None
    batch = opened(where)
    held = {h.id for h in written.contract.held_out}
    assert held == {e.id for e in batch.examples}
    assert {h.case for h in written.contract.held_out} == {"c1", "c3"}
    assert held.isdisjoint(e.id for e in written.contract.examples)


def test_no_file_of_the_tree_holds_the_text_of_a_held_out_example(tmp_path: Path) -> None:
    where = place(tmp_path)
    assert seal(where) == 0
    held = {e.id for e in opened(where).examples}
    texts = [HELD[name] for name in held]
    for path in where.project.rglob("*"):
        if path.is_file() and ".git" not in path.parts:
            content = path.read_bytes()
            for text in texts:
                assert text.encode() not in content, path


@pytest.mark.parametrize("inside", ["contract", "out"])
def test_a_contract_or_out_inside_the_tree_is_refused(
    tmp_path: Path, inside: str, capsys: pytest.CaptureFixture[str]
) -> None:
    where = place(tmp_path)
    if inside == "contract":
        moved = where.project / "approved.yaml"
        moved.write_text(where.approved.read_text())
        where.approved = moved
        git(where.project, "add", "--all")
        git(where.project, "commit", "--quiet", "--message", "in the tree")
    else:
        where.out = where.project / "out"
    assert seal(where) == 2
    assert "inside-the-tree" in capsys.readouterr().out
    assert not (where.project / str(sealed_path(STORY))).exists()


def test_an_out_that_is_not_empty_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    where = place(tmp_path)
    where.out.mkdir()
    (where.out / "something").write_text("x")
    assert seal(where) == 2
    assert "out-not-empty" in capsys.readouterr().out


def test_a_checkout_that_is_not_clean_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    where = place(tmp_path)
    (where.project / "src" / "p.py").write_text("changed\n")
    assert seal(where) == 2
    assert "not-a-clean-checkout" in capsys.readouterr().out


def test_a_contract_with_a_failing_finding_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    where = place(tmp_path)
    where.approved.write_text(contract().replace("format: 1", "format: 2"))
    assert seal(where) != 0
    assert not (where.project / str(sealed_path(STORY))).exists()
    assert "unknown-value" in capsys.readouterr().out


def test_a_contract_of_another_story_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    where = place(tmp_path)
    where.approved.write_text(contract(story="another-story"))
    assert seal(where) == 2
    assert "story-mismatch" in capsys.readouterr().out


def test_a_contract_already_split_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    where = place(tmp_path)
    split = contract() + "held_out:\n  - id: E-z9\n    requirement: R-add\n    case: c9\n"
    split += "    digest: sha256:" + "0" * 64 + "\n"
    where.approved.write_text(split)
    assert seal(where) == 2
    assert "already-split" in capsys.readouterr().out
