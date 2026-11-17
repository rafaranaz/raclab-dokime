"""Run the program that observes the examples on this machine, as the container would run it."""

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROGRAM = Path(__file__).parents[2] / "src" / "dokime" / "sandbox" / "observe_program.py"


@dataclass(frozen=True)
class Run:
    code: int
    observed: list[dict[str, Any]] | None


def project(directory: Path, files: dict[str, str]) -> Path:
    """A directory of modules of a project, to put on `PYTHONPATH`."""
    directory.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return directory


def function(name: str, target: str, *inputs: dict[str, Any]) -> dict[str, Any]:
    return {"example": name, "boundary": "function", "target": target, "inputs": list(inputs)}


def cli(name: str, target: str, *inputs: dict[str, Any]) -> dict[str, Any]:
    return {"example": name, "boundary": "cli", "target": target, "inputs": list(inputs)}


def observe(
    tmp_path: Path,
    code: Path,
    *examples: dict[str, Any],
    seconds: int = 20,
    flags: tuple[str, ...] = ("-I", "-S"),
) -> Run:
    """Run the main program on these examples, with `code` on `PYTHONPATH`."""
    probe, out = tmp_path / "probe", tmp_path / "out"
    probe.mkdir(parents=True)
    out.mkdir()
    requests = {"example_seconds": seconds, "examples": list(examples)}
    (probe / "requests.json").write_text(json.dumps(requests))
    environment = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    environment |= {"PYTHONPATH": str(code), "TMPDIR": str(tmp_path)}
    done = subprocess.run(
        [sys.executable, *flags, str(PROGRAM), str(probe), str(out)],
        env=environment,
        capture_output=True,
        timeout=120,
        check=False,
    )
    written = out / "observations.json"
    observed = json.loads(written.read_text())["examples"] if written.exists() else None
    return Run(code=done.returncode, observed=observed)


def only(run: Run) -> dict[str, Any]:
    assert run.observed is not None, "no observations were written"
    (example,) = run.observed
    return example
