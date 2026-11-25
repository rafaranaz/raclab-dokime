# SDD-EARS: SANDBOX-128 SANDBOX-129 SANDBOX-130 SANDBOX-131
"""What the podman adapter passes into the container of an example, each part fixed: the
arguments of `podman run`, read from a podman that records them, and the mounts, the directory of
the program and the environment, seen from inside a container of the real podman."""

import json
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from dokime.core.observation import (
    Boundary,
    ExampleRequest,
    ObservationLimits,
    Returned,
)
from dokime.core.runtime import BuildLimits, Digest
from dokime.sandbox.podman import FILE_BYTES, OUTPUT, PROBE, PROJECT, PodmanRuntime
from tests.sandbox.engines import ENGINES, PYTHON, require

RECORDING = r"""
import json
import os
import shutil
import sys
from pathlib import Path

record = Path(os.environ["DOKIME_RECORD"])
args = sys.argv[1:]
with record.open("a") as written:
    written.write(json.dumps(args) + "\n")
if args == ["--version"]:
    print("podman version 5.4.2")
elif args[:2] == ["image", "inspect"]:
    print("")
elif args[:2] == ["container", "inspect"]:
    print("exited 0 false")
elif args[:1] == ["run"]:
    volumes = [args[i + 1] for i, a in enumerate(args) if a == "--volume"]
    hosts = {v.split(":")[1]: v.split(":")[0] for v in volumes}
    probe, out = Path(hosts["/dokime/probe"]), Path(hosts["/dokime/out"])
    shutil.copytree(probe, record.with_name("probe"), dirs_exist_ok=True)
    requests = json.loads((probe / "requests.json").read_text())
    examples = [
        {"example": e["example"], "ending": "completed", "steps": [{"returned": 0}]}
        for e in requests["examples"]
    ]
    (out / "observations.json").write_text(json.dumps({"examples": examples}))
"""


def recording_podman(directory: Path) -> Path:
    """A podman that records each call, answers the calls of an observation, and runs nothing."""
    directory.mkdir(parents=True)
    program = directory / "podman"
    program.write_text(f"#!{sys.executable}\n{RECORDING}")
    program.chmod(program.stat().st_mode | stat.S_IXUSR)
    return program


REQUEST = ExampleRequest(
    example="E-1", boundary=Boundary.FUNCTION, target="proj:add", inputs=({"args": [2, 3]},)
)
IMAGE = Digest("sha256:" + "a" * 64)


@pytest.fixture
def recorded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    record = tmp_path / "record" / "calls.jsonl"
    record.parent.mkdir()
    monkeypatch.setenv("DOKIME_RECORD", str(record))
    runtime = PodmanRuntime(podman=str(recording_podman(tmp_path / "bin")))
    project = tmp_path / "project"
    project.mkdir()
    runtime.observe(IMAGE, project, (REQUEST,), ObservationLimits())
    return [json.loads(line) for line in record.read_text().splitlines()]


def the_run(calls: list[list[str]]) -> list[str]:
    (run,) = [call for call in calls if call[:1] == ["run"]]
    return run


def volumes(run: list[str]) -> dict[str, str]:
    """Each mount of the run by its path in the container, with the host path and the mode."""
    found = [run[i + 1] for i, argument in enumerate(run) if argument == "--volume"]
    return {inside: f"{host}:{mode}" for host, inside, mode in (v.split(":") for v in found)}


def test_podman_run_gets_only_the_fixed_arguments(
    recorded: list[list[str]], tmp_path: Path
) -> None:
    run = the_run(recorded)
    limits = ObservationLimits().run
    mounts = volumes(run)
    probe, out = mounts[PROBE].split(":")[0], mounts[OUTPUT].split(":")[0]
    assert run == [
        "run",
        "--name",
        run[2],
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
        f"type=tmpfs,destination=/tmp,tmpfs-mode=1777,tmpfs-size={limits.memory_bytes // 4}",
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
        f"{(tmp_path / 'project').resolve()}:{PROJECT}:ro",
        "--volume",
        f"{out}:{OUTPUT}:rw",
        "--volume",
        f"{probe}:{PROBE}:ro",
        "--workdir",
        PROJECT,
        IMAGE.text,
        "python",
        "-I",
        "-S",
        f"{PROBE}/observe_program.py",
        PROBE,
        OUTPUT,
    ]
    assert run[2].startswith("dokime-")


def test_only_the_project_the_program_and_the_output_are_mounted(
    recorded: list[list[str]],
) -> None:
    mounts = volumes(the_run(recorded))
    assert sorted(mounts) == [OUTPUT, PROBE, PROJECT]
    assert [mounts[p].rsplit(":", 1)[1] for p in (PROJECT, PROBE, OUTPUT)] == ["ro", "ro", "rw"]


def test_no_variable_of_the_environment_is_set(recorded: list[list[str]]) -> None:
    run = the_run(recorded)
    flags = ("-e", "--env", "--env-file", "--env-host", "--env-merge", "--secret", "--unsetenv")
    for flag in flags:
        assert not any(a == flag or a.startswith(f"{flag}=") for a in run), flag


def test_the_directory_of_the_program_holds_only_the_program_and_the_requests(
    recorded: list[list[str]], tmp_path: Path
) -> None:
    probe = tmp_path / "record" / "probe"
    assert sorted(p.name for p in probe.iterdir()) == ["observe_program.py", "requests.json"]
    requests: dict[str, Any] = json.loads((probe / "requests.json").read_text())
    assert sorted(requests) == ["example_bytes", "example_seconds", "examples"]
    assert requests["examples"] == [
        {
            "example": "E-1",
            "boundary": "function",
            "target": "proj:add",
            "inputs": [{"args": [2, 3]}],
        }
    ]


INSIDE = """
import os


def zone():
    mounts = sorted(
        line.split()[4]
        for line in open("/proc/self/mountinfo")
        if line.split()[4].startswith("/dokime")
    )
    return {
        "mounts": mounts,
        "probe": sorted(os.listdir("/dokime/probe")),
        "environment": sorted(os.environ),
    }
"""


@pytest.fixture(scope="module")
def adapter() -> PodmanRuntime:
    require("podman")
    return PodmanRuntime()


@pytest.fixture(scope="module")
def image(adapter: PodmanRuntime, tmp_path_factory: pytest.TempPathFactory) -> Digest:
    context = tmp_path_factory.mktemp("context")
    ENGINES["podman"].pull(PYTHON)
    (context / "Dockerfile").write_text(f"FROM {PYTHON}\nENV PYTHONPATH=/dokime/project\n")
    return adapter.build(context / "Dockerfile", context, BuildLimits()).image


def test_inside_the_container_the_zone_is_what_the_adapter_fixes(
    adapter: PodmanRuntime, image: Digest, tmp_path: Path
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "proj.py").write_text(INSIDE)
    request = ExampleRequest(
        example="E-1", boundary=Boundary.FUNCTION, target="proj:zone", inputs=({},)
    )
    (observed,) = adapter.observe(image, project, (request,), ObservationLimits())
    (step,) = observed.steps
    assert isinstance(step, Returned)
    seen: dict[str, Any] = step.value  # type: ignore[assignment]
    assert seen["mounts"] == [OUTPUT, PROBE, PROJECT]
    assert seen["probe"] == ["observe_program.py", "requests.json"]
    listed = subprocess.run(
        [require("podman"), "image", "inspect", "--format", "{{json .Config.Env}}", image.text],
        capture_output=True,
        text=True,
        check=True,
    )
    of_the_image: list[str] = json.loads(listed.stdout)
    names = {entry.split("=", 1)[0] for entry in of_the_image}
    assert set(seen["environment"]) <= names | {"HOME", "HOSTNAME", "container"}
