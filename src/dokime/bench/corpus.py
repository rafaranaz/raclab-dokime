"""The data of the corpus that `bench` reads from the repository: the cases with their labels, the
pending and withdrawn ones, the witnesses, the blind reading of B3a and the runs with the key."""

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dokime.bench.results import BenchError, Result

GOOD = "good"
HELD_OUT = "fails-a-held-out-example"
NOT_ISOLATED = frozenset({"not-isolated", "undecidable"})
_LABEL = re.compile(r"(W\d\d) \| (isolated|not-isolated|undecidable) \| ([-1-4]) \|")


@dataclass(frozen=True)
class Case:
    """A case of the corpus: its key, its label, and the commit of its witness when it is good."""

    key: str
    label: str
    witness: str | None = None


@dataclass(frozen=True)
class Withdrawn:
    """A withdrawn case, with what its first run gave."""

    key: str
    label: str
    first_run: Result
    key_given: bool


@dataclass(frozen=True)
class Corpus:
    """What `bench` needs of the corpus."""

    cases: dict[str, Case]
    pending: frozenset[str]
    withdrawn: tuple[Withdrawn, ...]
    not_isolated: frozenset[str]
    """The commits of the witnesses that the blind reading labels not isolated."""
    with_the_key: dict[str, Result]
    """The last result with the key of each case that a run with the key audited."""

    @property
    def runnable(self) -> dict[str, Case]:
        """The cases that the audit of the corpus runs: neither pending nor withdrawn."""
        out = self.pending | {w.key for w in self.withdrawn}
        return {k: c for k, c in self.cases.items() if k not in out}

    @property
    def excluded(self) -> frozenset[str]:
        """The good cases whose witness the blind reading labels not isolated (BENCH-012)."""
        return frozenset(
            k
            for k, c in self.runnable.items()
            if c.label == GOOD and c.witness in self.not_isolated
        )


def _toml(path: Path) -> dict[str, Any]:
    try:
        return tomllib.loads(path.read_text())
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise BenchError(f"{path}: cannot be read: {error}") from None


def _cases(directory: Path, witnesses: dict[str, str]) -> dict[str, Case]:
    cases: dict[str, Case] = {}
    for found in sorted(directory.glob("*/cases/*/case.toml")):
        key = f"{found.parent.parent.parent.name}/{found.parent.name}"
        label = str(_toml(found)["label"])
        cases[key] = Case(key, label, witnesses.get(key) if label == GOOD else None)
    if not cases:
        raise BenchError(f"{directory}: holds no case")
    return cases


def _not_isolated(blind: Path) -> frozenset[str]:
    """The commits of the witnesses that either reader labels, last, not isolated or undecidable."""
    commits = {w["id"]: str(w["commit"]) for w in _toml(blind / "draw.toml")["witness"]}
    found: set[str] = set()
    for reader in ("A", "B"):
        last: dict[str, str] = {}
        for answer in sorted((blind / "answers").glob(f"{reader}-*.txt")):
            for witness, label, _ in _LABEL.findall(answer.read_text()):
                last[witness] = label
        found |= {commits[w] for w, label in last.items() if label in NOT_ISOLATED}
    return frozenset(found)


def read_corpus(directory: Path) -> Corpus:
    """Read the data of the corpus under its directory, `tests/corpus` in this repository."""
    witnesses = {
        f"{w['project']}/{w['case']}": str(w["commit"])
        for w in _toml(directory / "witnesses.toml")["witness"]
    }
    cases = _cases(directory, witnesses)
    withdrawn = tuple(
        Withdrawn(
            str(e["key"]),
            cases[str(e["key"])].label,
            Result(str(e["key"]), str(e["verdict"]), e["failing_gate"] or None),
            bool(e["key_given"]),
        )
        for e in _toml(directory / "withdrawn.toml").get("withdrawn", [])
    )
    with_the_key: dict[str, Result] = {}
    for run in _toml(directory / "held-out-run.toml").get("run", []):
        for case in run["case"]:
            key = str(case["key"])
            with_the_key[key] = Result(key, str(case["verdict"]), case["failing_gate"] or None)
    return Corpus(
        cases=cases,
        pending=frozenset(_toml(directory / "pending.toml")["pending"]),
        withdrawn=withdrawn,
        not_isolated=_not_isolated(directory / "blind"),
        with_the_key=with_the_key,
    )
