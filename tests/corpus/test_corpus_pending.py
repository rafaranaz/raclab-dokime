# SDD-EARS: CORPUS-073 CORPUS-074 CORPUS-091
import tomllib
from pathlib import Path

from tests.corpus import test_corpus_audit
from tests.corpus.cases import CASES, PENDING, RUNNABLE, WITHDRAWN

HERE = Path(__file__).parent


def test_the_pending_cases_are_cases_of_the_corpus_listed_once() -> None:
    listed = tomllib.loads((HERE / "pending.toml").read_text())["pending"]
    assert isinstance(listed, list)
    assert len(listed) == len(set(listed))
    assert set(listed) <= {case.key for case in CASES}
    assert tuple(listed) == PENDING


def test_the_audit_runs_every_case_but_the_pending_ones() -> None:
    assert [case.key for case in RUNNABLE] == [
        case.key for case in CASES if case.key not in PENDING and case.key not in WITHDRAWN
    ]
    test = test_corpus_audit.test_a_case_gets_its_expected_verdict_at_its_gate
    attribute = "pytestmark"
    marks = getattr(test, attribute)
    (parametrized,) = [m for m in marks if m.name == "parametrize"]
    assert tuple(parametrized.args[1]) == RUNNABLE


def test_a_list_with_no_case_is_not_an_error() -> None:
    assert tomllib.loads("pending = []\n")["pending"] == []
