# SDD-EARS: INTERFACES-150 INTERFACES-151 INTERFACES-152 INTERFACES-153
import json
import subprocess
from pathlib import Path

import pytest

from dokime.core.repository import CommitName
from dokime.interfaces.audit_command import Harness, summary_of
from dokime.interfaces.cli import main
from tests.interfaces.audit_runs import STORY, TEST, audit, base_files, change
from tests.verify.doubles import patch

HARNESS = Harness("1.2.3", CommitName("e" * 40), asked=True)


def test_the_summary_has_the_verdict_the_inputs_and_every_gate() -> None:
    done = audit()
    summary = summary_of(done.audited, HARNESS, STORY)
    predicate = done.statement()["predicate"]
    assert done.audited.evidence is not None
    assert "PASS" in summary.splitlines()[0]
    for part in (
        STORY,
        predicate["contract"]["digest"],
        "1.2.3",
        "e" * 40,
        done.audited.evidence.digest,
    ):
        assert part in summary
    rows = [line for line in summary.splitlines() if line.startswith("| ") and "---" not in line]
    assert rows[0].startswith("| Gate ")
    assert [row.split("|")[1].strip() for row in rows[1:]] == [
        gate["gate"] for gate in predicate["gates"]
    ]
    assert "| visible-examples | run | PASS |" in summary
    assert "| relations | not-applicable |" in summary


def test_the_summary_names_codes_and_quotes_nothing_dokime_did_not_write() -> None:
    varies = json.dumps([{TEST: "passed"}, {TEST: "failed"}]).encode()
    done = audit(
        base_files(**{"outcomes.json": varies}),
        change(**{"answers.json": json.dumps({"E-0001": "**seven**"})}),
    )
    summary = summary_of(done.audited, HARNESS, STORY)
    assert "example-fails" in summary
    assert "**seven**" not in summary
    assert "seven" not in summary
    assert TEST not in summary
    for gate in done.statement()["predicate"]["gates"]:
        for reason in [gate.get("reason", "")]:
            assert not reason or reason not in summary


def test_an_audit_without_evidence_gives_its_verdict_and_codes() -> None:
    done = audit(changed=patch(removes=["absent.py"]))
    summary = summary_of(done.audited, HARNESS, STORY)
    assert "ERROR" in summary.splitlines()[0]
    assert "patch-does-not-apply" in summary
    assert "| Gate " not in summary
    assert "absent.py" not in summary


def test_a_story_that_is_not_a_name_is_left_out() -> None:
    done = audit(story="**not** a name")
    summary = summary_of(done.audited, Harness("1.2.3", None, asked=False), "**not** a name")
    assert "not a name" not in summary
    assert "not-a-story" in summary
    assert "commit not asked" in summary


def arguments(tmp_path: Path, summary: Path) -> list[str]:
    project = tmp_path / "project"
    project.mkdir()
    subprocess.run(["git", "-C", str(project), "init", "--quiet"], check=True)
    given = tmp_path / "change.patch"
    given.write_text("diff\n")
    return [
        "audit",
        "--project",
        str(project),
        "--base",
        "HEAD~1",
        "--patch",
        str(given),
        "--story",
        "add-one",
        "--out",
        str(tmp_path / "out"),
        "--summary",
        str(summary),
    ]


def test_the_summary_is_appended_to_its_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    summary = tmp_path / "summary.md"
    summary.write_text("before\n")
    assert main(arguments(tmp_path, summary)) == 2
    written = summary.read_text()
    assert written.startswith("before\n")
    assert "not-a-commit-name" in written
    capsys.readouterr()


def test_a_summary_that_cannot_be_written_ends_with_an_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    directory = tmp_path / "a-directory"
    directory.mkdir()
    assert main(arguments(tmp_path, directory)) == 2
    assert "summary" in capsys.readouterr().err


def test_with_a_contract_from_outside_the_story_is_the_name_of_its_directory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    summary = tmp_path / "summary.md"
    given = arguments(tmp_path, summary)
    contract = tmp_path / "add-one" / "contract.yaml"
    contract.parent.mkdir()
    contract.write_text("format: 1\n")
    story = given.index("--story")
    given[story : story + 2] = ["--contract", str(contract)]
    main(given)
    assert "- Story: `add-one`" in summary.read_text()
    capsys.readouterr()
