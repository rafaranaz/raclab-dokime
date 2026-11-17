"""A whole run, which the tests of the evidence change one part of at a time."""

import copy
import json
from dataclasses import replace
from typing import Any

from dokime.core.canonical import canonical
from dokime.core.findings import Finding
from dokime.core.ledger import Head
from dokime.core.policy import Policy
from dokime.core.repository import CommitName, TreeName
from dokime.core.runtime import Digest
from dokime.core.verdicts import Verdict
from dokime.evidence.run import (
    Checks,
    Contract,
    GateNotApplicable,
    GateRan,
    Image,
    Inputs,
    Requirement,
    Run,
)
from dokime.evidence.schema import read_back
from dokime.evidence.statement import build

TREE = TreeName("1" * 40)
BASE = CommitName("2" * 40)
PATCH = b"the patch"
IMAGE = Digest("sha256:" + "a" * 64)
PLATFORM = Digest("sha256:" + "b" * 64)
PROBE = Digest("sha256:" + "c" * 64)
HEAD = "sha256:" + "d" * 64
TEST = "tests.test_a::test_one"
FAILS = Finding(
    code="example-fails",
    message="the example E-1 of R-1: step 1 returns: expected 2, observed '**5**'",
    verdict=Verdict.FAIL,
    lines=(12,),
)
VARIES = Finding(
    code="example-varies-on-base",
    message="the example E-2 of R-1: every expectation of its steps held",
    verdict=Verdict.ASK,
    lines=(20, 21),
)
GATES = (
    GateRan("contract", Verdict.PASS),
    GateRan(
        "baseline",
        Verdict.ASK,
        findings=(VARIES,),
        checks=(Checks("human", 1), Checks("model", 3)),
        unstable_examples=("E-2",),
    ),
    GateRan(
        "existing-tests", Verdict.PASS, checks=(Checks("existing", 3),), unstable_tests=(TEST,)
    ),
    GateRan(
        "visible-examples",
        Verdict.FAIL,
        findings=(FAILS,),
        checks=(Checks("human", 1), Checks("model", 3)),
    ),
    GateNotApplicable("sealed-examples", "the gate is built in block B"),
)
CONTRACT = Contract(
    text=b"story: S-1\n",
    requirements=(
        Requirement("R-1", ("human", "model")),
        Requirement("R-2", ()),
        Requirement("R-3", ("model", "model")),
    ),
)


def run(**changes: Any) -> Run:
    """The whole run, with the fields given changed."""
    whole = Run(
        story="S-1",
        tree=TREE,
        patch=PATCH,
        verdict=Verdict.FAIL,
        harness="0.0.0",
        inputs=Inputs(
            base=BASE,
            policy=Policy(),
            image=Image(IMAGE, PLATFORM),
            pack=b"name: p\n",
            probe=PROBE,
        ),
        gates=GATES,
        ledger=Head(hash=HEAD, events=7),
        contract=CONTRACT,
    )
    return replace(whole, **changes)


def inputs(**changes: Any) -> Inputs:
    """The inputs of the whole run, with the fields given changed."""
    return replace(run().inputs, **changes)


def statement(given: Run | None = None) -> dict[str, Any]:
    """The statement of a run, read back from its bytes."""
    value: dict[str, Any] = json.loads(build(given or run()).data)
    return value


def predicate(given: Run | None = None) -> dict[str, Any]:
    """The predicate of the statement of a run."""
    value: dict[str, Any] = statement(given)["predicate"]
    return value


GONE = object()
"""A field taken out of the statement."""


def changed(*changes: tuple[str, object]) -> list[tuple[str, str]]:
    """The findings of the statement of the whole run with each place given changed."""
    value = copy.deepcopy(statement())
    for place, new in changes:
        *path, last = [int(part) if part.isdigit() else part for part in place.split("/")]
        parent: Any = value
        for part in path:
            parent = parent[part]
        if new is GONE:
            del parent[last]
        else:
            parent[last] = new
    found = read_back(canonical(value).encode())
    assert all(f.verdict is Verdict.ERROR for f in found)
    return [(f.code, f.message) for f in found]
