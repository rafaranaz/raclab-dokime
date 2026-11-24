# SDD-EARS: REPO-164 REPO-165 REPO-166 REPO-167 REPO-168 REPO-175 REPO-176 REPO-177
import json
from pathlib import Path

from tools import check_corpus_parts
from tools.check_corpus_parts import check_parts, check_results, collected

SUCCESS = dict.fromkeys("abcdef", "success")
RAN = dict.fromkeys("abcdef", True)
COMMIT = "a" * 40


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


AUDIT = "test_a_case_gets_its_expected_verdict_at_its_gate"


def audits(*keys: str) -> bytes:
    cases = "".join(
        f'<testcase classname="tests.corpus.test_corpus_audit" name="{AUDIT}[{k}]" time="1"/>'
        for k in keys
    )
    other = '<testcase classname="tests.corpus.test_corpus_cases" name="test_x" time="0"/>'
    return f"<testsuites><testsuite>{cases}{other}</testsuite></testsuites>".encode()


def lines(commit: str, *keys: str) -> str:
    return "".join(
        json.dumps({"commit": commit, "key": k, "verdict": "PASS", "failing_gate": None}) + "\n"
        for k in keys
    )


def test_parts_whose_results_hold_one_line_for_each_audit_pass() -> None:
    reports = {"a": audits("p/one", "p/two"), "b": audits(), "c": audits("q/three")}
    results = {"a": lines(COMMIT, "p/one", "p/two"), "b": "", "c": lines(COMMIT, "q/three")}
    passed, found = check_results(reports, results)
    assert passed, found


def test_an_audit_without_its_line_fails_naming_the_part_and_the_case() -> None:
    reports = {"a": audits("p/one", "p/two")}
    for written in (lines(COMMIT, "p/one"), lines(COMMIT, "p/one", "p/two", "p/two"), None):
        passed, found = check_results(reports, {"a": written})
        assert not passed
        assert any("part a" in line and "p/two" in line for line in found), found


def test_a_line_of_a_case_that_was_not_audited_fails() -> None:
    passed, found = check_results({"a": audits("p/one")}, {"a": lines(COMMIT, "p/one", "p/x")})
    assert not passed
    assert any("part a" in line and "p/x" in line for line in found), found


def test_lines_of_two_commits_fail_giving_both() -> None:
    other = "b" * 40
    reports = {"a": audits("p/one"), "b": audits("p/two")}
    passed, found = check_results(
        reports, {"a": lines(COMMIT, "p/one"), "b": lines(other, "p/two")}
    )
    assert not passed
    assert any(COMMIT in line and other in line for line in found), found


def test_the_command_gathers_the_results_of_the_parts_in_their_order(tmp_path: Path) -> None:
    keys = {"a": ["p/a1", "p/a2"], "b": ["p/b1"], "c": [], "d": ["p/d1"], "e": [], "f": ["p/f1"]}
    for part, found in keys.items():
        (tmp_path / part).mkdir()
        (tmp_path / part / "ran").write_text("true\n")
        (tmp_path / part / "corpus.xml").write_bytes(audits(*found))
        (tmp_path / part / "results.jsonl").write_text(lines(COMMIT, *found))
    total = sum(len(found) + 1 for found in keys.values())
    (tmp_path / "collection.txt").write_text(f"{total} tests collected in 0.2s\n")
    gathered = tmp_path / "results.jsonl"
    arguments = ["--parts", str(tmp_path), "--collection", str(tmp_path / "collection.txt")]
    arguments += [f"--result={p}=success" for p in keys]
    assert check_corpus_parts.main([*arguments, "--results", str(gathered)]) == 0
    written = [json.loads(line)["key"] for line in gathered.read_text().splitlines()]
    assert written == [k for part in "abcdef" for k in keys[part]]


def test_the_results_are_gathered_when_a_part_failed_and_the_check_still_fails(
    tmp_path: Path,
) -> None:
    keys = {"a": ["p/a1"], "b": ["p/b1"], "c": [], "d": [], "e": [], "f": ["p/f1"]}
    for part, found in keys.items():
        (tmp_path / part).mkdir()
        (tmp_path / part / "ran").write_text("true\n")
        (tmp_path / part / "corpus.xml").write_bytes(audits(*found))
        (tmp_path / part / "results.jsonl").write_text(lines(COMMIT, *found))
    total = sum(len(found) + 1 for found in keys.values())
    (tmp_path / "collection.txt").write_text(f"{total} tests collected in 0.2s\n")
    gathered = tmp_path / "results.jsonl"
    arguments = ["--parts", str(tmp_path), "--collection", str(tmp_path / "collection.txt")]
    arguments += [f"--result={p}=success" for p in "abcde"] + ["--result=f=failure"]
    assert check_corpus_parts.main([*arguments, "--results", str(gathered)]) == 1
    written = [json.loads(line)["key"] for line in gathered.read_text().splitlines()]
    assert written == ["p/a1", "p/b1", "p/f1"]
