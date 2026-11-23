"""The adapter of the verification runtime that builds and runs with the `podman` command.

`podman build` and `podman run` share the local store of images, so the image a build gives is
the one a run starts. A run has no network, limits of memory with swap, processor and processes, a
read-only root with a `/tmp` of its own, the project mounted read-only and the output directory
writable (ADR-0043), and no capabilities and no way to gain privileges. Each run has a container
named for it alone, which is removed however the run ends, an interruption of the harness included.
"""

import contextlib
import hashlib
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

from dokime.core.observation import ExampleObservation, ExampleRequest, ObservationLimits
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
from dokime.sandbox.observations import read_observations
from dokime.sandbox.report import expat_version, read_report

MINIMUM_VERSION = (4, 9)
"""The podman of ubuntu-24.04, where CI runs: reasoning, not a measurement of older versions."""

FILE_BYTES = 64 * 1024 * 1024
"""The largest file a run may write, in `/tmp` and in the mounts of the disk: room for a report
or for the observations, whose limits are 32 MiB, and not for a file that grows without end."""

PROJECT = "/dokime/project"
PROBE = "/dokime/probe"
_PROGRAM = Path(__file__).with_name("observe_program.py")
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
        return self._contained(image, command, project, output, limits, ())[0]

    def _contained(
        self,
        image: Digest,
        command: tuple[str, ...],
        project: Path,
        output: Path,
        limits: RunLimits,
        mounts: tuple[str, ...],
    ) -> tuple[RunResult, str]:
        """Run a command in a container of its own, removed however it ends; give how it
        ended and the last lines of its error output."""
        name = f"dokime-{uuid.uuid4().hex}"
        try:
            with _sigterm_raises(), tempfile.TemporaryDirectory(prefix="dokime-run-") as work:
                result = self._run(
                    name, image, command, project, output, limits, Path(work), mounts
                )
                return result, _last_lines(Path(work) / "errors")
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
        mounts: tuple[str, ...] = (),
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
                    "type=tmpfs,destination=/tmp,tmpfs-mode=1777,"
                    f"tmpfs-size={limits.memory_bytes // 4}",
                    "--ulimit",
                    f"fsize={FILE_BYTES}",
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
                    *mounts,
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

    observe_program_digest = "sha256:" + hashlib.sha256(_PROGRAM.read_bytes()).hexdigest()
    """The digest of the program that observes the examples, which the evidence records."""

    def observe(
        self,
        image: Digest,
        project: Path,
        requests: tuple[ExampleRequest, ...],
        limits: ObservationLimits,
    ) -> tuple[ExampleObservation, ...]:
        """Observe each example of the requests in a container of the image of its own (ADR-0063,
        ADR-0080), so that nothing one example leaves reaches another.

        The program and the request are mounted read-only; each example gets its share of the
        bytes of the observations, which are read with bounds when its container has ended. The
        time limit of an example counts from the start of its child, so the start of its container
        is bounded by the limits of a run and not charged to the example.
        """
        if not project.is_dir():
            raise ValueError(f"the project directory {project} is not an existing directory")
        self._check_user(image)
        share = max(1, limits.observations_bytes // max(1, len(requests)))
        return tuple(
            observed
            for request in requests
            for observed in self._observe_one(image, project, request, limits, share)
        )

    def _observe_one(
        self,
        image: Digest,
        project: Path,
        request: ExampleRequest,
        limits: ObservationLimits,
        share: int,
    ) -> tuple[ExampleObservation, ...]:
        with tempfile.TemporaryDirectory(prefix="dokime-observe-") as work:
            probe, output = Path(work) / "probe", Path(work) / "out"
            probe.mkdir()
            output.mkdir()
            shutil.copyfile(_PROGRAM, probe / _PROGRAM.name)
            (probe / "requests.json").write_text(
                json.dumps(
                    {
                        "example_seconds": limits.example_seconds,
                        "example_bytes": share,
                        "examples": [_request(request)],
                    }
                ),
                encoding="utf-8",
            )
            command = ("python", "-I", "-S", f"{PROBE}/{_PROGRAM.name}", PROBE, OUTPUT)
            mounts = ("--volume", f"{probe.resolve()}:{PROBE}:ro")
            result, said = self._contained(image, command, project, output, limits.run, mounts)
            if result != RunResult(ending=Ending.EXITED, exit_code=0):
                raise RefusalError(
                    "observation-failed",
                    f"the program that observes ended as {result.ending}"
                    f" ({result.exit_code}):\n{said or 'no output'}",
                )
            return read_observations(output, (request,), share)

    def read_report(self, output: Path, report: PurePosixPath, limits: ReportLimits) -> Report:
        """Read the report that a run wrote at `report` inside the output directory."""
        return read_report(output, report, limits)


def _request(request: ExampleRequest) -> dict[str, object]:
    return {
        "example": request.example,
        "boundary": str(request.boundary),
        "target": request.target,
        "inputs": [dict(step) for step in request.inputs],
    }
