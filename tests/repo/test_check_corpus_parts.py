# SDD-EARS: REPO-164 REPO-165 REPO-166 REPO-167 REPO-168
from pathlib import Path

from tools import check_corpus_parts
from tools.check_corpus_parts import check_parts, collected

SUCCESS = dict.fromkeys("abcdef", "success")
RAN = dict.fromkeys("abcdef", True)


def report(tests: int) -> bytes:
    cases = "".join(f'<testcase classname="c" name="t{n}" time="1"/>' for n in range(tests))
    return f'<?xml version="1.0"?><testsuites><testsuite>{cases}</testsuite></testsuites>'.encode()


REPORTS: dict[str, bytes | None] = {
    "a": report(2),
    "b": report(1),
    "c": report(1),
    "d": report(4),
    "e": report(1),
    "f": report(1),
}


def test_parts_that_ended_well_and_hold_the_collection_pass() -> None:
    passed, lines = check_parts(SUCCESS, RAN, REPORTS, 10)
    assert passed
    assert lines


def test_a_part_that_did_not_end_in_success_fails() -> None:
    for ending in ("failure", "skipped", "cancelled"):
        passed, lines = check_parts({**SUCCESS, "c": ending}, RAN, REPORTS, 10)
        assert not passed
        assert any("c" in line and ending in line for line in lines)


def test_a_part_that_ran_without_a_readable_report_fails() -> None:
    for left in (None, b"<not xml", b"<!DOCTYPE x><testsuites/>"):
        passed, lines = check_parts(SUCCESS, RAN, {**REPORTS, "b": left}, 10)
        assert not passed
        assert any("b" in line and "report" in line for line in lines)


def test_parts_that_do_not_hold_the_collection_fail_with_both_numbers() -> None:
    for collection in (9, 11):
        passed, lines = check_parts(SUCCESS, RAN, REPORTS, collection)
        assert not passed
        assert any("10" in line and str(collection) in line for line in lines)


def test_parts_that_ran_and_parts_that_did_not_fail() -> None:
    passed, lines = check_parts(SUCCESS, {**RAN, "a": False, "d": False}, REPORTS, 10)
    assert not passed
    assert any("a" in line and "d" in line for line in lines)


def test_no_part_that_ran_the_corpus_passes_and_says_so() -> None:
    none: dict[str, bytes | None] = dict.fromkeys("abcdef", None)
    passed, lines = check_parts(SUCCESS, dict.fromkeys("abcdef", False), none, 246)
    assert passed
    assert any("did not run" in line for line in lines)


def test_the_collection_is_read_from_the_quiet_output_of_pytest() -> None:
    assert collected("tests/corpus/x.py::y\n\n246 tests collected in 0.25s\n") == 246
    assert collected("1 test collected in 0.01s") == 1


def test_the_command_reads_what_each_part_left(tmp_path: Path) -> None:
    for part, tests in (("a", 2), ("b", 1), ("c", 1), ("d", 4), ("e", 1), ("f", 1)):
        (tmp_path / part).mkdir()
        (tmp_path / part / "ran").write_text("true\n")
        (tmp_path / part / "corpus.xml").write_bytes(report(tests))
    (tmp_path / "collection.txt").write_text("10 tests collected in 0.2s\n")
    arguments = ["--parts", str(tmp_path), "--collection", str(tmp_path / "collection.txt")]
    results = [f"--result={p}=success" for p in "abcdef"]
    assert check_corpus_parts.main([*arguments, *results]) == 0
    assert check_corpus_parts.main([*arguments, *results[:5], "--result=f=failure"]) == 1
