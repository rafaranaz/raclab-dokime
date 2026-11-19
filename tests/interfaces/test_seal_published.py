# SDD-EARS: INTERFACES-167 INTERFACES-168 INTERFACES-169 INTERFACES-170 INTERFACES-171
from pathlib import Path

import pytest

from dokime.core.canonical import digest
from dokime.interfaces import seal_command
from dokime.verify.sealed import Batch
from tests.interfaces.seals import contract, events, example, git, opened, place, seal
from tests.sandbox.engines import require


@pytest.fixture(autouse=True)
def needs_git() -> None:
    require("git")


def test_an_example_already_in_the_history_by_id_stays_visible(tmp_path: Path) -> None:
    history = (contract(example("E-a1", "c1", 1)),)
    where = place(tmp_path, history=history)
    assert seal(where) == 0
    batch = opened(where)
    assert "E-a1" in batch.kept_visible
    assert "E-a2" in {e.id for e in batch.examples}


def test_an_example_already_in_the_history_by_content_stays_visible(tmp_path: Path) -> None:
    history = (contract(example("E-old", "other", 5)),)
    where = place(tmp_path, history=history)
    assert seal(where) == 0
    batch = opened(where)
    assert batch.kept_visible == ("E-c2",)
    assert "E-c1" in {e.id for e in batch.examples}


def test_a_case_with_every_example_published_holds_out_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    history = (contract(example("E-c1", "c3", 4) + example("E-c2", "c3", 5)),)
    where = place(tmp_path, history=history)
    assert seal(where) == 0
    batch = opened(where)
    reasons = {(u.case, u.reason) for u in batch.unheld}
    assert reasons == {("c2", "single-example"), ("c3", "all-published")}
    said = capsys.readouterr().err
    assert "E-c1" in said
    assert "all-published" in said
    assert "single-example" in said


def test_the_examples_kept_visible_do_not_depend_on_the_seed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    history = (contract(example("E-a1", "c1", 1) + example("E-old", "x", 5)),)
    kept = []
    for seed in (1, 2):
        monkeypatch.setattr(seal_command, "seed", lambda value=seed: value)
        where = place(tmp_path / str(seed), history=history)
        assert seal(where) == 0
        batch = opened(where)
        assert batch.seed == seed
        kept.append(batch.kept_visible)
    assert kept[0] == kept[1] == ("E-a1", "E-c2")


def test_the_randomness_of_the_batch_comes_from_the_system(tmp_path: Path) -> None:
    first, second = opened_after(tmp_path / "one"), opened_after(tmp_path / "two")
    assert len({e.salt for e in (*first.examples, *second.examples)}) == 4
    assert all(len(e.salt) == 16 for e in first.examples)
    assert first.canary.expected != second.canary.expected
    assert first.canary.id not in first.order


def opened_after(root: Path) -> Batch:
    where = place(root)
    assert seal(where) == 0
    return opened(where)


def test_the_batch_names_its_base(tmp_path: Path) -> None:
    where = place(tmp_path)
    head = git(where.project, "rev-parse", "HEAD")
    assert seal(where) == 0
    assert opened(where).base == head


def test_the_ledger_records_the_run(tmp_path: Path) -> None:
    where = place(tmp_path)
    head = git(where.project, "rev-parse", "HEAD")
    assert seal(where) == 0
    batch = opened(where)
    recorded = events(where)
    assert [e["type"] for e in recorded] == [
        "run.started",
        "human.asked",
        "human.answered",
        "run.finished",
    ]
    assert (recorded[0]["story"], recorded[0]["base"]) == ("add-one", head)
    assert recorded[2]["answer"] == "y"
    assert recorded[3]["verdict"] == "PASS"
    assert recorded[3]["seed"] == digest(batch.seed)
