# SDD-EARS: CORPUS-098
import json
from pathlib import Path

from tests.corpus.results import append, result_line


def test_a_line_gives_the_commit_the_case_and_what_its_audit_gave() -> None:
    line = result_line("a" * 40, "python-semver/a-case", "FAIL", "visible-examples", True)
    assert "\n" not in line
    assert json.loads(line) == {
        "commit": "a" * 40,
        "key": "python-semver/a-case",
        "verdict": "FAIL",
        "failing_gate": "visible-examples",
        "key_given": True,
    }


def test_a_case_without_a_failing_gate_gives_null() -> None:
    line = result_line("b" * 40, "mdformat/a-case", "PASS", None, False)
    assert json.loads(line)["failing_gate"] is None


def test_each_line_is_appended_to_the_file(tmp_path: Path) -> None:
    results = tmp_path / "results.jsonl"
    append(results, result_line("c" * 40, "p/one", "PASS", None, False))
    append(results, result_line("c" * 40, "p/two", "FAIL", "relations", False))
    keys = [json.loads(line)["key"] for line in results.read_text().splitlines()]
    assert keys == ["p/one", "p/two"]
