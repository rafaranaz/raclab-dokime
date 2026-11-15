"""The loop of the self-check of a pack, over the ports that the caller gives.

The history is ordered by the rule of ADR-0044 and each candidate is run on two sides: the tree of
its parent with the test paths taken from the commit, and the tree of the commit. The second
witness ends the loop, and so does a finding with the verdict `ERROR`, which nothing found later
could change. Each side is extracted into a temporary directory of its own, removed after it runs
and on SIGINT or SIGTERM.
"""

import contextlib
import signal
import tempfile
import threading
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from types import FrameType

from dokime.core.findings import Finding, summarise
from dokime.core.outcomes import Report
from dokime.core.repository import (
    CommitName,
    ProjectRepository,
    RefusalError,
    RepoPath,
    TreeName,
)
from dokime.core.runtime import BaseImage, Digest, VerificationRuntime
from dokime.core.verdicts import Verdict
from dokime.packs.model import Pack
from dokime.packs.order import order_history
from dokime.packs.selfcheck import (
    CANDIDATES_LOOKED_AT,
    WITNESSES_NEEDED,
    is_candidate,
    is_witness,
    self_check,
    turned_green,
)
from dokime.packs.testrun import run_tests


@dataclass(frozen=True)
class Program:
    """A program that runs a port, as the caller names it."""

    name: str
    path: str
    version: str


@dataclass(frozen=True)
class Side:
    """One side of a candidate: the tree that was composed and the image built from it."""

    tree: TreeName
    image: Digest
    base: BaseImage | None


@dataclass(frozen=True)
class Candidate:
    """A candidate that was looked at, with its two sides and what they proved."""

    commit: CommitName
    parent_side: Side
    commit_side: Side
    witness: bool
    turned_green: tuple[str, ...]


@dataclass(frozen=True)
class SelfCheckResult:
    """The result of a self-check: what was looked at, the findings and the programs that ran."""

    candidates: tuple[Candidate, ...]
    findings: tuple[Finding, ...]
    programs: tuple[Program, ...]

    @property
    def verdict(self) -> Verdict:
        """The verdict that the findings give: `PASS` when there are none."""
        return summarise(self.findings)


class _TerminatedError(BaseException):
    """SIGTERM reached the harness while the self-check was going on."""


def _raise_terminated(_signal: int, _frame: FrameType | None) -> None:
    raise _TerminatedError


@contextlib.contextmanager
def _sigterm_raises() -> Iterator[None]:
    """Turn SIGTERM into an exception while the self-check lasts, so that the directories of the
    side are removed; on the way out, SIGTERM is raised again with the previous handler.

    Only the main thread receives signals; elsewhere nothing changes.
    """
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    previous = signal.signal(signal.SIGTERM, _raise_terminated)
    try:
        yield
    except _TerminatedError:
        signal.signal(signal.SIGTERM, previous)
        signal.raise_signal(signal.SIGTERM)
        raise
    finally:
        signal.signal(signal.SIGTERM, previous)


class _EndedError(Exception):
    """A finding with the verdict `ERROR` ended the self-check."""

    def __init__(self, finding: Finding) -> None:
        super().__init__(finding.message)
        self.finding = finding


def _side(
    pack: Pack,
    dockerfile: Path,
    tree: TreeName,
    repository: ProjectRepository,
    runtime: VerificationRuntime,
) -> tuple[Side, Report]:
    """Extract a tree and run the tests of the pack on it, in directories removed afterwards."""
    with tempfile.TemporaryDirectory(prefix="dokime-side-") as work:
        directory, output = Path(work) / "tree", Path(work) / "out"
        directory.mkdir()
        output.mkdir()
        repository.extract(tree, directory)
        run = run_tests(pack, dockerfile, directory, output, runtime)
    if run.finding is not None:
        raise _EndedError(run.finding)
    if run.build is None or run.report is None:
        raise RuntimeError("a test run without a finding gives its image and its report")
    return Side(tree=tree, image=run.build.image, base=run.build.base), run.report


def _candidates(
    pack: Pack,
    dockerfile: Path,
    start: CommitName,
    repository: ProjectRepository,
    runtime: VerificationRuntime,
) -> Iterator[Candidate]:
    def is_test(path: RepoPath) -> bool:
        return pack.is_test(path.text)

    for commit in order_history(repository.history(start)):
        change = repository.change(commit.name)
        if not is_candidate(pack, [path.text for path in change.paths]):
            continue
        parent_tree = repository.compose_with_paths(change.parent, commit.name, is_test)
        commit_tree = repository.compose_with_paths(commit.name, commit.name, lambda _: True)
        parent_side, parent_report = _side(pack, dockerfile, parent_tree, repository, runtime)
        commit_side, commit_report = _side(pack, dockerfile, commit_tree, repository, runtime)
        green = turned_green(parent_report, commit_report)
        yield Candidate(
            commit=commit.name,
            parent_side=parent_side,
            commit_side=commit_side,
            witness=is_witness(parent_report, commit_report),
            turned_green=green if is_witness(parent_report, commit_report) else (),
        )


def run_self_check(
    pack: Pack,
    dockerfile: Path,
    start: CommitName,
    repository: ProjectRepository,
    runtime: VerificationRuntime,
    programs: tuple[Program, ...],
    on_candidate: Callable[[Candidate], None] = lambda _: None,
) -> SelfCheckResult:
    """Self-check a pack from a commit, with the Dockerfile read once from the working copy.

    `on_candidate` receives each candidate as soon as it has been looked at.
    """
    looked: list[Candidate] = []
    with _sigterm_raises(), tempfile.TemporaryDirectory(prefix="dokime-pack-") as work:
        copy = Path(work) / "Dockerfile"
        copy.write_bytes(dockerfile.read_bytes())
        try:
            for candidate in _candidates(pack, copy, start, repository, runtime):
                looked.append(candidate)
                on_candidate(candidate)
                witnesses = sum(c.witness for c in looked)
                if witnesses == WITNESSES_NEEDED or len(looked) == CANDIDATES_LOOKED_AT:
                    break
        except _EndedError as ended:
            return SelfCheckResult(tuple(looked), (ended.finding,), programs)
        except RefusalError as refusal:
            return SelfCheckResult(tuple(looked), (refusal.finding,), programs)
    findings = self_check([c.witness for c in looked])
    return SelfCheckResult(tuple(looked), findings, programs)
