"""Running the tests of a pack on a directory: the operation of the self-check and of verify.

The image is built from the Dockerfile that the caller read from the working copy, with the
directory as the context of the build, so that a `.dokime/` inside the directory plays no part.
The test command runs in that image with the directory as the project and an output directory
that the caller gives empty. Any exit code of the command is a report to read; a container killed
at a limit or for another reason, and any refusal of the runtime, end the run with a finding with
the verdict `ERROR`.
"""

from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from dokime.core.findings import Finding
from dokime.core.outcomes import Report, ReportLimits
from dokime.core.repository import RefusalError
from dokime.core.runtime import Build, BuildLimits, Ending, RunLimits, VerificationRuntime
from dokime.core.verdicts import Verdict
from dokime.packs.model import Pack


@dataclass(frozen=True)
class TestRun:
    """What a test run gave: the image it built, and the report or the finding that ended it."""

    __test__ = False  # not a class of tests, though its name starts with Test

    build: Build | None
    report: Report | None
    finding: Finding | None


def run_tests(
    pack: Pack, dockerfile: Path, directory: Path, output: Path, runtime: VerificationRuntime
) -> TestRun:
    """Build the image of the pack with `directory` as its context and run its tests there."""
    built: Build | None = None
    try:
        built = runtime.build(dockerfile, directory, BuildLimits())
        result = runtime.run(built.image, pack.command, directory, output, RunLimits())
        if result.ending is not Ending.EXITED:
            killed = Finding(
                code="run-killed",
                message=f"the container of the tests was killed: {result.ending.value}",
                verdict=Verdict.ERROR,
            )
            return TestRun(build=built, report=None, finding=killed)
        report = runtime.read_report(output, PurePosixPath(pack.report), ReportLimits())
    except RefusalError as refusal:
        return TestRun(build=built, report=None, finding=refusal.finding)
    return TestRun(build=built, report=report, finding=None)
