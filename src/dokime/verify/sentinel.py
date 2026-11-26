"""The sentinel of a sealed batch, looked for in what enters the zone (INV-2, INV-3).

The sentinel is the impossible value of the canary: it exists only in the batch, so finding it in
the tree of the change or in a request means that the content of the batch left it in clear. The
search is for the text as it is; content transformed on purpose is outside the threat model.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from dokime.core.findings import Finding
from dokime.core.observation import ExampleRequest
from dokime.core.verdicts import Verdict

_CHUNK = 1 << 20
"""The bytes of a file read at a time."""


@dataclass(frozen=True)
class Place:
    """Where under a root the sentinel was found: in the name of a path, in the target of a link,
    or in the bytes of a file, with the path relative to the root."""

    kind: Literal["path", "link", "file"]
    relative: str


def in_zone(sentinel: str, project: Path, requests: tuple[ExampleRequest, ...]) -> Finding | None:
    """The finding of a sentinel in the tree extracted at `project` or in a request, or None."""
    place = find_in_tree(sentinel.encode(), project)
    where = None if place is None else f"a {place.kind} of the tree of the change"
    if where is None and any(sentinel in _json(request) for request in requests):
        where = "a request to the zone"
    if where is None:
        return None
    message = f"the sentinel of the sealed batch is in {where}: the hold-out is not sealed"
    return Finding(code="sentinel-in-zone", message=message, verdict=Verdict.ERROR)


def find_in_tree(sentinel: bytes, root: Path) -> Place | None:
    """The first place under `root`, in the order of the names, whose path, link target or bytes
    hold the sentinel, or None; links are never followed."""
    for directory, directories, files in os.walk(root, followlinks=False):
        directories.sort()
        for name in sorted((*directories, *files)):
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if sentinel in relative.encode():
                return Place("path", relative)
            if path.is_symlink():
                if sentinel in os.fsencode(os.readlink(path)):
                    return Place("link", relative)
            elif path.is_file() and _in_file(sentinel, path):
                return Place("file", relative)
    return None


def _json(request: ExampleRequest) -> str:
    data = {
        "example": request.example,
        "boundary": str(request.boundary),
        "target": request.target,
        "inputs": [dict(step) for step in request.inputs],
    }
    return json.dumps(data, ensure_ascii=False, default=repr)


def _in_file(sentinel: bytes, path: Path) -> bool:
    """Whether the file holds the sentinel, read in chunks that overlap by its length."""
    tail = b""
    with path.open("rb") as file:
        while chunk := file.read(_CHUNK):
            if sentinel in tail + chunk:
                return True
            tail = chunk[-(len(sentinel) - 1) :] if len(sentinel) > 1 else b""
    return False
