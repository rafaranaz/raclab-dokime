"""The gate `existing-tests` (ADR-0017, ADR-0058).

The tests of the pack run on the base as many times as `baseline.runs` of the policy says, and a
test counts as passing in the baseline only when it passed in every run; one whose outcome varied,
or that some run did not report, is left out and listed as unstable. Then they run once on the tree
of the change, the code of the patch with the tests and their configuration of the base except what
the contract authorises. A test that passed in the baseline has to pass there and be there: one
that disappears from a file that the contract authorises asks, since renaming a file and emptying
it cannot be told apart mechanically.

A test is named `<class name>::<name>`, as the report gives it, and belongs to a file when its class
name is the path of the file with `/` as `.` and without `.py`, or starts with that and a `.`; a
test whose file cannot be told this way counts as of no authorised file, the stricter reading.
"""

import tempfile
from collections.abc import Callable
from pathlib import Path

from dokime.contract.model import Contract
from dokime.core.findings import Finding
from dokime.core.outcomes import Outcome, Report
from dokime.core.policy import Policy
from dokime.core.repository import AuditedRepository, CommitName, RefusalError, TreeName
from dokime.core.runtime import VerificationRuntime
from dokime.core.verdicts import Verdict
from dokime.packs.model import Pack
from dokime.packs.testrun import run_tests
from dokime.verify.result import GateResult, checks_of
from dokime.verify.trees import base_tree, change_tree

GATE = "existing-tests"


class _RunError(Exception):
    """A run of the tests ended with a finding."""

    def __init__(self, finding: Finding) -> None:
        super().__init__(finding.message)
        self.finding = finding


def existing_tests(
    pack: Pack,
    contract: Contract,
    policy: Policy,
    base: CommitName,
    patch: bytes,
    dockerfile: Path,
    repository: AuditedRepository,
    runtime: VerificationRuntime,
) -> GateResult:
    """Check that every test that passed in every run of the base still passes with the change."""
    try:
        with tempfile.TemporaryDirectory(prefix="dokime-tests-") as work:
            room = _Room(Path(work), pack, dockerfile, repository, runtime)
            baseline = room.run(lambda: base_tree(repository, base), policy.baseline_runs)
            (changed,) = room.run(lambda: change_tree(pack, contract, base, patch, repository), 1)
    except (RefusalError, _RunError) as error:
        return GateResult(gate=GATE, findings=(error.finding,))
    names = sorted(set().union(*baseline))
    unstable = tuple(name for name in names if len({run.get(name) for run in baseline}) > 1)
    passed = [n for n in names if n not in unstable and baseline[0][n] is Outcome.PASSED]
    findings = []
    for name in passed:
        if name not in changed:
            if any(_of_file(name, path) for path in contract.may_modify_tests):
                code, verdict = "authorised-test-disappears", Verdict.ASK
            else:
                code, verdict = "existing-test-disappears", Verdict.FAIL
            findings.append(_finding(code, verdict, name, "disappeared"))
        elif changed[name] is not Outcome.PASSED:
            what = f"is {changed[name].value}"
            findings.append(_finding("existing-test-fails", Verdict.FAIL, name, what))
    checks = checks_of("existing" for _ in passed)
    return GateResult(gate=GATE, findings=tuple(findings), unstable=unstable, checks=checks)


class _Room:
    """Where the trees are extracted and the tests run, each run with an output of its own."""

    def __init__(
        self,
        work: Path,
        pack: Pack,
        dockerfile: Path,
        repository: AuditedRepository,
        runtime: VerificationRuntime,
    ) -> None:
        self.work, self.pack, self.dockerfile = work, pack, dockerfile
        self.repository, self.runtime = repository, runtime
        self.count = 0

    def _directory(self) -> Path:
        self.count += 1
        directory = self.work / str(self.count)
        directory.mkdir()
        return directory

    def run(self, tree: Callable[[], TreeName], times: int) -> list[Report]:
        """Extract the tree once and run the tests on it `times` times."""
        project = self._directory()
        self.repository.extract(tree(), project)
        reports = []
        for _ in range(times):
            done = run_tests(self.pack, self.dockerfile, project, self._directory(), self.runtime)
            if done.finding is not None:
                raise _RunError(done.finding)
            if done.report is None:
                raise RuntimeError("a test run without a finding gives its report")
            reports.append(done.report)
        return reports


def _of_file(name: str, path: str) -> bool:
    module = path.removesuffix(".py").replace("/", ".")
    classname = name.split("::", 1)[0]
    return classname == module or classname.startswith(module + ".")


def _finding(code: str, verdict: Verdict, name: str, what: str) -> Finding:
    return Finding(
        code=code,
        message=f"the test {name} passed in every run of the base and {what} with the change",
        verdict=verdict,
    )
