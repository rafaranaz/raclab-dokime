"""The sentinel of a sealed batch, looked for in what enters the zone (INV-2, INV-3).

The sentinel is the impossible value of the canary: it exists only in the batch, so finding it in
the tree of the change or in a request means that the content of the batch left it in clear. The
search is for the text as it is; content transformed on purpose is outside the threat model.
"""

import json
import os
from pathlib import Path

from dokime.core.findings import Finding
from dokime.core.observation import ExampleRequest
from dokime.core.verdicts import Verdict

_CHUNK = 1 << 20
"""The bytes of a file read at a time."""


def in_zone(sentinel: str, project: Path, requests: tuple[ExampleRequest, ...]) -> Finding | None:
    """The finding of a sentinel in the tree extracted at `project` or in a request, or None."""
    where = _in_tree(sentinel.encode(), project)
    if where is None and any(sentinel in _json(request) for request in requests):
        where = "a request to the zone"
    if where is None:
        return None
    message = f"the sentinel of the sealed batch is in {where}: the hold-out is not sealed"
    return Finding(code="sentinel-in-zone", message=message, verdict=Verdict.ERROR)


def _json(request: ExampleRequest) -> str:
    data = {
        "example": request.example,
        "boundary": str(request.boundary),
        "target": request.target,
        "inputs": [dict(step) for step in request.inputs],
    }
    return json.dumps(data, ensure_ascii=False, default=repr)


def _in_tree(sentinel: bytes, project: Path) -> str | None:
    """Where in the tree the sentinel is: a path, a link or a file; links are never followed."""
    for directory, directories, files in os.walk(project, followlinks=False):
        for name in (*directories, *files):
            path = Path(directory) / name
            relative = path.relative_to(project).as_posix().encode()
            if sentinel in relative:
                return "a path of the tree of the change"
            if path.is_symlink():
                if sentinel in os.fsencode(os.readlink(path)):
                    return "a link of the tree of the change"
            elif path.is_file() and _in_file(sentinel, path):
                return "a file of the tree of the change"
    return None


def _in_file(sentinel: bytes, path: Path) -> bool:
    """Whether the file holds the sentinel, read in chunks that overlap by its length."""
    tail = b""
    with path.open("rb") as file:
        while chunk := file.read(_CHUNK):
            if sentinel in tail + chunk:
                return True
            tail = chunk[-(len(sentinel) - 1) :] if len(sentinel) > 1 else b""
    return False
