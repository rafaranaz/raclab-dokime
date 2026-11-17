"""The contracts, the doubles and the runs that the tests of the gates of examples share."""

import json

from dokime.contract.model import Contract, Example, Requirement, Step
from dokime.core.findings import Finding
from dokime.core.observation import ObservationLimits
from dokime.core.repository import CommitName
from dokime.core.runtime import Digest
from dokime.core.verdicts import Verdict
from dokime.packs.model import Pack
from dokime.verify.examples import baseline, visible_examples
from tests.verify.doubles import AuditedDouble, Files, ObserverDouble, patch

IMAGE = Digest("sha256:" + "a" * 64)
PACK = Pack(
    name="p",
    dockerfile=".dokime/Dockerfile",
    command=("pytest",),
    report="report.xml",
    test_paths=("tests/**",),
    config_paths=("conftest.py",),
)


def requirement(name: str, kind: str) -> Requirement:
    return Requirement(id=name, kind=kind, text="", source="", replaces=None, line=3)


def example(name: str, requirement: str, origin: str = "human", line: int = 10) -> Example:
    return Example(
        id=name,
        requirement=requirement,
        case="",
        boundary="function",
        target="p:f",
        description=None,
        origin=origin,
        steps=(Step(input={"args": [1]}, expect={"returns": 2}),),
        line=line,
    )


def contract(
    *examples: Example, kinds: dict[str, str] | None = None, authorised: tuple[str, ...] = ()
) -> Contract:
    kinds = kinds or {"R-new": "new", "R-keep": "preserve", "R-change": "change"}
    return Contract(
        story="S-1",
        may_modify_tests=authorised,
        requirements=tuple(requirement(name, kind) for name, kind in kinds.items()),
        examples=examples,
        relations=(),
    )


def answers(**values: int) -> bytes:
    return json.dumps(values).encode()


def on_base(
    given: Contract, held: dict[str, int], *, missing_base: bool = False
) -> tuple[list[Finding], ObserverDouble]:
    """Run `baseline` on a base whose observer answers `held`."""
    repository, observer = AuditedDouble(), ObserverDouble()
    base = repository.add({"answers.json": answers(**held), "src/p.py": b"code"})
    if missing_base:
        base = CommitName("0" * 40)
    result = baseline(given, base, IMAGE, repository, observer, ObservationLimits())
    assert result.gate == "baseline"
    return list(result.findings), observer


def on_change(
    given: Contract,
    held: dict[str, int],
    observer: ObserverDouble | None = None,
    *,
    changed: bytes | None = None,
    base_files: Files | None = None,
) -> tuple[list[Finding], ObserverDouble]:
    """Run `visible-examples` on a patch after which the observer answers `held`."""
    repository, observer = AuditedDouble(), observer or ObserverDouble()
    base = repository.add(
        {"answers.json": b"{}", "src/p.py": b"code"} if base_files is None else base_files
    )
    if changed is None:
        changed = patch({"answers.json": json.dumps(held), "src/p.py": "new"})
    result = visible_examples(
        PACK, given, base, changed, IMAGE, repository, observer, ObservationLimits()
    )
    assert result.gate == "visible-examples"
    return list(result.findings), observer


def codes(findings: list[Finding]) -> list[tuple[str, Verdict]]:
    return [(f.code, f.verdict) for f in findings]
