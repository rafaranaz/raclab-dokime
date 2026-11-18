# SDD-EARS: INTERFACES-125 INTERFACES-126 INTERFACES-127 INTERFACES-131
"""`audit` with the real git and podman, on a small repository made for the test.

The code of the project is `p.py`, which the Dockerfile copies into the site-packages of the image,
so that each side is observed in an image built with its own tree. The tests are a script that
writes a JUnit report with one test that passes.
"""

import importlib.metadata
import json
import os
import signal
import subprocess
import sys
import time
import tomllib
from pathlib import Path

import pytest

from dokime.core.ledger import verify
from dokime.evidence.schema import read_back
from dokime.interfaces import audit_command
from dokime.interfaces.audit_command import LEDGER
from tests.sandbox.engines import ENGINES, PYTHON, require

STORY = "add-one-but-not-to-zero"
CONTRACT = f"""\
format: 1
story: {STORY}
may_modify_tests: []

requirements:
  - id: add-one
    kind: new
    text: When the function is given a number other than zero, the system shall add one to it.
    source: written
  - id: keep-zero
    kind: preserve
    text: When the function is given zero, the system shall return zero.
    source: written

examples:
  - id: E-0001
    requirement: add-one
    case: normal
    boundary: function
    target: p:f
    origin: human
    steps:
      - input: {{args: [1]}}
        expect: {{returns: 2}}
  - id: E-0002
    requirement: keep-zero
    case: zero
    boundary: function
    target: p:f
    origin: human
    steps:
      - input: {{args: [0]}}
        expect: {{returns: 0}}
"""
PACK = """\
format: 1
name: small
environment:
  dockerfile: Dockerfile
tests:
  command: [sh, /dokime/project/run.sh]
  report: report.xml
  paths: ["tests/**"]
  config: ["pytest.ini"]
"""
RUN = """\
#!/bin/sh
echo '<testsuite><testcase classname="tests" name="test_one"/></testsuite>' > /dokime/out/report.xml
"""
SITE = "/usr/local/lib/python3.13/site-packages"
SLOW = RUN.replace("#!/bin/sh\n", "#!/bin/sh\nsleep 120\n")


def git(project: Path, *args: str) -> str:
    environment = {
        **os.environ,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.com",
        "GIT_AUTHOR_DATE": "1700000000 +0000",
        "GIT_COMMITTER_DATE": "1700000000 +0000",
    }
    done = subprocess.run(
        ["git", "-C", str(project), *args],
        capture_output=True,
        text=True,
        check=True,
        env=environment,
    )
    return done.stdout


def make_project(root: Path, run: str = RUN) -> tuple[Path, str, Path]:
    """A project with one commit, and the patch of a change on it in a file of its own."""
    project = root / "project"
    files = {
        "p.py": "def f(x):\n    return x\n",
        "run.sh": run,
        "tests/test_one.txt": "one\n",
        ".dokime/pack.yaml": PACK,
        ".dokime/Dockerfile": f"FROM {PYTHON}\nCOPY p.py {SITE}/p.py\n",
        f".dokime/changes/{STORY}/contract.yaml": CONTRACT,
    }
    for path, text in files.items():
        (project / path).parent.mkdir(parents=True, exist_ok=True)
        (project / path).write_text(text)
    git(project, "init", "--quiet", "--initial-branch=main")
    git(project, "add", "--all")
    git(project, "commit", "--quiet", "--message", "base")
    base = git(project, "rev-parse", "HEAD").strip()
    (project / "p.py").write_text("def f(x):\n    return x + 1 if x else 0\n")
    patch = root / "change.patch"
    patch.write_text(git(project, "diff"))
    git(project, "checkout", "--quiet", "--", "p.py")
    return project, base, patch


@pytest.fixture
def temporary(tmp_path: Path) -> Path:
    directory = tmp_path / "temporary"
    directory.mkdir()
    return directory


def dokime(*args: str, temporary: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "dokime.interfaces", *args],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "TMPDIR": str(temporary)},
        timeout=900,
    )


def engines() -> None:
    require("git")
    require("podman")
    ENGINES["podman"].pull(PYTHON)


def test_a_change_that_meets_its_contract_passes_with_its_evidence(
    tmp_path: Path, temporary: Path
) -> None:
    engines()
    project, base, patch = make_project(tmp_path)
    out = tmp_path / "out"
    before = ENGINES["podman"].containers()
    done = dokime(
        "audit",
        "--project",
        str(project),
        "--base",
        base,
        "--patch",
        str(patch),
        "--story",
        STORY,
        "--out",
        str(out),
        temporary=temporary,
    )
    assert done.returncode == 0, done.stdout + done.stderr
    lines = done.stdout.splitlines()
    assert "gate visible-examples: run PASS" in lines
    assert lines[-1] == "PASS: no findings"
    evidence = out / f"{STORY}.statement.json"
    assert read_back(evidence.read_bytes()) == ()
    predicate = json.loads(evidence.read_bytes())["predicate"]
    assert predicate["verdict"] == "PASS"
    assert predicate["verifier"]["harness"]
    assert predicate["inputs"]["probe"].startswith("sha256:")
    ledger = (out / "ledger.jsonl").read_text().splitlines()
    assert verify(ledger) == ()
    assert json.loads(ledger[-1])["type"] == "run.finished"
    assert sorted(p.name for p in out.iterdir()) == sorted([LEDGER, f"{STORY}.statement.json"])
    assert ENGINES["podman"].containers() <= before
    assert list(temporary.iterdir()) == []


def test_a_project_that_is_not_a_repository_is_refused_on_opening(
    tmp_path: Path, temporary: Path
) -> None:
    require("git")
    require("podman")
    (tmp_path / "not-a-repository").mkdir()
    patch = tmp_path / "change.patch"
    patch.write_text("")
    done = dokime(
        "audit",
        "--project",
        str(tmp_path / "not-a-repository"),
        "--base",
        "a" * 40,
        "--patch",
        str(patch),
        "--story",
        STORY,
        "--out",
        str(tmp_path / "out"),
        temporary=temporary,
    )
    assert done.returncode == 2
    assert "ERROR not-a-repository" in done.stdout


def running_containers() -> list[str]:
    listed = ENGINES["podman"].command("ps", "--filter", "name=^dokime-", "--format", "{{.Names}}")
    return listed.split()


@pytest.mark.parametrize("sent", [signal.SIGTERM, signal.SIGINT])
def test_an_interruption_in_the_middle_of_an_audit_leaves_no_container_and_no_directory(
    tmp_path: Path, temporary: Path, sent: signal.Signals
) -> None:
    engines()
    project, base, patch = make_project(tmp_path, SLOW)
    engine = ENGINES["podman"]
    before = engine.containers()
    harness = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "dokime.interfaces",
            "audit",
            "--project",
            str(project),
            "--base",
            base,
            "--patch",
            str(patch),
            "--story",
            STORY,
            "--out",
            str(tmp_path / "out"),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "TMPDIR": str(temporary)},
    )
    try:
        deadline = time.monotonic() + 300
        while not any(name for name in running_containers() if name not in before):
            assert time.monotonic() < deadline, "the container of the tests never started"
            assert harness.poll() is None, harness.communicate()
            time.sleep(0.2)
        harness.send_signal(sent)
        harness.communicate(timeout=60)
    finally:
        harness.kill()
    assert harness.returncode == -sent
    assert engine.containers() <= before
    assert list(temporary.iterdir()) == []


def test_the_version_is_that_of_the_installed_distribution() -> None:
    installed = importlib.metadata.version("raclab-dokime")
    assert audit_command._version() == installed != audit_command.UNVERSIONED


def test_the_distribution_is_the_name_of_the_project() -> None:
    project = tomllib.loads((Path(__file__).parents[2] / "pyproject.toml").read_text())
    assert project["project"]["name"] == audit_command.DISTRIBUTION


def test_a_distribution_that_is_not_installed_is_unversioned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing(name: str) -> str:
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, "version", missing)
    assert audit_command._version() == audit_command.UNVERSIONED == "unversioned"
