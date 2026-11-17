"""The audit of a change by `existing-tests` on the doubles, which its tests share."""

import json
from pathlib import Path

from dokime.core.findings import Finding
from dokime.core.policy import Policy
from dokime.core.verdicts import Verdict
from dokime.verify.existing import existing_tests
from dokime.verify.result import GateResult
from tests.verify.doubles import AuditedDouble, Files, RuntimeDouble, patch
from tests.verify.gates import PACK, codes, contract

PASSED, FAILED, SKIPPED = "passed", "failed", "skipped"
A, B = "tests.test_a::test_one", "tests.test_a.Group::test_two"


def outcomes(*reports: dict[str, str] | str) -> str:
    return json.dumps(reports[0] if reports == ("killed",) else list(reports))


def audit(
    base_runs: tuple[dict[str, str], ...] | str,
    change_run: dict[str, str] | str,
    *,
    runs: int = 2,
    authorised: tuple[str, ...] = (),
    files: Files | None = None,
    changed: bytes | None = None,
) -> tuple[GateResult, RuntimeDouble]:
    repository, runtime = AuditedDouble(), RuntimeDouble()
    given = outcomes(base_runs) if isinstance(base_runs, str) else outcomes(*base_runs)
    base = repository.add({"outcomes.json": given.encode(), "src/p.py": b"code", **(files or {})})
    if changed is None:
        after = outcomes(change_run)
        changed = patch({"outcomes.json": after, "src/p.py": "new"})
    result = existing_tests(
        PACK,
        contract(authorised=authorised),
        Policy(baseline_runs=runs),
        base,
        changed,
        Path("Dockerfile"),
        repository,
        runtime,
    )
    assert result.gate == "existing-tests"
    return result, runtime


def found(result: GateResult) -> list[tuple[str, Verdict]]:
    return codes(list(result.findings))


def named(findings: tuple[Finding, ...]) -> list[str]:
    return [f.message.split(" ", 2)[1] for f in findings]
