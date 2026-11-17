"""A change to audit on the doubles of the ports, which the tests of the run of `audit` share."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dokime.core.runtime import Build, BuildLimits, Digest
from dokime.interfaces.audit import Audited, Ports, Request, run_audit
from tests.core.ledgers import Lines, Ticks
from tests.verify.doubles import AuditedDouble, Files, ObserverDouble, RuntimeDouble, patch

STORY = "add-one-to-a-number"
CONTRACT = f"""\
format: 1
story: {STORY}
may_modify_tests: []

requirements:
  - id: add-one
    kind: new
    text: When the function is given a number, the system shall return the number plus one.
    source: written
  - id: keep-zero
    kind: preserve
    text: When the function is given zero, the system shall return one.
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
        expect: {{returns: 1}}
""".encode()
PACK = b"""\
format: 1
name: p
environment:
  dockerfile: Dockerfile
tests:
  command: [pytest]
  report: report.xml
  paths: ["tests/**"]
  config: ["conftest.py"]
"""
DOCKERFILE = b"FROM scratch\n"
TEST = "tests.test_p::test_one"
CONTRACT_PATH = f".dokime/changes/{STORY}/contract.yaml"
PROBE = Digest("sha256:" + "c" * 64)
ON_BASE = {"E-0001": 1, "E-0002": 1}
ON_CHANGE = {"E-0001": 2, "E-0002": 1}


def base_files(**changes: bytes | None) -> Files:
    """The files of the base commit, with some changed, or left out when given `None`."""
    files: dict[str, Any] = {
        CONTRACT_PATH: CONTRACT,
        ".dokime/pack.yaml": PACK,
        ".dokime/Dockerfile": DOCKERFILE,
        "answers.json": json.dumps(ON_BASE).encode(),
        "outcomes.json": json.dumps([{TEST: "passed"}]).encode(),
        "src/p.py": b"code",
    }
    for name, data in changes.items():
        path = name.replace("__", "/")
        if data is None:
            files.pop(path, None)
        else:
            files[path] = data
    return files


def change(**sets: str) -> bytes:
    """The patch of the change: the answers of the change and new code, with the sets given."""
    return patch({"answers.json": json.dumps(ON_CHANGE), "src/p.py": "new", **sets})


@dataclass
class BuildsRecorded(RuntimeDouble):
    """The runtime double, recording the Dockerfile and the context of each build."""

    builds: list[tuple[Path, bytes, Path, set[str]]] = field(default_factory=list)

    def build(self, dockerfile: Path, directory: Path, limits: BuildLimits) -> Build:
        context = {p.relative_to(directory).as_posix() for p in directory.rglob("*")}
        self.builds.append((dockerfile, dockerfile.read_bytes(), directory, context))
        return Build(image=Digest("sha256:" + "b" * 64), base=None)


@dataclass
class Done:
    """An audit run on the doubles, with what each double saw."""

    audited: Audited
    store: Lines
    repository: AuditedDouble
    runtime: BuildsRecorded
    observer: ObserverDouble

    def events(self) -> list[dict[str, Any]]:
        return [json.loads(line) for line in self.store.lines()]

    def statement(self) -> dict[str, Any]:
        assert self.audited.evidence is not None
        value: dict[str, Any] = json.loads(self.audited.evidence.data)
        return value

    def gates(self) -> list[dict[str, Any]]:
        value: list[dict[str, Any]] = self.statement()["predicate"]["gates"]
        return value


def audit(
    files: Files | None = None,
    changed: bytes | None = None,
    *,
    runtime: BuildsRecorded | None = None,
    observer: ObserverDouble | None = None,
    repository: AuditedDouble | None = None,
    **request: Any,
) -> Done:
    """Audit a change on the doubles."""
    repository = repository or AuditedDouble()
    base = repository.add(base_files() if files is None else files)
    runtime = runtime or BuildsRecorded()
    observer = observer or ObserverDouble()
    store = Lines()
    asked = Request(
        base=base,
        patch=change() if changed is None else changed,
        harness="0.0.0",
        **({"story": STORY} | request),
    )
    audited = run_audit(asked, Ports(repository, runtime, observer, PROBE), store, Ticks())
    return Done(audited, store, repository, runtime, observer)
