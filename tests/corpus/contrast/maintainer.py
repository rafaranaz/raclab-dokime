"""A stub of the command of the runs of R2: it opens nothing and runs nothing."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tests.corpus.cases import ACTIVE, Case
from tests.corpus.contrast.runs import Entry

ARMS: tuple[str, ...] = ()
HELPER = ("node",)
AUTHOR: dict[str, str] = {}


@dataclass(frozen=True)
class Spec:
    key: str
    origin: str
    base: str
    patch: bytes
    adaptation: Mapping[str, Any]
    contract: str
    sealed: Path | None
    witness: str
    turned_green: tuple[str, ...]
    pack_paths: tuple[str, ...]


def specs(clones: Path | None = None, cases: Sequence[Case] = ACTIVE) -> list[Spec]:
    return []


def run_arm(
    spec: Spec,
    arm: str,
    opener: Callable[[bytes], bytes],
    out: Path,
    helper: Sequence[str] = HELPER,
) -> Entry:
    return Entry(spec.key)


def main(
    argv: Sequence[str],
    environ: Mapping[str, str] = {},
    passphrase: Callable[[], str] = lambda: "",
    helper: Sequence[str] = HELPER,
) -> int:
    return 0
