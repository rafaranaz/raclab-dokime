"""The run of `audit` over the ports it is given: the states of the audit flow, their gates, the
ledger and the evidence.

The inputs come from the tree of the base commit, or from files given from outside the patch,
never from the patch. The examples of each side are observed in an image built with the tree of
that side as the context: the base for `baseline`, the tree of the change of ADR-0058 for
`visible-examples`. The run goes through the states of the audit flow of A3 in their order and
stops at the first one whose verdict is not `PASS`, with the gates after it not reached. The
aggregation's own findings are a fault of the harness: they stop the run with no evidence and an
event that says so. A patch that does not apply, a policy that does not read and a story that is
not a name end the audit before the run, since there is nothing to attest or name.
"""

import tempfile
from dataclasses import dataclass
from pathlib import Path

from dokime.contract.model import Contract
from dokime.core.clock import Clock
from dokime.core.findings import Finding
from dokime.core.layout import change_directory
from dokime.core.ledger import Ledger, LedgerStore, head
from dokime.core.observation import ExampleObserver, ObservationLimits
from dokime.core.policy import Policy
from dokime.core.repository import AuditedRepository, CommitName, RefusalError, TreeName
from dokime.core.runtime import Build, BuildLimits, Digest, VerificationRuntime
from dokime.core.verdicts import Verdict
from dokime.evidence import run as evidence
from dokime.evidence.statement import Evidence, build
from dokime.interfaces.inputs import (
    ContractRead,
    PackRead,
    read_contract,
    read_pack,
    read_tree_policy,
)
from dokime.packs.model import Pack
from dokime.verify.aggregate import BUILT, NOT_BUILT, GateEntry, Status, aggregate_state
from dokime.verify.examples import baseline, visible_examples
from dokime.verify.existing import existing_tests
from dokime.verify.protected import protected_paths
from dokime.verify.result import GateResult
from dokime.verify.trees import base_tree, change_tree

STATES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("checking-contract", ("contract",)),
    ("preparing", ("environment",)),
    ("baselining", ("baseline",)),
    (
        "verifying",
        (
            "protected-paths",
            "existing-tests",
            "visible-examples",
            "relations",
            "changed-line-coverage",
            "behaviour-differences",
            "repeatability",
        ),
    ),
    ("sealed", ("sealed-examples",)),
)
"""The states of the audit flow of A3, each with its gates, in their order."""
CONVERTED = frozenset({"gate", "findings", "unstable", "checks"})
"""The fields of the result of a gate of `verify` that the conversion carries."""
_UNSTABLE_TESTS = "existing-tests"
_UNSTABLE_EXAMPLES = "baseline"


@dataclass(frozen=True)
class Ports:
    """The ports of an audit, and the digest of the program that observes the examples."""

    repository: AuditedRepository
    runtime: VerificationRuntime
    observer: ExampleObserver
    probe: Digest


@dataclass(frozen=True)
class Request:
    """What an audit is asked: the base, the patch, the version of the harness and the inputs."""

    base: CommitName
    patch: bytes
    harness: str
    story: str | None = None
    contract: Path | None = None
    pack: Path | None = None


@dataclass(frozen=True)
class Audited:
    """How an audit ended: its verdict, the findings that ended it outside a gate, the gates of
    the run and its evidence, when it has one."""

    verdict: Verdict
    findings: tuple[Finding, ...] = ()
    gates: tuple[evidence.Gate, ...] = ()
    evidence: Evidence | None = None


def convert(entry: GateEntry) -> evidence.Gate:
    """A gate of a state of `verify` in the types of `evidence`."""
    if entry.status is Status.NOT_APPLICABLE or entry.result is None:
        return evidence.GateNotApplicable(entry.gate, entry.reason or "")
    result = entry.result
    if result.unstable and result.gate not in (_UNSTABLE_TESTS, _UNSTABLE_EXAMPLES):
        raise ValueError(
            f"the gate {result.gate!r} lists unstable items, which none but"
            f" {_UNSTABLE_TESTS} and {_UNSTABLE_EXAMPLES} may"
        )
    return evidence.GateRan(
        gate=result.gate,
        verdict=result.verdict,
        findings=result.findings,
        checks=tuple(evidence.Checks(c.origin, c.total) for c in result.checks),
        unstable_tests=result.unstable if result.gate == _UNSTABLE_TESTS else (),
        unstable_examples=result.unstable if result.gate == _UNSTABLE_EXAMPLES else (),
    )


def run_audit(request: Request, ports: Ports, store: LedgerStore, clock: Clock) -> Audited:
    """Audit the change of the request over the ports, recording the run in the store."""
    story = (request.story or "") if request.contract is None else request.contract.parent.name
    try:
        change_directory(story)
    except ValueError:
        return _before(
            _error(
                "not-a-story",
                f"the story {story!r} is not a name: letters and digits in words joined by"
                " hyphens, starting with a letter",
            )
        )
    try:
        tree = ports.repository.compose_with_patch(request.base, request.patch)
    except RefusalError as refusal:
        return _before(refusal.finding)
    with tempfile.TemporaryDirectory(prefix="dokime-audit-") as work:
        root = Path(work) / "base"
        root.mkdir()
        try:
            ports.repository.extract(base_tree(ports.repository, request.base), root)
        except RefusalError as refusal:
            return _before(refusal.finding)
        policy = read_tree_policy(root)
        if policy.policy is None:
            return _before(*policy.findings)
        run = _Run(request, ports, store, Ledger(store, clock), policy.policy, root, Path(work))
        return run.go(story, tree)


class _Run:
    """One run of the audit flow, from `run.started` to `run.finished`."""

    def __init__(
        self,
        request: Request,
        ports: Ports,
        store: LedgerStore,
        ledger: Ledger,
        policy: Policy,
        root: Path,
        work: Path,
    ) -> None:
        self.request, self.ports, self.policy = request, ports, policy
        self.store, self.ledger = store, ledger
        self.root, self.work = root, work
        self.contract: ContractRead | None = None
        self.pack: PackRead | None = None
        self.built: Build | None = None
        self.dockerfile: Path | None = None
        self.observed = False
        self.change_image: Digest | None = None

    def go(self, story: str, tree: TreeName) -> Audited:
        self.ledger.record("run.started", {"base": self.request.base.text, "story": story})
        gates: list[evidence.Gate] = []
        verdict = Verdict.PASS
        stopped: tuple[str, Verdict] | None = None
        for state, names in STATES:
            if stopped is not None:
                gates.extend(_unreached(name, *stopped) for name in names)
                continue
            self.ledger.record("state.entered", {"state": state})
            results = tuple(self._gate(name) for name in names if name in BUILT)
            outcome = aggregate_state(names, results)
            if outcome.findings:
                self.ledger.record(
                    "run.finished",
                    {
                        "verdict": Verdict.ERROR.value,
                        "findings": [f.code for f in outcome.findings],
                    },
                )
                return Audited(verdict=Verdict.ERROR, findings=outcome.findings, gates=tuple(gates))
            gates.extend(convert(entry) for entry in outcome.gates)
            verdict = outcome.verdict
            if verdict is not Verdict.PASS:
                stopped = (state, verdict)
        built = build(self._evidence(story, tree, verdict, tuple(gates)))
        self.ledger.record("evidence.built", {"digest": built.digest})
        self.ledger.record("run.finished", {"verdict": verdict.value})
        return Audited(verdict=verdict, gates=tuple(gates), evidence=built)

    def _gate(self, name: str) -> GateResult:
        self.ledger.record("gate.started", {"gate": name})
        result = self._result(name)
        finished: dict[str, object] = {"gate": name, "verdict": result.verdict.value}
        if name == "visible-examples" and self.change_image is not None:
            finished["image"] = self.change_image.text
        self.ledger.record("gate.finished", finished)
        if result.unstable:
            kind = "tests" if name == _UNSTABLE_TESTS else "examples"
            self.ledger.record("baseline.unstable", {"gate": name, kind: list(result.unstable)})
        return result

    def _result(self, name: str) -> GateResult:
        if name == "contract":
            self.contract = read_contract(
                self.root, story=self.request.story, outside=self.request.contract
            )
            return GateResult(gate=name, findings=self.contract.findings)
        if name == "environment":
            return self._environment()
        contract, pack, image, dockerfile = self._reached()
        repository, base, patch = self.ports.repository, self.request.base, self.request.patch
        limits = ObservationLimits()
        if name == "baseline":
            self.observed = True
            return baseline(
                contract, self.policy, base, image, repository, self.ports.observer, limits
            )
        if name == "protected-paths":
            return protected_paths(pack, contract, base, patch, repository)
        if name == "existing-tests":
            return existing_tests(
                pack,
                contract,
                self.policy,
                base,
                patch,
                dockerfile,
                repository,
                self.ports.runtime,
            )
        if name == "visible-examples":
            try:
                changed = self._image_of_the_change(pack, contract, dockerfile)
            except RefusalError as refusal:
                return GateResult(gate=name, findings=(refusal.finding,))
            return visible_examples(
                pack, contract, base, patch, changed, repository, self.ports.observer, limits
            )
        raise ValueError(f"the gate {name!r} is not one that this version runs")

    def _image_of_the_change(self, pack: Pack, contract: Contract, dockerfile: Path) -> Digest:
        """The image built with the tree of the change of ADR-0058 as the context."""
        repository = self.ports.repository
        tree = change_tree(pack, contract, self.request.base, self.request.patch, repository)
        directory = self.work / "change"
        directory.mkdir()
        repository.extract(tree, directory)
        self.change_image = self.ports.runtime.build(dockerfile, directory, BuildLimits()).image
        return self.change_image

    def _environment(self) -> GateResult:
        self.pack = read_pack(self.root, self.request.pack)
        findings = list(self.pack.findings)
        if self.pack.pack is not None and self.pack.dockerfile is not None:
            self.dockerfile = self.work / "Dockerfile"
            self.dockerfile.write_bytes(self.pack.dockerfile)
            try:
                self.built = self.ports.runtime.build(self.dockerfile, self.root, BuildLimits())
            except RefusalError as refusal:
                findings.append(refusal.finding)
        return GateResult(gate="environment", findings=tuple(findings))

    def _reached(self) -> tuple[Contract, Pack, Digest, Path]:
        """The inputs of the earlier states, which a state after them has, since they passed."""
        contract = self.contract.contract if self.contract else None
        pack = self.pack.pack if self.pack else None
        if contract is None or pack is None or self.built is None or self.dockerfile is None:
            raise ValueError("a gate after the environment runs only when the earlier ones passed")
        return contract, pack, self.built.image, self.dockerfile

    def _evidence(
        self, story: str, tree: TreeName, verdict: Verdict, gates: tuple[evidence.Gate, ...]
    ) -> evidence.Run:
        contract = None
        if self.contract is not None and self.contract.text is not None:
            read = self.contract.contract
            contract = evidence.Contract(
                text=self.contract.text,
                requirements=()
                if read is None
                else tuple(
                    evidence.Requirement(
                        r.id,
                        tuple(e.origin for e in read.examples if e.requirement == r.id),
                    )
                    for r in read.requirements
                ),
            )
        image = None
        if self.built is not None:
            platform = self.built.base.platform if self.built.base else None
            image = evidence.Image(self.built.image, platform)
        return evidence.Run(
            story=story,
            tree=tree,
            patch=self.request.patch,
            verdict=verdict,
            harness=self.request.harness,
            inputs=evidence.Inputs(
                base=self.request.base,
                policy=self.policy,
                image=image,
                pack=self.pack.text if self.pack and self.pack.pack else None,
                probe=self.ports.probe if self.observed else None,
            ),
            gates=gates,
            ledger=head(self.store.lines()),
            contract=contract,
        )


def _unreached(name: str, state: str, verdict: Verdict) -> evidence.Gate:
    if name in NOT_BUILT:
        return evidence.GateNotApplicable(name, NOT_BUILT[name])
    return evidence.GateNotReached(
        name, f"the run stopped at the state {state}, whose verdict is {verdict.value}"
    )


def _before(*findings: Finding) -> Audited:
    return Audited(verdict=Verdict.ERROR, findings=findings)


def _error(code: str, message: str) -> Finding:
    return Finding(code=code, message=message, verdict=Verdict.ERROR)
