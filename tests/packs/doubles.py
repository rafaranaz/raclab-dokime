"""Doubles of the two ports, so that the loop of the self-check is tested with no git and no engine.

A project is a list of commits, each with its files. A test file says which code it expects, as
`expects:<text>`, and the runtime gives a test as passed when `src/code.py` holds that text and as
failed otherwise. A directory may also hold a file `ending` that makes the run end in that way.
"""

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from dokime.core.outcomes import Outcome, Report, ReportLimits
from dokime.core.repository import (
    Change,
    CommitName,
    HistoryCommit,
    RefusalError,
    RepoPath,
    TreeName,
)
from dokime.core.runtime import (
    BaseImage,
    Build,
    BuildLimits,
    Digest,
    Ending,
    RunLimits,
    RunResult,
)
from dokime.packs.check import check
from dokime.packs.model import Pack
from tests.packs.packs import VALID

BASE = BaseImage(platform=Digest(f"sha256:{'b' * 64}"))
CODE = "src/code.py"

Files = dict[str, bytes]


def pack() -> Pack:
    checked = check(VALID)
    assert checked.pack is not None
    return checked.pack


def name_of(text: str) -> str:
    return hashlib.sha1(text.encode(), usedforsecurity=False).hexdigest()


@dataclass
class FakeRepository:
    """A project repository held in memory. `refuse` names an operation that is refused."""

    commits: dict[CommitName, tuple[int, tuple[CommitName, ...], Files]] = field(
        default_factory=dict
    )
    trees: dict[TreeName, Files] = field(default_factory=dict)
    refuse: str = ""
    calls: list[str] = field(default_factory=list)
    extracted: list[Path] = field(default_factory=list)

    def add(self, label: str, date: int, files: Files, *parents: CommitName) -> CommitName:
        name = CommitName(name_of(label))
        self.commits[name] = (date, parents, dict(files))
        return name

    def _refused(self, operation: str) -> None:
        self.calls.append(operation)
        if self.refuse == operation:
            raise RefusalError("unknown-commit", f"the double refuses {operation}")

    def history(self, start: CommitName) -> tuple[HistoryCommit, ...]:
        self._refused("history")
        seen: dict[CommitName, HistoryCommit] = {}
        waiting = [start]
        while waiting:
            name = waiting.pop()
            if name in seen:
                continue
            date, parents, _ = self.commits[name]
            seen[name] = HistoryCommit(name=name, date=date, parents=parents)
            waiting.extend(parents)
        return tuple(seen.values())

    def change(self, commit: CommitName) -> Change:
        self._refused("change")
        _, parents, files = self.commits[commit]
        before = self.commits[parents[0]][2]
        paths = sorted(p for p in set(files) | set(before) if files.get(p) != before.get(p))
        return Change(commit=commit, parent=parents[0], paths=tuple(RepoPath(p) for p in paths))

    def compose_with_paths(
        self, base: CommitName, source: CommitName, take: Callable[[RepoPath], bool]
    ) -> TreeName:
        self._refused("compose")
        kept = {p: d for p, d in self.commits[base][2].items() if not take(RepoPath(p))}
        taken = {p: d for p, d in self.commits[source][2].items() if take(RepoPath(p))}
        files = kept | taken
        tree = TreeName(name_of(json.dumps(sorted((p, d.hex()) for p, d in files.items()))))
        self.trees[tree] = files
        return tree

    def compose_with_patch(self, base: CommitName, patch: bytes) -> TreeName:
        raise RefusalError("patch-not-supported", "the double composes no patch")

    def extract(self, tree: TreeName, directory: Path) -> None:
        self._refused("extract")
        assert directory.is_dir()
        assert not any(directory.iterdir())
        self.extracted.append(directory)
        for path, data in self.trees[tree].items():
            target = directory / PurePosixPath(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)


@dataclass
class FakeRuntime:
    """A runtime that runs nothing. `refuse` names an operation that is refused."""

    refuse: str = ""
    builds: list[tuple[str, Path, BuildLimits]] = field(default_factory=list)
    runs: list[tuple[Digest, tuple[str, ...], Path, Path, RunLimits]] = field(default_factory=list)
    readings: list[tuple[Path, PurePosixPath, ReportLimits]] = field(default_factory=list)
    while_running: Callable[[Path, Path], None] = lambda project, output: None

    def build(self, dockerfile: Path, directory: Path, limits: BuildLimits) -> Build:
        if self.refuse == "build":
            raise RefusalError("build-failed", "the double refuses to build")
        text = dockerfile.read_text()
        self.builds.append((text, directory, limits))
        listing = sorted(str(p.relative_to(directory)) for p in directory.rglob("*"))
        image = Digest("sha256:" + hashlib.sha256(f"{text}{listing}".encode()).hexdigest())
        return Build(image=image, base=BASE)

    def run(
        self,
        image: Digest,
        command: tuple[str, ...],
        project: Path,
        output: Path,
        limits: RunLimits,
    ) -> RunResult:
        if self.refuse == "run":
            raise RefusalError("podman-failed", "the double refuses to run")
        assert output.is_dir()
        assert not any(output.iterdir())
        self.runs.append((image, command, project, output, limits))
        self.while_running(project, output)
        ending = project / "ending"
        if ending.exists():
            return RunResult(ending=Ending(ending.read_text().strip()), exit_code=None)
        code = (project / CODE).read_bytes() if (project / CODE).exists() else b""
        report = {
            str(path.relative_to(project)): (
                Outcome.PASSED if path.read_bytes() == b"expects:" + code else Outcome.FAILED
            )
            for path in sorted((project / "tests").rglob("test_*.py"))
        }
        (output / "report.xml").write_text(json.dumps(report))
        failed = any(outcome is Outcome.FAILED for outcome in report.values())
        return RunResult(ending=Ending.EXITED, exit_code=1 if failed else 0)

    def read_report(self, output: Path, report: PurePosixPath, limits: ReportLimits) -> Report:
        if self.refuse == "read":
            raise RefusalError("report-unreadable", "the double refuses to read")
        self.readings.append((output, report, limits))
        return {
            name: Outcome(value)
            for name, value in json.loads((output / report).read_text()).items()
        }


def fixing_commit(
    repository: FakeRepository, parent: CommitName, label: str, date: int
) -> CommitName:
    """A commit that changes the code and its test together: a witness."""
    files = dict(repository.commits[parent][2])
    files[CODE] = label.encode()
    files[f"tests/test_{label}.py"] = b"expects:" + label.encode()
    for path in list(files):
        if path.startswith("tests/") and path != f"tests/test_{label}.py":
            files[path] = b"expects:" + label.encode()
    return repository.add(label, date, files, parent)
