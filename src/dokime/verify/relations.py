"""The gate `relations` (ADR-0013, ADR-0076).

The gate runs each relation of the contract on its sources, the visible examples of its requirement
at its target that have one step; a held-out example is never one, since the gate runs where the
key may not be. It observes the sources on the tree of the change, builds their follow-ups with
the oracle, observes them on the same tree, and compares each follow-up with its source with the
input of each run. The orders of a source are drawn with a seed derived from the seed of the run
and the ids of the relation and the source, so that sources of the same length do not all get the
same orders. A check of a relation is of origin `derived`: approved by a person, applied
mechanically, and it fails when it does not hold.
"""

import hashlib
import tempfile
from dataclasses import dataclass
from pathlib import Path

from dokime.contract.model import Contract, Example, Relation
from dokime.core.findings import Finding
from dokime.core.observation import (
    Boundary,
    Ending,
    ExampleObservation,
    ExampleObserver,
    ExampleRequest,
    ObservationLimits,
    StepObservation,
)
from dokime.core.repository import AuditedRepository, CommitName, RefusalError
from dokime.core.runtime import Digest
from dokime.core.verdicts import Verdict
from dokime.oracle.relations import holds, in_order, items_of, orders, repeated, words
from dokime.packs.model import Pack
from dokime.verify.examples import _request
from dokime.verify.result import GateResult, checks_of
from dokime.verify.trees import change_tree

GATE = "relations"


@dataclass(frozen=True)
class FailedFollowUp:
    """A follow-up that did not hold: its relation, its source and, for `order-insensitive`, its
    order as indices of the items of the source."""

    relation: str
    example: str
    order: tuple[int, ...] | None


@dataclass(frozen=True)
class RelationsOutcome:
    """The result of the gate, the seed of the run, and each follow-up that did not hold."""

    result: GateResult
    seed: int
    failed: tuple[FailedFollowUp, ...]


@dataclass(frozen=True)
class _FollowUp:
    relation: Relation
    source: Example
    order: tuple[int, ...] | None
    source_given: dict[str, object]
    given: dict[str, object]
    observed: StepObservation


def source_seed(seed: int, relation: str, example: str) -> int:
    """The seed that draws the orders of one source of one relation: 48 bits of the digest of the
    seed of the run and the two ids."""
    drawn = hashlib.sha256(f"{seed}/{relation}/{example}".encode()).digest()
    return int.from_bytes(drawn[:6], "big")


def relations(
    pack: Pack,
    contract: Contract,
    base: CommitName,
    patch: bytes,
    image: Digest,
    repository: AuditedRepository,
    observer: ExampleObserver,
    limits: ObservationLimits,
    seed: int,
    permutations: int,
) -> RelationsOutcome:
    """Run each relation of the contract on its visible sources and their follow-ups."""
    sources = {r.id: _sources(contract, r) for r in contract.relations}
    try:
        tree = change_tree(pack, contract, base, patch, repository)
        with tempfile.TemporaryDirectory(prefix="dokime-relations-") as work:
            project = Path(work) / "project"
            project.mkdir()
            repository.extract(tree, project)
            by_id = {e.id: e for found in sources.values() for e in found}
            feeding = [e for e in contract.examples if e.id in by_id]
            first = _observed(observer, image, project, [_request(e) for e in feeding], limits)
            follow_ups = [
                one
                for relation in contract.relations
                for source in sources[relation.id]
                for one in _follow_ups(relation, source, first, seed, permutations)
            ]
            requests = [
                ExampleRequest(
                    example=f"{one.relation.id}/{one.source.id}/{number}",
                    boundary=Boundary(one.source.boundary),
                    target=one.source.target,
                    inputs=(one.given,),
                )
                for number, one in enumerate(follow_ups)
            ]
            second = _observed(observer, image, project, requests, limits)
    except RefusalError as refusal:
        return RelationsOutcome(GateResult(gate=GATE, findings=(refusal.finding,)), seed, ())
    failed = [
        one
        for number, one in enumerate(follow_ups)
        if not _holds(one, second.get(requests[number].example))
    ]
    return RelationsOutcome(
        GateResult(
            gate=GATE,
            findings=_findings(contract, follow_ups, failed),
            checks=checks_of("derived" for _ in follow_ups),
        ),
        seed,
        tuple(FailedFollowUp(one.relation.id, one.source.id, one.order) for one in failed),
    )


def _sources(contract: Contract, relation: Relation) -> list[Example]:
    return [
        e
        for e in contract.examples
        if (e.requirement, e.target) == (relation.requirement, relation.target)
        and len(e.steps) == 1
    ]


def _observed(
    observer: ExampleObserver,
    image: Digest,
    project: Path,
    requests: list[ExampleRequest],
    limits: ObservationLimits,
) -> dict[str, ExampleObservation]:
    if not requests:
        return {}
    return {o.example: o for o in observer.observe(image, project, tuple(requests), limits)}


def _step(observation: ExampleObservation | None) -> StepObservation | None:
    """The step of an observation of one step, when it was observed to its end."""
    if observation is None or observation.ending is not Ending.COMPLETED or not observation.steps:
        return None
    return observation.steps[0]


def _follow_ups(
    relation: Relation,
    source: Example,
    first: dict[str, ExampleObservation],
    seed: int,
    permutations: int,
) -> list[_FollowUp]:
    observed = _step(first.get(source.id))
    if observed is None:
        return []
    given: dict[str, object] = dict(source.steps[0].input)
    if relation.relation == "idempotent":
        again = repeated(source.boundary, given, observed, relation.over, relation.via)
        return [] if again is None else [_FollowUp(relation, source, None, given, again, observed)]
    over = relation.over or ""
    items = items_of(source.boundary, given, over)
    if items is None:
        return []
    drawn = orders(items, source_seed(seed, relation.id, source.id), permutations)
    return [
        _FollowUp(
            relation, source, order, given, in_order(source.boundary, given, over, order), observed
        )
        for order in drawn
    ]


def _holds(one: _FollowUp, observation: ExampleObservation | None) -> bool:
    follow = _step(observation)
    return follow is not None and holds(
        one.relation,
        one.source.boundary,
        one.observed,
        follow,
        source_given=one.source_given,
        follow_given=one.given,
    )


def _findings(
    contract: Contract, follow_ups: list[_FollowUp], failed: list[_FollowUp]
) -> tuple[Finding, ...]:
    findings = []
    for relation in contract.relations:
        if not any(one.relation.id == relation.id for one in follow_ups):
            message = (
                f"no visible example of the requirement {relation.requirement} at the target of"
                f" the relation {relation.id} gives it a follow-up"
            )
            findings.append(
                Finding(
                    code="relation-without-source",
                    message=message,
                    verdict=Verdict.ASK,
                    lines=(relation.line,),
                )
            )
            continue
        broken = dict.fromkeys(one.source.id for one in failed if one.relation.id == relation.id)
        findings.extend(
            Finding(
                code="relation-fails",
                message=words(relation, example),
                verdict=Verdict.FAIL,
                lines=(relation.line,),
            )
            for example in broken
        )
    return tuple(findings)
