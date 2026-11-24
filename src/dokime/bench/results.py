"""The files of results that a run of the corpus writes, one line of JSON for each case."""

import json
from dataclasses import dataclass
from pathlib import Path


class BenchError(Exception):
    """What stops `bench`: a file of results or data of the corpus that it cannot use."""


@dataclass(frozen=True)
class Result:
    """What the audit of one case gave in a run."""

    key: str
    verdict: str
    failing_gate: str | None


@dataclass(frozen=True)
class Run:
    """A run of the corpus: its commit, whether it had the key, and the result of each case."""

    commit: str
    key_given: bool
    results: dict[str, Result]


def read_run(path: Path) -> Run:
    """Read a file of results, refusing one whose lines differ in their commit or in the key."""
    commits: set[str] = set()
    keys_given: set[bool] = set()
    results: dict[str, Result] = {}
    for number, text in enumerate(path.read_text().splitlines(), start=1):
        if not text.strip():
            continue
        try:
            line = json.loads(text)
            result = Result(str(line["key"]), str(line["verdict"]), line["failing_gate"])
            commits.add(str(line["commit"]))
            keys_given.add(bool(line["key_given"]))
        except (ValueError, KeyError, TypeError) as error:
            raise BenchError(f"{path}: line {number} cannot be read: {error}") from None
        if result.key in results:
            raise BenchError(f"{path}: the case {result.key} has more than one line")
        results[result.key] = result
    if not results:
        raise BenchError(f"{path}: the file holds no result")
    if len(commits) > 1:
        raise BenchError(f"{path}: its lines give more than one commit: {sorted(commits)}")
    if len(keys_given) > 1:
        raise BenchError(f"{path}: its lines differ in whether the key was given")
    return Run(commits.pop(), keys_given.pop(), results)
