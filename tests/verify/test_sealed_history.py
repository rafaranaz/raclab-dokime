# SDD-EARS: VERIFY-171 VERIFY-172 VERIFY-173 VERIFY-174 VERIFY-170
import dataclasses

from dokime.core.repository import CommitName, FileVersion, RefusalError, RepoPath
from dokime.core.verdicts import Verdict
from tests.verify.doubles import HistoryDouble
from tests.verify.gates import codes
from tests.verify.sealed_contracts import (
    BASE,
    TEXTS,
    batch_of,
    held,
    history_of,
    partner,
    published_before,
    run,
    split,
)

PAIR = (("E-h1", held("E-h1")), ("E-h2", held("E-h2")))
PASSING: dict[str, object] = {"E-h1": 2, "E-h2": 2}


def test_the_seal_as_it_was_made_passes_with_the_entries_of_held_out_in_the_history() -> None:
    contract, sealed = split(*PAIR)
    asked: list[tuple[CommitName, RepoPath]] = []

    def history(base: CommitName) -> HistoryDouble:
        double = history_of(contract, base)
        double.asked = asked
        return double

    result, observer = run(contract, batch_of(contract, sealed), PASSING, history=history)
    assert result.findings == ()
    assert len(observer.calls) == 1
    assert "held_out:\n  - id: E-h1" in TEXTS[id(contract)]
    path = RepoPath(".dokime/changes/S-1/contract.yaml")
    assert {p for _, p in asked} == {path}
    assert CommitName(BASE) in {start for start, _ in asked}


def test_a_base_of_the_batch_out_of_the_history_of_the_change_is_a_mismatch() -> None:
    contract, sealed = split(*PAIR)
    result, observer = run(contract, batch_of(contract, sealed), PASSING, ancestors=())
    assert codes(list(result.findings)) == [("sealed-batch-mismatch", Verdict.ERROR)]
    assert observer.calls == []


def test_examples_kept_visible_that_were_not_published_from_the_base_are_a_mismatch() -> None:
    contract, sealed = split(*PAIR)

    def history(base: CommitName) -> HistoryDouble:
        double = history_of(contract, base)
        before = published_before(contract).replace(held("E-q2", case="c-pub"), "")
        double.versions_from[CommitName(BASE)] = (FileVersion(CommitName(BASE), before.encode()),)
        return double

    result, observer = run(contract, batch_of(contract, sealed), PASSING, history=history)
    assert codes(list(result.findings)) == [("sealed-batch-mismatch", Verdict.ERROR)]
    assert observer.calls == []


def test_an_example_published_from_the_base_that_the_batch_does_not_keep_is_a_mismatch() -> None:
    contract, sealed = split(*PAIR)

    def history(base: CommitName) -> HistoryDouble:
        double = history_of(contract, base)
        before = published_before(contract) + held("E-s1", case="c-single")
        double.versions_from[CommitName(BASE)] = (FileVersion(CommitName(BASE), before.encode()),)
        return double

    result, observer = run(contract, batch_of(contract, sealed), PASSING, history=history)
    assert codes(list(result.findings)) == [("sealed-batch-mismatch", Verdict.ERROR)]
    assert observer.calls == []


def leaked(contract_text: str, example: str, base: CommitName) -> FileVersion:
    """A version in the history of the change that has a held-out example in clear."""
    return FileVersion(base, (contract_text.split("held_out:")[0] + example).encode())


def test_a_held_out_example_published_since_the_seal_is_an_error_at_its_entry() -> None:
    contract, sealed = split(*PAIR)

    def history(base: CommitName) -> HistoryDouble:
        double = history_of(contract, base)
        text = TEXTS[id(contract)]
        double.versions_from[base] = (
            leaked(text, held("E-h2"), base),
            *double.versions_from[base],
        )
        return double

    result, observer = run(contract, batch_of(contract, sealed), PASSING, history=history)
    assert codes(list(result.findings)) == [("held-out-published", Verdict.ERROR)]
    (finding,) = result.findings
    lines = {h.id: h.line for h in contract.held_out}
    assert finding.lines == (lines["E-h2"],)
    assert "E-h2" not in finding.message
    assert "replace" in finding.message
    assert "seal again" in finding.message
    assert observer.calls == []


def test_a_held_out_example_published_under_another_id_is_an_error() -> None:
    contract, sealed = split(*PAIR)
    copy = sealed[0].text.replace("id: E-h1", "id: E-copy")

    def history(base: CommitName) -> HistoryDouble:
        double = history_of(contract, base)
        double.versions_from[base] = (
            leaked(TEXTS[id(contract)], copy, base),
            *double.versions_from[base],
        )
        return double

    result, observer = run(contract, batch_of(contract, sealed), PASSING, history=history)
    assert codes(list(result.findings)) == [("held-out-published", Verdict.ERROR)]
    assert observer.calls == []


def test_a_refusal_of_the_history_is_an_error_never_a_pass() -> None:
    contract, sealed = split(*PAIR)

    def history(base: CommitName) -> HistoryDouble:
        return HistoryDouble(refusal=RefusalError("git-failed", "git log failed"))

    result, observer = run(contract, batch_of(contract, sealed), PASSING, history=history)
    assert codes(list(result.findings)) == [("git-failed", Verdict.ERROR)]
    assert observer.calls == []


def test_the_partners_are_the_examples_kept_visible() -> None:
    contract, sealed = split(*PAIR)
    assert batch_of(contract, sealed).kept_visible[:2] == (partner(0), partner(1))


def test_a_base_of_the_batch_that_is_not_a_commit_is_a_mismatch() -> None:
    contract, sealed = split(*PAIR)
    batch = dataclasses.replace(batch_of(contract, sealed), base="not a commit")
    result, observer = run(contract, batch, PASSING)
    assert codes(list(result.findings)) == [("sealed-batch-mismatch", Verdict.ERROR)]
    assert observer.calls == []
