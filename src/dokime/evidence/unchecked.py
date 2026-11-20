"""What was not checked in a run, listed mechanically (ADR-0064, ADR-0075).

A case of a sealed run that holds out nothing is listed with its motive, and so is each limit of
the detection of what was published; a run without a hold-out lists neither, since its gate
`sealed-examples` already says that nothing of the hold-out was checked.
"""

from dokime.evidence.run import Contract, GateRan, Holdout, Run
from dokime.evidence.schema import QUOTED, SEALED, cut

_IN_PROCESS = {
    "existing-tests": "the tests run in the process of the code under test, which can change"
    " their outcome",
    "baseline": "the code under test runs in the process that observes it, which it can rewrite",
    "visible-examples": "the code under test runs in the process that observes it, which it can"
    " rewrite",
}
"""The gates that run the code under test in a process it can change, with the reason."""
_MOTIVES = {
    "single-example": "the case has a single example",
    "all-published": "every example of the case was published before the seal",
}
"""The reason of a case that holds out nothing, by its motive."""
LIMITS = (
    "the content of an example is compared as YAML reads it, so one published with a field added or"
    " a value spelt otherwise is not recognised",
    "a version of the contract under an earlier path, after a rename, is not read",
    "a commit that only other refs reach is not read",
    "a copy of an example in another file is not looked for",
    "the history is read up to the base of the pull request, so a held-out example published in a"
    " commit of the pull request and taken back in another is not seen by this audit: where the"
    " project merges keeping the commits, by rebase or by a merge commit, the next audit sees it,"
    " and with a squash merge no audit does",
)
"""The limits of the detection of a held-out example already published, in the order of
ADR-0075."""

type Entry = dict[str, object]


def not_checked(run: Run) -> list[Entry]:
    """Every entry of `not_checked`, by code in the order of ADR-0064."""
    ran = [gate for gate in run.gates if isinstance(gate, GateRan)]
    holdout = next((g.holdout for g in ran if g.gate == SEALED and g.holdout is not None), None)
    return [
        *_of_holdout(holdout),
        *_of_contract(run.contract),
        *(
            _entry(
                "test-excluded-unstable",
                gate.gate,
                "the outcome of the test varied between the runs of the base, so it was left out",
                [{"label": "test", "text": cut(test, QUOTED)}],
            )
            for gate in ran
            for test in gate.unstable_tests
        ),
        *(
            _entry(
                "example-unstable",
                example,
                f"whether the example holds varied between the runs of the base in {gate.gate}",
            )
            for gate in ran
            for example in gate.unstable_examples
        ),
        *(
            _entry("outside-threat-model", gate.gate, _IN_PROCESS[gate.gate])
            for gate in ran
            if gate.gate in _IN_PROCESS
        ),
        *(
            _entry("best-effort-secrecy", SEALED, limit)
            for limit in (LIMITS if holdout is not None else ())
        ),
    ]


def _of_holdout(holdout: Holdout | None) -> list[Entry]:
    if holdout is None:
        return []
    return [
        {
            "code": "case-without-holdout",
            "what": case.requirement,
            "case": case.case,
            "reason": _MOTIVES[case.motive],
        }
        for case in holdout.without_holdout
    ]


def _of_contract(contract: Contract | None) -> list[Entry]:
    if contract is None:
        return []
    requirements = contract.requirements
    return [
        *(
            _entry("requirement-without-example", r.id, "the requirement has no example")
            for r in requirements
            if not r.origins
        ),
        *(
            _entry(
                "only-model-checks",
                r.id,
                "every example of the requirement is of origin model, which no person stands"
                " behind",
            )
            for r in requirements
            if r.origins and all(origin == "model" for origin in r.origins)
        ),
    ]


def _entry(code: str, what: str, reason: str, untrusted: list[Entry] | None = None) -> Entry:
    entry: Entry = {"code": code, "what": what, "reason": reason}
    if untrusted:
        entry["untrusted"] = untrusted
    return entry
