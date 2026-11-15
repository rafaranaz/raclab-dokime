# SDD-EARS: SANDBOX-001 SANDBOX-002 SANDBOX-003 SANDBOX-004 SANDBOX-005
import stat
import subprocess
from pathlib import Path

import pytest

from dokime.core.runtime import Digest, RunLimits
from dokime.sandbox.podman import PodmanRuntime
from tests.sandbox.engines import refusal, require


def fake_podman(directory: Path, version_line: str) -> Path:
    """A program that answers `--version` with a given line and fails on anything else."""
    directory.mkdir(parents=True, exist_ok=True)
    program = directory / "podman"
    program.write_text(
        f'#!/bin/sh\nif [ "$1" = "--version" ]; then echo "{version_line}"; exit 0; fi\nexit 1\n'
    )
    program.chmod(program.stat().st_mode | stat.S_IXUSR)
    return program


def test_a_podman_that_is_not_found_is_refused(tmp_path: Path) -> None:
    finding = refusal(lambda: PodmanRuntime(podman=str(tmp_path / "no-such-podman")))
    assert finding.code == "podman-not-found"


def test_a_podman_that_is_not_executable_is_refused(tmp_path: Path) -> None:
    program = tmp_path / "podman"
    program.write_text("#!/bin/sh\n")
    finding = refusal(lambda: PodmanRuntime(podman=str(program)))
    assert finding.code == "podman-not-found"


@pytest.mark.parametrize("line", ["podman version 4.8.9", "podman version 3.4.4", "nonsense"])
def test_a_podman_older_than_4_9_or_unreadable_is_refused_quoting_the_version(
    tmp_path: Path, line: str
) -> None:
    program = fake_podman(tmp_path / "bin", line)
    finding = refusal(lambda: PodmanRuntime(podman=str(program)))
    assert (finding.code, line in finding.message) == ("podman-too-old", True)


@pytest.mark.parametrize("line", ["podman version 4.9.0", "podman version 5.4.2"])
def test_a_podman_of_4_9_or_later_is_accepted(tmp_path: Path, line: str) -> None:
    runtime = PodmanRuntime(podman=str(fake_podman(tmp_path / "bin", line)))
    assert runtime.podman_version == line.removeprefix("podman version ")


def test_podman_is_resolved_once_to_an_absolute_path_that_every_command_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    program = fake_podman(tmp_path / "bin", "podman version 5.0.0")
    monkeypatch.setenv("PATH", str(program.parent))
    runtime = PodmanRuntime()
    monkeypatch.setenv("PATH", "")
    assert runtime.podman_path == program.resolve()
    assert runtime.podman_path.is_absolute()
    project, out = tmp_path / "project", tmp_path / "out"
    project.mkdir()
    out.mkdir()
    finding = refusal(
        lambda: runtime.run(Digest(f"sha256:{'a' * 64}"), ("true",), project, out, RunLimits())
    )
    assert finding.code == "podman-failed"


def test_the_adapter_gives_the_path_and_the_version_of_the_podman_it_runs() -> None:
    found = Path(require("podman")).resolve()
    runtime = PodmanRuntime()
    assert runtime.podman_path == found
    line = subprocess.run([found, "--version"], capture_output=True, text=True, check=True).stdout
    assert line.strip() == f"podman version {runtime.podman_version}"


def test_an_error_of_podman_that_nothing_else_names_is_refused_with_what_podman_wrote(
    tmp_path: Path,
) -> None:
    require("podman")
    project, out = tmp_path / "project", tmp_path / "out"
    project.mkdir()
    out.mkdir()
    missing = Digest(f"sha256:{'0' * 64}")
    finding = refusal(lambda: PodmanRuntime().run(missing, ("true",), project, out, RunLimits()))
    assert finding.code == "podman-failed"
    assert "image not known" in finding.message
