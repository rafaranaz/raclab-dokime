"""The program that observes the examples inside the zone of verification (ADR-0063).

It runs in the container from a directory mounted read-only and needs only the standard library.

    python -I -S observe_program.py PROBE OUT

The main program reads `PROBE/requests.json`, runs each example in a child process of its own,

    python -I observe_program.py --step FD REQUESTS INDEX

in an empty working directory and within the time of one example, and writes what it saw to
`OUT/observations.json`. A child writes one line of JSON on the descriptor `FD` for each step it
observed, as soon as it observed it, so that an example that reaches its limit keeps the steps
before. The child imports its own modules before it appends the entries of `PYTHONPATH` to
`sys.path`, so that a module of the project cannot replace one of them.
"""

import contextlib
import importlib
import json
import os
import shlex
import signal
import subprocess
import sys
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

_IMPORT_FAILED = 3
"""The exit code of a child whose target cannot be imported or found."""


def main(argv: list[str]) -> int:
    """Run the main program, or the child of one example when the first argument is `--step`."""
    if argv[1:2] == ["--step"]:
        return _child(int(argv[2]), Path(argv[3]), int(argv[4]))
    if not sys.flags.isolated or not sys.flags.no_site:
        sys.stderr.write("the program that observes runs with python -I -S\n")
        return 2
    probe, out = Path(argv[1]), Path(argv[2])
    requests = json.loads((probe / "requests.json").read_text(encoding="utf-8"))
    observed = [
        _example(probe / "requests.json", index, request, requests["example_seconds"])
        for index, request in enumerate(requests["examples"])
    ]
    (out / "observations.json").write_text(json.dumps({"examples": observed}), encoding="utf-8")
    return 0


def _example(requests: Path, index: int, request: dict[str, Any], seconds: int) -> dict[str, Any]:
    """Run one example in a child, and observe how it ended."""
    work = tempfile.mkdtemp(prefix="example-")
    read, write = os.pipe()
    child = subprocess.Popen(
        [sys.executable, "-I", __file__, "--step", str(write), str(requests), str(index)],
        pass_fds=(write,),
        cwd=work,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    os.close(write)
    lines: list[bytes] = []
    reader = threading.Thread(target=_drain, args=(read, lines), daemon=True)
    reader.start()
    try:
        code = child.wait(timeout=seconds)
    except subprocess.TimeoutExpired:
        _end(child)
        code = None
    reader.join()
    steps = [json.loads(line) for line in b"".join(lines).splitlines() if line]
    observed = {"example": request["example"], "steps": steps, "ending": "completed"}
    if code is None:
        observed["ending"] = "time-limit"
    elif code < 0:
        observed |= {"ending": "crashed", "signal": -code}
    elif code != 0 or len(steps) < len(request["inputs"]):
        observed |= {"ending": "crashed", "exit_code": code}
    return observed


def _drain(descriptor: int, lines: list[bytes]) -> None:
    with os.fdopen(descriptor, "rb") as handle:
        lines.extend(iter(lambda: handle.read(65536), b""))


def _end(child: "subprocess.Popen[bytes]") -> None:
    """End the child and every process it started, which share its session."""
    with contextlib.suppress(ProcessLookupError):
        os.killpg(child.pid, signal.SIGKILL)
    child.wait()


def _child(descriptor: int, requests: Path, index: int) -> int:
    """Observe each step of one example, writing a line for each as soon as it is observed."""
    request = json.loads(requests.read_text(encoding="utf-8"))["examples"][index]
    output = os.fdopen(descriptor, "w", encoding="utf-8")
    sys.path.extend(entry for entry in os.environ.get("PYTHONPATH", "").split(os.pathsep) if entry)
    function: Callable[..., object] | None = None
    if request["boundary"] == "function":
        try:
            function = _target(request["target"])
        except Exception:
            return _IMPORT_FAILED
    for step in request["inputs"]:
        seen = _call(function, step) if function else _command(request["target"], step)
        output.write(json.dumps(seen) + "\n")
        output.flush()
    return 0


def _target(target: str) -> Callable[..., object]:
    """The function named `module:function`, where the function may be a dotted path."""
    module, _, path = target.partition(":")
    found: object = importlib.import_module(module)
    for name in path.split("."):
        found = getattr(found, name)
    if not callable(found):
        raise TypeError(f"{target} is not a function")
    return found


def _call(function: Callable[..., object], step: dict[str, Any]) -> dict[str, Any]:
    try:
        value = function(*step.get("args", []), **step.get("kwargs", {}))
    except BaseException as error:
        return {"raised": _raised(error)}
    try:
        text = json.dumps(value, allow_nan=False)
    except (TypeError, ValueError, RecursionError):
        return {"not_json": type(value).__name__}
    return {"returned": json.loads(text)}


def _raised(error: BaseException) -> dict[str, Any]:
    classes = [f"{kind.__module__}.{kind.__qualname__}" for kind in type(error).__mro__]
    return {
        "type": type(error).__name__,
        "qualified": classes[0],
        "classes": classes,
        "message": str(error),
    }


def _command(target: str, step: dict[str, Any]) -> dict[str, Any]:
    work = Path.cwd()
    for name, text in step.get("files", {}).items():
        (work / name).write_text(text, encoding="utf-8")
    done = subprocess.run(
        [*shlex.split(target), *step.get("args", [])],
        input=step.get("stdin", "").encode("utf-8"),
        env=os.environ | step.get("env", {}),
        capture_output=True,
        check=False,
    )
    return {
        "exit": done.returncode,
        "stdout": done.stdout.decode("utf-8", errors="replace"),
        "stderr": done.stderr.decode("utf-8", errors="replace"),
        "files": _files(work),
    }


def _files(work: Path) -> dict[str, str]:
    """The regular files of the working directory, by their path in it, reached by no link."""
    found = {}
    for directory, names, files in os.walk(work, followlinks=False):
        here = Path(directory)
        names[:] = [name for name in names if not (here / name).is_symlink()]
        for name in files:
            path = here / name
            if path.is_symlink() or not path.is_file():
                continue
            text = path.read_bytes().decode("utf-8", errors="replace")
            found[path.relative_to(work).as_posix()] = text
    return found


if __name__ == "__main__":
    sys.exit(main(sys.argv))
