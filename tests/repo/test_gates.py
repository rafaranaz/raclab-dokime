# SDD-EARS: REPO-120 REPO-121 REPO-122 REPO-123
import stat
import subprocess
from pathlib import Path

import pytest

from tools import gates
from tools._common import DEFAULT_ROOT

FAKE = """#!/bin/sh
echo "$(basename "$0") $*" >> "$GATES_LOG"
case "$(basename "$0") $*" in
  *"$GATES_FAIL"*) [ -n "$GATES_FAIL" ] && exit 7 ;;
esac
exit 0
"""


@pytest.fixture
def fake_tools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """`uv` and `npm` that write each call to a log and fail on the call named in GATES_FAIL."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name in ("uv", "npm"):
        program = bin_dir / name
        program.write_text(FAKE)
        program.chmod(program.stat().st_mode | stat.S_IXUSR)
    log = tmp_path / "calls.log"
    monkeypatch.setenv("GATES_LOG", str(log))
    monkeypatch.setenv("GATES_FAIL", "")
    monkeypatch.setenv("PATH", f"{bin_dir}:/usr/bin:/bin")
    return log


@pytest.fixture
def project(repo: Path) -> Path:
    (repo / "CLAUDE.md").write_text((DEFAULT_ROOT / "CLAUDE.md").read_text())
    return repo


def calls(log: Path) -> list[str]:
    return log.read_text().splitlines() if log.exists() else []


def expected_calls(branch: str) -> list[str]:
    block = gates.gate_block((DEFAULT_ROOT / "CLAUDE.md").read_text())
    assert block is not None
    wanted = []
    for line in block.replace("<branch>", branch).splitlines():
        for command in line.split("&&"):
            command = command.split("|")[0].strip()
            if command:
                wanted.append(command)
    return wanted


def test_every_command_of_the_block_runs_in_order_with_the_current_branch(
    project: Path, fake_tools: Path
) -> None:
    assert gates.main([], root=project) == 0
    assert calls(fake_tools) == expected_calls("main")
    assert any("--branch main" in call for call in calls(fake_tools))


@pytest.mark.parametrize("failing", ["uv run ruff check .", "uv run mypy", "uv run lint-imports"])
def test_a_failing_command_stops_the_runner_with_its_exit_code(
    project: Path, fake_tools: Path, monkeypatch: pytest.MonkeyPatch, failing: str
) -> None:
    monkeypatch.setenv("GATES_FAIL", failing)
    assert gates.main([], root=project) == 7
    made = calls(fake_tools)
    assert made[-1] == failing
    assert len(made) < len(expected_calls("main"))


def test_a_command_that_fails_inside_a_pipeline_stops_the_runner(
    project: Path, fake_tools: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    claude = project / "CLAUDE.md"
    claude.write_text("## Gates locally\n\n```bash\nuv run first | tail -1\nuv run second\n```\n")
    monkeypatch.setenv("GATES_FAIL", "uv run first")
    assert gates.main([], root=project) == 7
    assert calls(fake_tools) == ["uv run first"]


def test_a_claude_md_without_the_block_is_refused_naming_it(
    project: Path, fake_tools: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (project / "CLAUDE.md").write_text("# Instructions\n\nNo gates here.\n")
    assert gates.main([], root=project) != 0
    assert "Gates locally" in capsys.readouterr().err
    assert calls(fake_tools) == []


def test_a_branch_whose_name_has_shell_syntax_is_passed_as_one_argument(
    project: Path, fake_tools: Path
) -> None:
    branch = "feat/repo-x;touch${IFS}injected;$(touch${IFS}substituted)"
    subprocess.run(["git", "-C", str(project), "checkout", "-q", "-b", branch], check=True)
    (project / "CLAUDE.md").write_text(
        "## Gates locally\n\n```bash\nuv run check --branch <branch>\n```\n"
    )
    assert gates.main([], root=project) == 0
    assert calls(fake_tools) == [f"uv run check --branch {branch}"]
    assert not (project / "injected").exists()
    assert not (project / "substituted").exists()
