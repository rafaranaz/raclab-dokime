"""A double of the port of the audited repository, held in memory, for the tests of verify.

A file is its bytes, an executable file `("x", bytes)` and a link `("->", target)`. A patch is the
JSON of the files it sets and the paths it removes, since the double reads no patch of git.
"""

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from dokime.core.observation import (
    ExampleObservation,
    ExampleRequest,
    ObservationLimits,
    Raised,
    Returned,
)
from dokime.core.outcomes import Outcome, Report, ReportLimits
from dokime.core.repository import (
    Change,
    CommitName,
    HistoryCommit,
    RefusalError,
    RepoPath,
    TreeName,
)
from dokime.core.runtime import Build, BuildLimits, Digest, Ending, RunLimits, RunResult

Entry = bytes | tuple[str, bytes] | tuple[str, str]
Files = dict[str, Entry]


def _name(files: Files) -> str:
    text = json.dumps(sorted((path, repr(entry)) for path, entry in files.items()))
    return hashlib.sha1(text.encode(), usedforsecurity=False).hexdigest()


def patch(
    sets: dict[str, str | tuple[str, str]] | None = None, removes: list[str] | None = None
) -> bytes:
    """The patch of the double: the files it sets, as texts, and the paths it removes."""
    return json.dumps({"set": sets or {}, "remove": removes or []}).encode()


@dataclass
class AuditedDouble:
    """The audited repository in memory."""

    commits: dict[CommitName, Files] = field(default_factory=dict)
    trees: dict[TreeName, Files] = field(default_factory=dict)

    def add(self, files: Files) -> CommitName:
        name = CommitName(_name(files))
        self.commits[name] = dict(files)
        return name

    def _known(self, commit: CommitName) -> None:
        if commit not in self.commits:
            raise RefusalError("commit-missing", f"the commit {commit} is not in the repository")

    def _tree(self, files: Files) -> TreeName:
        name = TreeName(_name({**files, "\0tree": b""}))
        self.trees[name] = dict(files)
        return name

    def history(self, start: CommitName) -> tuple[HistoryCommit, ...]:
        raise NotImplementedError

    def change(self, commit: CommitName) -> Change:
        raise NotImplementedError

    def compose_with_paths(
        self, base: CommitName, source: CommitName, take: Callable[[RepoPath], bool]
    ) -> TreeName:
        self._known(base)
        self._known(source)
        kept = {p: e for p, e in self.commits[base].items() if not take(RepoPath(p))}
        taken = {p: e for p, e in self.commits[source].items() if take(RepoPath(p))}
        return self._tree(kept | taken)

    def compose_with_patch(self, base: CommitName, patch: bytes) -> TreeName:
        self._known(base)
        given = json.loads(patch)
        files = dict(self.commits[base])
        for path in given["remove"]:
            if path not in files:
                raise RefusalError("patch-does-not-apply", f"{path} is not in the base")
            del files[path]
        for path, entry in given["set"].items():
            files[path] = tuple(entry) if isinstance(entry, list) else entry.encode()
        return self._tree(files)

    def compose_tree_with_paths(
        self, tree: TreeName, source: CommitName, take: Callable[[RepoPath], bool]
    ) -> TreeName:
        kept = {p: e for p, e in self.trees[tree].items() if not take(RepoPath(p))}
        taken = {p: e for p, e in self.commits[source].items() if take(RepoPath(p))}
        return self._tree(kept | taken)

    def extract(self, tree: TreeName, directory: Path) -> None:
        for path, entry in self.trees[tree].items():
            target = directory / PurePosixPath(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(entry, tuple) and entry[0] == "->":
                target.symlink_to(str(entry[1]))
            elif isinstance(entry, tuple):
                target.write_bytes(entry[1] if isinstance(entry[1], bytes) else entry[1].encode())
                target.chmod(0o755)
            else:
                target.write_bytes(entry)


@dataclass
class ObserverDouble:
    """The port that observes, in memory: each example returns what `answers.json` of the project
    says, a mapping from the example to the value, or a list of them, one for each call in turn; an
    example it does not name raises."""

    calls: list[tuple[dict[str, str], tuple[ExampleRequest, ...]]] = field(default_factory=list)
    refusal: RefusalError | None = None

    def observe(
        self,
        image: Digest,
        project: Path,
        requests: tuple[ExampleRequest, ...],
        limits: ObservationLimits,
    ) -> tuple[ExampleObservation, ...]:
        files = {
            p.relative_to(project).as_posix(): p.read_text()
            for p in sorted(project.rglob("*"))
            if p.is_file()
        }
        self.calls.append((files, requests))
        if self.refusal is not None:
            raise self.refusal
        given = json.loads(files.get("answers.json", "{}"))
        answers = given[(len(self.calls) - 1) % len(given)] if isinstance(given, list) else given
        return tuple(
            ExampleObservation(
                example=request.example,
                steps=tuple(
                    Returned(value=answers[request.example])
                    if request.example in answers
                    else Raised(
                        type="KeyError",
                        qualified="builtins.KeyError",
                        classes=("builtins.KeyError", "builtins.Exception", "builtins.object"),
                        message=request.example,
                    )
                    for _ in request.inputs
                ),
            )
            for request in requests
        )


@dataclass
class RuntimeDouble:
    """The runtime of the tests, in memory: a run of a project gives the next report of the list in
    its `outcomes.json`, by the number of runs of that project, and a project whose list says
    `"killed"` ends at the time limit."""

    runs: list[dict[str, str]] = field(default_factory=list)
    _counts: dict[str, int] = field(default_factory=dict)
    _reports: dict[Path, Report] = field(default_factory=dict)

    def build(self, dockerfile: Path, directory: Path, limits: BuildLimits) -> Build:
        return Build(image=Digest("sha256:" + "b" * 64), base=None)

    def run(
        self,
        image: Digest,
        command: tuple[str, ...],
        project: Path,
        output: Path,
        limits: RunLimits,
    ) -> RunResult:
        files = {
            p.relative_to(project).as_posix(): p.read_text()
            for p in sorted(project.rglob("*"))
            if p.is_file()
        }
        self.runs.append(files)
        given = json.loads(files["outcomes.json"])
        if given == "killed":
            return RunResult(ending=Ending.TIME_LIMIT, exit_code=None)
        key = json.dumps(files, sort_keys=True)
        count = self._counts.get(key, 0)
        self._counts[key] = count + 1
        report = given[count % len(given)]
        self._reports[output] = {name: Outcome(value) for name, value in report.items()}
        return RunResult(ending=Ending.EXITED, exit_code=1)

    def read_report(self, output: Path, report: PurePosixPath, limits: ReportLimits) -> Report:
        return self._reports[output]
