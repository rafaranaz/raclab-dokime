# SDD-EARS: REPO-130 REPO-131 REPO-132 REPO-133 REPO-134
from pathlib import Path

import pytest

from tools import check_corpus

PROJECTS = ["cachetools", "mdformat", "python-semver"]
CLASS = "tests.corpus.test_corpus_self_check"
NAME = "test_the_pack_of_a_project_passes_its_self_check_at_its_commit"


def case(project: str, inner: str = "", seconds: float = 12.5) -> str:
    attributes = f'classname="{CLASS}" name="{NAME}[{project}]" time="{seconds}"'
    return f"<testcase {attributes}>{inner}</testcase>"


def report(*cases: str) -> bytes:
    body = "".join(cases)
    return f'<?xml version="1.0"?><testsuites><testsuite>{body}</testsuite></testsuites>'.encode()


def all_passed() -> bytes:
    return report(*(case(p, seconds=10 * (i + 1)) for i, p in enumerate(PROJECTS)))


def test_every_project_passed_once_passes() -> None:
    passed, lines = check_corpus.check_report(all_passed(), PROJECTS)
    assert passed
    assert len(lines) == 3


@pytest.mark.parametrize(
    ("cases", "words"),
    [
        ((case("cachetools"), case("mdformat")), "python-semver: missing"),
        (
            (case("cachetools"), case("mdformat"), case("python-semver", "<skipped/>")),
            "python-semver: skipped",
        ),
        (
            (case("cachetools"), case("mdformat"), case("python-semver", '<failure message="x"/>')),
            "python-semver: failed",
        ),
        (
            (case("cachetools"), case("mdformat"), case("python-semver", '<error message="x"/>')),
            "python-semver: error",
        ),
        (
            (case("cachetools"), case("mdformat"), case("python-semver"), case("python-semver")),
            "python-semver: ran 2 times",
        ),
    ],
)
def test_a_project_missing_skipped_failed_or_repeated_fails_the_check(
    cases: tuple[str, ...], words: str
) -> None:
    passed, lines = check_corpus.check_report(report(*cases), PROJECTS)
    assert not passed
    assert any(words in line for line in lines), lines


def test_all_three_skipped_fails_the_check() -> None:
    skipped = report(*(case(p, "<skipped/>") for p in PROJECTS))
    passed, lines = check_corpus.check_report(skipped, PROJECTS)
    assert not passed
    assert sum("skipped" in line for line in lines) == 3


def test_a_failure_of_the_network_is_named_as_such() -> None:
    failing = case("mdformat", '<failure message="Failed: network: cloning https://x failed"/>')
    passed, lines = check_corpus.check_report(
        report(case("cachetools"), failing, case("python-semver")), PROJECTS
    )
    assert not passed
    assert any("mdformat: failed: the cause was the network" in line for line in lines), lines


def test_the_duration_of_each_self_check_is_written() -> None:
    _, lines = check_corpus.check_report(all_passed(), PROJECTS)
    assert lines == [
        "cachetools: passed in 10 s",
        "mdformat: passed in 20 s",
        "python-semver: passed in 30 s",
    ]


def test_the_projects_are_those_of_tests_corpus_and_a_bad_report_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    good = tmp_path / "good.xml"
    good.write_bytes(all_passed())
    assert check_corpus.main(["--report", str(good)]) == 0
    assert "python-semver: passed" in capsys.readouterr().out
    for text in (b"not xml", b"<!DOCTYPE x><testsuites/>"):
        bad = tmp_path / "bad.xml"
        bad.write_bytes(text)
        assert check_corpus.main(["--report", str(bad)]) == 1
        assert str(bad) in capsys.readouterr().out
    assert check_corpus.main(["--report", str(tmp_path / "absent.xml")]) == 1
