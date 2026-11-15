# SDD-EARS: PACKS-050 PACKS-051 PACKS-052 PACKS-053 PACKS-054 PACKS-055 PACKS-056
from pathlib import Path, PurePosixPath

import pytest

from dokime.core.outcomes import Outcome, ReportLimits
from dokime.core.runtime import BuildLimits, RunLimits
from dokime.core.verdicts import Verdict
from dokime.packs.testrun import run_tests
from tests.packs.doubles import BASE, CODE, FakeRuntime, pack


@pytest.fixture
def dockerfile(tmp_path: Path) -> Path:
    path = tmp_path / "pack" / "Dockerfile"
    path.parent.mkdir()
    path.write_text("FROM the-working-copy\n")
    return path


def directory(tmp_path: Path, code: bytes, *extra: tuple[str, bytes]) -> Path:
    tree = tmp_path / "tree"
    (tree / "src").mkdir(parents=True)
    (tree / "tests").mkdir()
    (tree / CODE).write_bytes(code)
    (tree / "tests" / "test_one.py").write_bytes(b"expects:good")
    for path, data in extra:
        (tree / path).parent.mkdir(parents=True, exist_ok=True)
        (tree / path).write_bytes(data)
    return tree


def output(tmp_path: Path) -> Path:
    out = tmp_path / "out"
    out.mkdir()
    return out


def test_the_image_is_built_from_the_dockerfile_of_the_working_copy_ignoring_the_tree(
    tmp_path: Path, dockerfile: Path
) -> None:
    runtime = FakeRuntime()
    tree = directory(tmp_path, b"good", (".dokime/Dockerfile", b"FROM the-old-tree\n"))
    run_tests(pack(), dockerfile, tree, output(tmp_path), runtime)
    assert [(text, context) for text, context, _ in runtime.builds] == [
        ("FROM the-working-copy\n", tree)
    ]


def test_the_command_runs_in_the_image_with_the_directory_and_an_empty_output(
    tmp_path: Path, dockerfile: Path
) -> None:
    runtime = FakeRuntime()
    tree, out = directory(tmp_path, b"good"), output(tmp_path)
    run = run_tests(pack(), dockerfile, tree, out, runtime)
    assert run.build is not None
    ((image, command, project, given_output, _),) = runtime.runs
    assert (image, command, project, given_output) == (run.build.image, pack().command, tree, out)


@pytest.mark.parametrize(("code", "outcome"), [(b"good", Outcome.PASSED), (b"bad", Outcome.FAILED)])
def test_the_report_is_read_whatever_the_exit_code(
    tmp_path: Path, dockerfile: Path, code: bytes, outcome: Outcome
) -> None:
    runtime = FakeRuntime()
    run = run_tests(pack(), dockerfile, directory(tmp_path, code), output(tmp_path), runtime)
    assert (run.report, run.finding) == ({"tests/test_one.py": outcome}, None)
    ((_, report, _),) = runtime.readings
    assert report == PurePosixPath(pack().report)


def test_the_run_gives_the_image_and_its_base(tmp_path: Path, dockerfile: Path) -> None:
    runtime = FakeRuntime()
    run = run_tests(pack(), dockerfile, directory(tmp_path, b"good"), output(tmp_path), runtime)
    assert run.build is not None
    assert run.build.base == BASE
    assert run.build.image.text.startswith("sha256:")


def test_the_default_limits_are_passed(tmp_path: Path, dockerfile: Path) -> None:
    runtime = FakeRuntime()
    run_tests(pack(), dockerfile, directory(tmp_path, b"good"), output(tmp_path), runtime)
    assert runtime.builds[0][2] == BuildLimits()
    assert runtime.runs[0][4] == RunLimits()
    assert runtime.readings[0][2] == ReportLimits()


@pytest.mark.parametrize(
    ("refused", "code"),
    [("build", "build-failed"), ("run", "podman-failed"), ("read", "report-unreadable")],
)
def test_a_refusal_of_the_runtime_gives_its_finding_with_the_verdict_error(
    tmp_path: Path, dockerfile: Path, refused: str, code: str
) -> None:
    runtime = FakeRuntime(refuse=refused)
    run = run_tests(pack(), dockerfile, directory(tmp_path, b"good"), output(tmp_path), runtime)
    assert run.finding is not None
    assert (run.finding.code, run.finding.verdict, run.report) == (code, Verdict.ERROR, None)


@pytest.mark.parametrize("ending", ["time-limit", "memory-limit", "killed"])
def test_a_killed_container_gives_run_killed_naming_the_cause(
    tmp_path: Path, dockerfile: Path, ending: str
) -> None:
    runtime = FakeRuntime()
    tree = directory(tmp_path, b"good", ("ending", ending.encode()))
    run = run_tests(pack(), dockerfile, tree, output(tmp_path), runtime)
    assert run.finding is not None
    assert (run.finding.code, run.finding.verdict) == ("run-killed", Verdict.ERROR)
    assert ending in run.finding.message
    assert runtime.readings == []
