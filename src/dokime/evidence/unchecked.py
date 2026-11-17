"""What was not checked in a run, listed mechanically (ADR-0064)."""

from dokime.evidence.run import Contract, GateRan, Run

_IN_PROCESS = {
    "existing-tests": "the tests run in the process of the code under test, which can change"
    " their outcome",
    "baseline": "the code under test runs in the process that observes it, which it can rewrite",
    "visible-examples": "the code under test runs in the process that observes it, which it can"
    " rewrite",
}
"""The gates that run the code under test in a process it can change, with the reason."""

type Entry = dict[str, object]


def not_checked(run: Run) -> list[Entry]:
    """Every entry of `not_checked`, by code in the order of ADR-0064."""
    ran = [gate for gate in run.gates if isinstance(gate, GateRan)]
    return [
        *_of_contract(run.contract),
        *(
            _entry(
                "test-excluded-unstable",
                gate.gate,
                "the outcome of the test varied between the runs of the base, so it was left out",
                [{"label": "test", "text": test}],
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
    ]


def _of_contract(contract: Contract | None) -> list[Entry]:
    if contract is None:
        return []
    requirements = contract.requirements
    return [
        *(
            _entry("no-holdout", r.id, "there are no sealed examples until block B")
            for r in requirements
        ),
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
