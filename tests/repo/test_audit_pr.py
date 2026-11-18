# SDD-EARS: REPO-150 REPO-151 REPO-152 REPO-153 REPO-154
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.audit_pr import main, story_of

CONTRACT = "format: 1\nstory: add-one\n"


def git(project: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(project), "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def commit(project: Path, files: dict[str, str | None]) -> str:
    for name, text in files.items():
        path = project / name
        if text is None:
            path.unlink()
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    git(project, "add", "--all")
    git(project, "commit", "--quiet", "--message", "change")
    return git(project, "rev-parse", "HEAD")


@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    git(root, "init", "--quiet", "--initial-branch=main")
    commit(root, {"src/p.py": "x = 1\n"})
    return root


class Runs:
    """The runner of the tool, recording each command; it answers only dokime."""

    def __init__(self, code: int = 0, answer: dict[str, object] | None = None) -> None:
        self.calls: list[list[str]] = []
        self.files: dict[str, str] = {}
        self.code, self.answer = code, answer

    def __call__(self, command: list[str], capture: bool) -> subprocess.CompletedProcess[str]:
        assert command[:3] == [sys.executable, "-m", "dokime.interfaces"], command
        self.calls.append(command)
        for argument in command:
            if argument.endswith((".yaml", ".patch")) and Path(argument).is_file():
                self.files[argument] = Path(argument).read_text()
        stdout = json.dumps(self.answer) if capture and self.answer is not None else ""
        return subprocess.CompletedProcess(command, self.code, stdout, "")


def audit(project: Path, base: str, head: str, branch: str, tmp: Path, runs: Runs) -> int:
    summary = tmp / "summary.md"
    summary.touch()
    return main(
        [
            "--project",
            str(project),
            "--base",
            base,
            "--head",
            head,
            "--branch",
            branch,
            "--out",
            str(tmp / "out"),
            "--summary",
            str(summary),
        ],
        run=runs,
    )


@pytest.mark.parametrize(
    ("branch", "story"),
    [
        ("feat/interfaces-add-one", "add-one"),
        ("fix/repo-keep-the-canonical-form", "keep-the-canonical-form"),
        ("main", None),
        ("feat/interfaces", None),
        ("feat/repo-$(touch x)", None),
    ],
)
def test_the_story_is_the_description_of_the_branch(branch: str, story: str | None) -> None:
    assert story_of(branch) == story


def test_a_pull_request_of_a_contract_is_checked_and_not_audited(
    project: Path, tmp_path: Path
) -> None:
    base = git(project, "rev-parse", "HEAD")
    head = commit(project, {".dokime/changes/add-one/contract.yaml": CONTRACT})
    runs = Runs(code=3, answer={"verdict": "ASK", "findings": [{"code": "no-example"}]})
    code = audit(project, base, head, "docs/repo-add-one", tmp_path, runs)
    ((command),) = runs.calls
    assert command[3:5] == ["contract", "check"]
    assert runs.files[command[5]] == CONTRACT
    assert Path(command[5]).parent.name == "add-one"
    summary = (tmp_path / "summary.md").read_text()
    assert "contract pull request: checked, not audited" in summary
    assert "| add-one | ASK | `no-example` |" in summary
    assert code == 3


def test_a_branch_without_a_contract_in_the_base_is_not_audited(
    project: Path, tmp_path: Path
) -> None:
    base = git(project, "rev-parse", "HEAD")
    head = commit(project, {"src/p.py": "x = 2\n"})
    runs = Runs()
    assert audit(project, base, head, "feat/repo-add-one", tmp_path, runs) == 0
    assert runs.calls == []
    summary = (tmp_path / "summary.md").read_text()
    assert "not audited" in summary
    assert "`add-one`" in summary


def test_a_branch_that_gives_no_story_is_not_audited(project: Path, tmp_path: Path) -> None:
    base = git(project, "rev-parse", "HEAD")
    head = commit(project, {"src/p.py": "x = 2\n"})
    runs = Runs()
    assert audit(project, base, head, "main", tmp_path, runs) == 0
    assert runs.calls == []
    summary = (tmp_path / "summary.md").read_text()
    assert "not audited" in summary
    assert "main" not in summary


def test_a_change_with_a_contract_in_the_base_is_audited(project: Path, tmp_path: Path) -> None:
    base = commit(project, {".dokime/changes/add-one/contract.yaml": CONTRACT})
    head = commit(project, {"src/p.py": "x = 2\n"})
    runs = Runs(code=1)
    code = audit(project, base, head, "feat/repo-add-one", tmp_path, runs)
    ((command),) = runs.calls
    given = dict(zip(command[4::2], command[5::2], strict=False))
    assert command[3] == "audit"
    assert given["--project"] == str(project)
    assert (given["--base"], given["--story"]) == (base, "add-one")
    assert given["--out"] == str(tmp_path / "out")
    assert given["--summary"] == str(tmp_path / "summary.md")
    patch = runs.files[given["--patch"]]
    assert "-x = 1" in patch
    assert "+x = 2" in patch
    assert code == 1


def test_dokime_runs_with_the_python_of_the_tool_never_from_the_pull_request(
    project: Path, tmp_path: Path
) -> None:
    base = commit(project, {".dokime/changes/add-one/contract.yaml": CONTRACT})
    head = commit(project, {"src/p.py": "x = 2\n"})
    runs = Runs()
    audit(project, base, head, "feat/repo-add-one", tmp_path, runs)
    ((command),) = runs.calls
    assert command[0] == sys.executable
    assert not Path(command[0]).is_relative_to(project)


def test_a_base_or_a_head_that_is_not_a_commit_is_an_error(project: Path, tmp_path: Path) -> None:
    runs = Runs()
    assert audit(project, "HEAD", "HEAD", "feat/repo-add-one", tmp_path, runs) == 2
    assert runs.calls == []
    assert "not audited" in (tmp_path / "summary.md").read_text()


def test_a_pull_request_that_changes_no_contract_under_changes_checks_none(
    project: Path, tmp_path: Path
) -> None:
    base = commit(
        project,
        {
            ".dokime/changes/add-one/contract.yaml": CONTRACT,
            ".dokime/changes/add-one/notes.md": "a",
        },
    )
    head = commit(
        project,
        {".dokime/changes/add-one/contract.yaml": None, ".dokime/changes/add-one/notes.md": "b"},
    )
    runs = Runs()
    assert audit(project, base, head, "docs/repo-add-one", tmp_path, runs) == 0
    assert runs.calls == []
    assert "It adds or changes no contract." in (tmp_path / "summary.md").read_text()


@pytest.mark.parametrize("answer", [None, {"verdict": "MAYBE", "findings": []}])
def test_an_answer_of_contract_check_that_does_not_read_is_an_error(
    project: Path, tmp_path: Path, answer: dict[str, object] | None
) -> None:
    base = git(project, "rev-parse", "HEAD")
    head = commit(project, {".dokime/changes/a b/contract.yaml": CONTRACT})
    runs = Runs(code=0, answer=answer)
    assert audit(project, base, head, "docs/repo-add-one", tmp_path, runs) == 2
    summary = (tmp_path / "summary.md").read_text()
    assert "| a directory that is not a name | ERROR | — |" in summary
    assert "a b" not in summary


def test_the_contract_is_checked_by_the_real_command(project: Path, tmp_path: Path) -> None:
    base = git(project, "rev-parse", "HEAD")
    head = commit(project, {".dokime/changes/add-one/contract.yaml": CONTRACT})
    summary = tmp_path / "summary.md"
    summary.touch()
    code = main(
        [
            "--project",
            str(project),
            "--base",
            base,
            "--head",
            head,
            "--branch",
            "docs/repo-add-one",
            "--out",
            str(tmp_path / "out"),
            "--summary",
            str(summary),
        ]
    )
    written = summary.read_text()
    assert "| add-one | FAIL |" in written
    assert code == 1
