"""The adapter of the verification runtime that builds and runs with the `podman` command.

`podman build` and `podman run` share the local store of images, so the image a build gives is
the one a run starts. A run has no network, limits of memory with swap, processor and processes, a
read-only root with a `/tmp` of its own, the project mounted read-only and the output directory
writable (ADR-0043), and no capabilities and no way to gain privileges. Each run has a container
named for it alone, which is removed however the run ends, an interruption of the harness included.
"""

import contextlib
import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import threading
import uuid
from collections.abc import Iterator
from pathlib import Path, PurePosixPath
from types import FrameType

from dokime.core.outcomes import Report, ReportLimits
from dokime.core.repository import RefusalError
from dokime.core.runtime import (
    BaseImage,
    Build,
    BuildLimits,
    Digest,
    Ending,
    RunLimits,
    RunResult,
)
from dokime.sandbox.report import expat_version, read_report

MINIMUM_VERSION = (4, 9)
"""The podman of ubuntu-24.04, where CI runs: reasoning, not a measurement of older versions."""

PROJECT = "/dokime/project"
OUTPUT = "/dokime/out"

_VERSION = re.compile(r"podman version (\d+)\.(\d+)\.\S+")
_BASE_DIGEST = "org.opencontainers.image.base.digest"
_LAST_LINES = 20
_STOP_SECONDS = 10
_OOM_EXIT = 137
_NOT_STARTED = (126, 127)
"""What podman returns when the command cannot be invoked or is not found."""
_ROOT = ("", "0", "root")
_ENDED = ("exited", "stopped")
"""The states of a container whose command has ended: cleaned up or not yet."""
_CONMON_OOM = "oom"
"""The file that conmon leaves in its working directory when the memory limit kills the container.

conmon writes it with a relative path and never changes directory, and podman 4.9 looks for it
elsewhere, so it never reports `OOMKilled`; podman 5 reads its own copy. This is read in the
sources of conmon 2.1.10 and podman 4.9.3, and is not documented.
"""


class _TerminatedError(BaseException):
    """SIGTERM reached the harness while a run was going on."""


def _raise_terminated(_signal: int, _frame: FrameType | None) -> None:
    raise _TerminatedError


@contextlib.contextmanager
def _sigterm_raises() -> Iterator[None]:
    """Turn SIGTERM into an exception, so that the container is removed before the harness ends.

    Only the main thread receives signals; elsewhere nothing changes.
    """
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    previous = signal.signal(signal.SIGTERM, _raise_terminated)
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, previous)


def _last_lines(path: Path) -> str:
    lines = path.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    return "\n".join(lines[-_LAST_LINES:])


def _stop(process: "subprocess.Popen[bytes]") -> None:
    """End a process and the processes it started: politely, then by force."""
    for sent in (signal.SIGTERM, signal.SIGKILL):
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, sent)
        try:
            process.wait(timeout=_STOP_SECONDS)
        except subprocess.TimeoutExpired:
            continue
        return


class PodmanRuntime:
    """Builds with `podman build` and runs with `podman run`, which share the store of images."""

    def __init__(self, *, podman: str = "podman") -> None:
        found = shutil.which(podman)
        if found is None:
            raise RefusalError(
                "podman-not-found", f"no executable program {podman!r} was found to run podman"
            )
        self.podman_path = Path(found).resolve()
        self.podman_version = self._check_version()
        self.expat_version = expat_version()

    def _check_version(self) -> str:
        try:
            done = subprocess.run(
                [self.podman_path, "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )
            line = done.stdout.strip()
        except (OSError, subprocess.TimeoutExpired) as error:
            line = str(error)
        found = _VERSION.fullmatch(line)
        if found is None or (int(found[1]), int(found[2])) < MINIMUM_VERSION:
            raise RefusalError(
                "podman-too-old",
                f"the podman adapter needs podman 4.9 or later, and podman gave {line!r}",
            )
        return line.removeprefix("podman version ")

    def _podman(self, *args: str) -> str:
        done = subprocess.run(
            [self.podman_path, *args], capture_output=True, text=True, check=False
        )
        if done.returncode != 0:
            raise RefusalError(
                "podman-failed", f"podman {args[0]} failed: {done.stderr.strip() or 'no output'}"
            )
        return done.stdout.strip()

    def build(self, dockerfile: Path, directory: Path, limits: BuildLimits) -> Build:
        """Build an image from a Dockerfile and the directory it builds from."""
        with tempfile.TemporaryDirectory(prefix="dokime-build-") as work:
            image_file, log = Path(work) / "image", Path(work) / "log"
            with log.open("wb") as written:
                process = subprocess.Popen(
                    [
                        self.podman_path,
                        "build",
                        "--force-rm",
                        "--iidfile",
                        image_file,
                        "--file",
                        dockerfile.resolve(),
                        directory.resolve(),
                    ],
                    stdin=subprocess.DEVNULL,
                    stdout=written,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    cwd=work,
                )
                try:
                    code = process.wait(timeout=limits.time_seconds)
                except subprocess.TimeoutExpired:
                    _stop(process)
                    raise RefusalError(
                        "build-timed-out",
                        f"the build did not end within its limit of {limits.time_seconds} seconds",
                    ) from None
                except BaseException:
                    _stop(process)
                    raise
            if code != 0:
                raise RefusalError(
                    "build-failed", f"the build ended with {code}:\n{_last_lines(log)}"
                )
            image = Digest(image_file.read_text().strip())
        return Build(image=image, base=self._base(image))

    def _base(self, image: Digest) -> BaseImage | None:
        listed = self._podman("image", "inspect", "--format", "{{json .Annotations}}", image.text)
        annotations = json.loads(listed) or {}
        digest = annotations.get(_BASE_DIGEST)
        return BaseImage(platform=Digest(digest)) if digest else None

    def run(
        self,
        image: Digest,
        command: tuple[str, ...],
        project: Path,
        output: Path,
        limits: RunLimits,
    ) -> RunResult:
        """Run a command in an image, with the project and the output directory mounted."""
        for role, directory in (("project", project), ("output", output)):
            if not directory.is_dir():
                raise ValueError(f"the {role} directory {directory} is not an existing directory")
        self._check_user(image)
        name = f"dokime-{uuid.uuid4().hex}"
        try:
            with _sigterm_raises(), tempfile.TemporaryDirectory(prefix="dokime-run-") as work:
                return self._run(name, image, command, project, output, limits, Path(work))
        except _TerminatedError:
            self._remove(name)
            signal.raise_signal(signal.SIGTERM)
            raise
        finally:
            self._remove(name)

    def _check_user(self, image: Digest) -> None:
        """Refuse an image that runs as a user other than root.

        In a rootless engine, root in the container is the person who runs the harness; another
        user is a subordinate one, which cannot write in the output.
        """
        user = self._podman("image", "inspect", "--format", "{{.Config.User}}", image.text)
        name, _, group = user.partition(":")
        if name in _ROOT and (not group or group in _ROOT):
            return
        raise RefusalError(
            "user-not-root",
            f"the image runs as the user {user!r}, not as root, so it could not write its"
            " report in the output; the user can come from the base image, and the person can"
            " set USER root in the Dockerfile of the pack",
        )

    def _run(
        self,
        name: str,
        image: Digest,
        command: tuple[str, ...],
        project: Path,
        output: Path,
        limits: RunLimits,
        work: Path,
    ) -> RunResult:
        errors = work / "errors"
        with errors.open("wb") as written:
            process = subprocess.Popen(
                [
                    self.podman_path,
                    "run",
                    "--name",
                    name,
                    "--pull",
                    "never",
                    "--network",
                    "none",
                    "--cap-drop",
                    "ALL",
                    "--security-opt",
                    "no-new-privileges",
                    "--read-only",
                    "--read-only-tmpfs=false",
                    "--mount",
                    "type=tmpfs,destination=/tmp,tmpfs-mode=1777",
                    "--memory",
                    str(limits.memory_bytes),
                    "--memory-swap",
                    str(limits.memory_bytes),
                    "--cpus",
                    str(limits.processors),
                    "--pids-limit",
                    str(limits.processes),
                    "--volume",
                    f"{project.resolve()}:{PROJECT}:ro",
                    "--volume",
                    f"{output.resolve()}:{OUTPUT}:rw",
                    "--workdir",
                    PROJECT,
                    image.text,
                    *command,
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=written,
                start_new_session=True,
                cwd=work,
            )
            try:
                process.wait(timeout=limits.time_seconds)
            except subprocess.TimeoutExpired:
                self._kill(name, process)
                return RunResult(ending=Ending.TIME_LIMIT, exit_code=None)
            except BaseException:
                self._kill(name, process)
                raise
        return self._ending(name, process.returncode, work)

    def _ending(self, name: str, returned: int, work: Path) -> RunResult:
        errors = work / "errors"
        done = subprocess.run(
            [
                self.podman_path,
                "container",
                "inspect",
                "--format",
                "{{.State.Status}} {{.State.ExitCode}} {{.State.OOMKilled}}",
                name,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        state = done.stdout.split()
        if returned in _NOT_STARTED and state[:1] == ["created"]:
            return RunResult(ending=Ending.EXITED, exit_code=returned)
        if done.returncode != 0 or len(state) != 3 or state[0] not in _ENDED:
            seen = " ".join(state) or done.stderr.strip() or "no state"
            raise RefusalError(
                "podman-failed",
                f"podman run failed (container: {seen}): {_last_lines(errors) or 'no output'}",
            )
        code = int(state[1])
        killed_by_memory = state[2] == "true" or (work / _CONMON_OOM).exists()
        if code == _OOM_EXIT and killed_by_memory:
            return RunResult(ending=Ending.MEMORY_LIMIT, exit_code=None)
        return RunResult(ending=Ending.EXITED, exit_code=code)

    def _kill(self, name: str, process: "subprocess.Popen[bytes]") -> None:
        subprocess.run(
            [self.podman_path, "kill", "--signal", "KILL", name],
            capture_output=True,
            check=False,
        )
        try:
            process.wait(timeout=_STOP_SECONDS)
        except subprocess.TimeoutExpired:
            _stop(process)

    def _remove(self, name: str) -> None:
        subprocess.run(
            [self.podman_path, "rm", "--force", "--ignore", "--time", "0", name],
            capture_output=True,
            check=False,
        )

    def read_report(self, output: Path, report: PurePosixPath, limits: ReportLimits) -> Report:
        """Read the report that a run wrote at `report` inside the output directory."""
        return read_report(output, report, limits)
