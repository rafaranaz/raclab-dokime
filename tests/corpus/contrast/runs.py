"""A stub of the entry of the results of a run of R2."""

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any

VISIBLE = "tests/dokime_visible"
HELD_OUT = "tests/dokime_held_out"
VISIBLE_CHECK = "dokime-visible"
HELD_OUT_CHECK = "held-out"
XFAIL = ""
FAILURES = ("",)


@dataclass(frozen=True)
class Entry:
    key: str


def failed_run(key: str, arm: str, failure: str) -> Entry:
    return Entry(key)


def entry_of(
    key: str,
    arm: str,
    result: Mapping[str, Any],
    observations: Mapping[str, Any],
    held_out: Callable[[str], bool],
) -> Entry:
    return Entry(key)


def in_held_out_conversion(test_id: str) -> bool:
    return False


def turned_green_by(witness: Iterable[str]) -> Callable[[str], bool]:
    return lambda test_id: False


def toml_of(entry: Entry) -> str:
    return ""


def check_command(test: str, paths: Iterable[str]) -> str:
    return test
