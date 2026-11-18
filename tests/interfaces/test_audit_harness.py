# SDD-EARS: INTERFACES-145 INTERFACES-146
import json
import subprocess
from pathlib import Path

import pytest

from dokime.core.repository import CommitName, RefusalError
from dokime.interfaces import audit_command
from dokime.interfaces.cli import main
from tests.interfaces.audit_runs import audit

COMMIT = CommitName("e" * 40)


def test_the_commit_of_the_harness_reaches_the_evidence() -> None:
    done = audit(harness_commit=COMMIT)
    assert done.statement()["predicate"]["verifier"]["commit"] == "e" * 40
    assert "commit" not in audit().statement()["predicate"]["verifier"]


def project(root: Path) -> Path:
    root.mkdir()
    subprocess.run(["git", "-C", str(root), "init", "--quiet"], check=True)
    return root


def arguments(tmp_path: Path, *more: str) -> list[str]:
    patch = tmp_path / "change.patch"
    patch.write_text("diff\n")
    return [
        "audit",
        "--project",
        str(project(tmp_path / "project")),
        "--base",
        "a" * 40,
        "--patch",
        str(patch),
        "--story",
        "add-one",
        "--out",
        str(tmp_path / "out"),
        *more,
    ]


def stop_at_podman() -> None:
    raise RefusalError("stopped", "the test stops before podman")


def test_the_commit_is_asked_after_git_and_before_anything_is_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    asked: list[tuple[str, bool]] = []

    def commit(directory: Path, *, git: str = "git") -> CommitName:
        asked.append((git, (tmp_path / "out").exists()))
        return COMMIT

    monkeypatch.setattr(audit_command, "checkout_commit", commit)
    monkeypatch.setattr(audit_command, "PodmanRuntime", stop_at_podman)
    main(arguments(tmp_path))
    ((git, written),) = asked
    assert Path(git).is_absolute()
    assert written is False
    lines = capsys.readouterr().out.splitlines()
    assert f"harness {audit_command._version()} {'e' * 40}" in lines


def test_the_output_says_when_the_harness_has_no_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(audit_command, "checkout_commit", lambda directory, git="git": None)
    monkeypatch.setattr(audit_command, "PodmanRuntime", stop_at_podman)
    main([*arguments(tmp_path), "--format", "json"])
    document = json.loads(capsys.readouterr().out)
    assert document["harness"] == {"version": audit_command._version(), "commit": None}
    (tmp_path / "again").mkdir()
    main(arguments(tmp_path / "again"))
    lines = capsys.readouterr().out.splitlines()
    assert f"harness {audit_command._version()} without a commit" in lines
