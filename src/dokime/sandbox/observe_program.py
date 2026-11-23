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
_OUTPUT_LIMIT = 4
"""The exit code of a child whose command wrote more than the bytes of one example."""
_REPR_KEPT = 1000
"""The characters of a `repr` that the harness keeps, `REPR_LIMIT` of `core`; this program needs
only the standard library, so it has the number of its own."""


class _TooLargeError(Exception):
    """What a command wrote, or left in the working directory, passes the bytes of one example."""


def main(argv: list[str]) -> int:
    """Run the main program, or the child of one example when the first argument is `--step`."""
    if argv[1:2] == ["--step"]:
        return _child(int(argv[2]), Path(argv[3]), int(argv[4]))
    if not sys.flags.isolated or not sys.flags.no_site:
        sys.stderr.write("the program that observes runs with python -I -S\n")
        return 2
    probe, out = Path(argv[1]), Path(argv[2])
    requests = json.loads((probe / "requests.json").read_text(encoding="utf-8"))
    outside = _names_outside(requests["examples"])
    if outside:
        sys.stderr.write(f"the files {outside} would be written outside the working directory\n")
        return 2
    limits = requests["example_seconds"], requests["example_bytes"]
    observed = [
        _example(probe / "requests.json", index, request, *limits)
        for index, request in enumerate(requests["examples"])
    ]
    (out / "observations.json").write_text(json.dumps({"examples": observed}), encoding="utf-8")
    return 0


def _names_outside(examples: list[dict[str, Any]]) -> list[str]:
    """The names of files of steps at `cli` that are absolute or go up with `..`."""
    names = (
        name
        for example in examples
        if example["boundary"] == "cli"
        for step in example["inputs"]
        for name in step.get("files", {})
    )
    return [name for name in names if name.startswith("/") or ".." in name.split("/")]


def _example(
    requests: Path, index: int, request: dict[str, Any], seconds: int, size: int
) -> dict[str, Any]:
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
    flooded = threading.Event()
    reader = threading.Thread(target=_drain, args=(read, lines, size, flooded, child), daemon=True)
    reader.start()
    try:
        code: int | None = child.wait(timeout=seconds)
    except subprocess.TimeoutExpired:
        _end(child)
        code = None
    reader.join()
    steps, broken = _steps(b"".join(lines))
    observed: dict[str, Any] = {"example": request["example"], "steps": steps}
    if flooded.is_set() or code == _OUTPUT_LIMIT:
        return observed | {"ending": "output-limit"}
    if code is None:
        return observed | {"ending": "time-limit"}
    if code < 0:
        return observed | {"ending": "crashed", "signal": -code}
    if broken or code != 0 or len(steps) < len(request["inputs"]):
        return observed | {"ending": "crashed", "exit_code": code}
    return observed | {"ending": "completed"}


def _steps(data: bytes) -> tuple[list[Any], bool]:
    """The steps of the lines a child wrote, up to the first that cannot be read, and whether
    there was one: a child cut while it wrote, or code under test that wrote on the descriptor."""
    steps = []
    for line in data.splitlines():
        try:
            steps.append(json.loads(line))
        except (ValueError, RecursionError):
            return steps, True
    return steps, False


def _drain(
    descriptor: int,
    lines: list[bytes],
    size: int,
    flooded: threading.Event,
    child: "subprocess.Popen[bytes]",
) -> None:
    """Read what a child writes, no more than its bytes; past them, end it."""
    taken = 0
    with os.fdopen(descriptor, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            taken += len(chunk)
            if taken > size:
                flooded.set()
                _end(child)
                return
            lines.append(chunk)


def _end(child: "subprocess.Popen[bytes]") -> None:
    """End the child and every process it started, which share its session."""
    with contextlib.suppress(ProcessLookupError):
        os.killpg(child.pid, signal.SIGKILL)
    child.wait()


def _child(descriptor: int, requests: Path, index: int) -> int:
    """Observe each step of one example, writing a line for each as soon as it is observed."""
    loaded = json.loads(requests.read_text(encoding="utf-8"))
    request, size = loaded["examples"][index], loaded["example_bytes"]
    output = os.fdopen(descriptor, "w", encoding="utf-8")
    sys.path.extend(entry for entry in os.environ.get("PYTHONPATH", "").split(os.pathsep) if entry)
    function: Callable[..., object] | None = None
    if request["boundary"] == "function":
        try:
            function = _target(request["target"])
        except Exception:
            return _IMPORT_FAILED
    returned: list[object] = []
    calls = any("call" in step for step in request["inputs"])
    for index, step in enumerate(request["inputs"]):
        if calls and index > 0 and not returned:
            break
        try:
            if function is None:
                seen = _command(request["target"], step, size)
            elif "call" in step:
                seen = _method(returned[0], step)
            else:
                seen = _call(function, step, returned if index == 0 else None)
        except _TooLargeError:
            return _OUTPUT_LIMIT
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


def _call(
    function: Callable[..., object], step: dict[str, Any], kept: list[object] | None = None
) -> dict[str, Any]:
    """Call the function with the arguments of the step; what the first step returns is kept in
    `kept`, the object whose methods the later steps with `call` call (ADR-0079)."""
    try:
        value = function(*step.get("args", []), **step.get("kwargs", {}))
    except BaseException as error:
        return {"raised": _raised(error)}
    if kept is not None:
        kept.append(value)
    try:
        text = json.dumps(value, allow_nan=False)
    except (TypeError, ValueError, RecursionError):
        return {"not_json": _not_json(value)}
    return {"returned": json.loads(text)}


def _method(owner: object, step: dict[str, Any]) -> dict[str, Any]:
    """Call the method that `call` names on what the first step returned."""
    try:
        method = getattr(owner, step["call"])
    except BaseException as error:
        return {"raised": _raised(error)}
    return _call(method, step)


def _not_json(value: object) -> dict[str, Any]:
    """The type of a value that JSON cannot hold and its `repr`, one character past the limit of
    the harness so that it can tell a longer one, or no `repr` when `repr` raises."""
    seen: dict[str, Any] = {"type": type(value).__name__}
    try:
        seen["repr"] = repr(value)[: _REPR_KEPT + 1]
    except BaseException:
        return seen
    return seen


def _raised(error: BaseException) -> dict[str, Any]:
    classes = [f"{kind.__module__}.{kind.__qualname__}" for kind in type(error).__mro__]
    return {
        "type": type(error).__name__,
        "qualified": classes[0],
        "classes": classes,
        "message": _message(error),
    }


def _message(error: BaseException) -> str:
    try:
        return str(error)
    except Exception as unreadable:
        return f"the message cannot be read: {type(unreadable).__name__} from __str__"


def _command(target: str, step: dict[str, Any], size: int) -> dict[str, Any]:
    work = Path.cwd()
    for name, text in step.get("files", {}).items():
        (work / name).write_text(text, encoding="utf-8")
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        done = subprocess.run(
            [*shlex.split(target), *step.get("args", [])],
            input=step.get("stdin", "").encode("utf-8"),
            env=os.environ | step.get("env", {}),
            stdout=out,
            stderr=err,
            check=False,
        )
        stdout, stderr = _bounded(out, size), _bounded(err, size)
    return {
        "exit": done.returncode,
        "stdout": stdout.decode("utf-8", errors="replace"),
        "stderr": stderr.decode("utf-8", errors="replace"),
        "files": _files(work, size),
    }


def _bounded(handle: Any, size: int) -> bytes:
    """What a command wrote to a file, refused past the bytes of one example."""
    handle.seek(0)
    data: bytes = handle.read(size + 1)
    if len(data) > size:
        raise _TooLargeError
    return data


def _files(work: Path, size: int) -> dict[str, str]:
    """The regular files of the working directory, by their path in it, reached by no link, and
    no more of them in all than the bytes of one example."""
    found = {}
    taken = 0
    for directory, names, files in os.walk(work, followlinks=False):
        here = Path(directory)
        names[:] = [name for name in names if not (here / name).is_symlink()]
        for name in files:
            path = here / name
            if path.is_symlink() or not path.is_file():
                continue
            taken += path.stat().st_size
            if taken > size:
                raise _TooLargeError
            text = path.read_bytes().decode("utf-8", errors="replace")
            found[path.relative_to(work).as_posix()] = text
    return found


if __name__ == "__main__":
    sys.exit(main(sys.argv))
