# SDD-EARS: CORE-010 CORE-011 CORE-012 CORE-013 CORE-014 CORE-015 CORE-016
import pytest

from dokime.core.findings import Finding, summarise
from dokime.core.verdicts import Verdict


def finding(verdict: Verdict = Verdict.FAIL, code: str = "duplicate-key") -> Finding:
    return Finding(code=code, message="the key 'id' is repeated", verdict=verdict)


def test_a_finding_carries_code_message_verdict_and_lines() -> None:
    found = Finding(
        code="duplicate-key", message="the key 'id' is repeated", verdict=Verdict.FAIL, lines=(3, 7)
    )
    assert (found.code, found.message, found.verdict, found.lines) == (
        "duplicate-key",
        "the key 'id' is repeated",
        Verdict.FAIL,
        (3, 7),
    )


def test_the_lines_of_a_finding_may_be_empty() -> None:
    assert finding().lines == ()


@pytest.mark.parametrize("verdict", [Verdict.FAIL, Verdict.ASK, Verdict.ERROR])
def test_a_finding_may_carry_any_verdict_but_pass(verdict: Verdict) -> None:
    assert finding(verdict).verdict is verdict


def test_a_finding_with_the_verdict_pass_is_rejected_naming_the_verdict() -> None:
    with pytest.raises(ValueError, match="PASS"):
        finding(Verdict.PASS)


def test_a_finding_with_an_empty_code_is_rejected_naming_the_field() -> None:
    with pytest.raises(ValueError, match="code"):
        Finding(code="", message="something", verdict=Verdict.FAIL)


def test_a_finding_with_an_empty_message_is_rejected_naming_the_field() -> None:
    with pytest.raises(ValueError, match="message"):
        Finding(code="duplicate-key", message="", verdict=Verdict.FAIL)


@pytest.mark.parametrize(
    "code", ["Duplicate-Key", "duplicate_key", "duplicate key", "-key", "key-", "a--b", "clé"]
)
def test_a_code_that_is_not_lowercase_words_joined_by_hyphens_is_rejected(code: str) -> None:
    with pytest.raises(ValueError, match=code):
        finding(code=code)


@pytest.mark.parametrize("code", ["tag", "duplicate-key", "text-on-several-lines", "not-yaml"])
def test_a_code_of_lowercase_words_joined_by_hyphens_is_accepted(code: str) -> None:
    assert finding(code=code).code == code


@pytest.mark.parametrize("line", [0, -1])
def test_a_line_smaller_than_one_is_rejected_naming_the_line(line: int) -> None:
    with pytest.raises(ValueError, match=str(line)):
        Finding(code="tag", message="a tag", verdict=Verdict.FAIL, lines=(4, line))


def test_the_summary_is_the_aggregation_of_the_verdicts() -> None:
    assert summarise([finding(Verdict.ASK), finding(Verdict.FAIL)]) is Verdict.FAIL
    assert summarise([finding(Verdict.ASK), finding(Verdict.ASK)]) is Verdict.ASK
    assert summarise([finding(Verdict.FAIL), finding(Verdict.ERROR)]) is Verdict.ERROR


def test_no_findings_summarise_to_pass() -> None:
    assert summarise([]) is Verdict.PASS
