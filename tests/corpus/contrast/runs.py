"""What a run of an arm of R2 leaves on the machine where it ran: one entry of the results.

An entry holds the key of the case, the arm, the state and the regression that swarm-verify gave,
how many tests of the visible checks and of the held-out checks passed and did not pass, whether
the rejection comes only from the strict-xfail test of mdformat, and the kind of a failure of the
mount; no id of a test, no path and no log, so that it can leave that machine after review.
"""

import json
import shlex
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, fields
from typing import Any

VISIBLE = "tests/dokime_visible"
"""Where the conversion of the visible examples is laid in the base, for the arm S2."""
HELD_OUT = "tests/dokime_held_out"
"""Where swarm-verify lays the sealed conversion of the held-out examples, for the arm S2."""
VISIBLE_CHECK = "dokime-visible"
HELD_OUT_CHECK = "held-out"

XFAIL = "tests.test_api::test_output_is_equal[```\\na\\n```\\n\\u2003\\n# A\\n]"
"""The test of mdformat that its witness `27e2ba3` takes out of `xfail`, and that the good patch of
the corpus, which holds the fix without the change to the test, makes pass under `xfail_strict`."""

FAILURES = ("", "mount", "helper")
"""The kinds of failure of a run: none, the mount of the local copy, or the helper of Node."""


@dataclass(frozen=True)
class Entry:
    """One run of one arm on one case, as it leaves the machine of the maintainer."""

    key: str
    arm: str
    state: str
    regression: str
    visible_passed: int
    visible_failed: int
    held_out_passed: int
    held_out_failed: int
    xfail_only: bool
    failure: str


def failed_run(key: str, arm: str, failure: str) -> Entry:
    """The entry of a run whose mount or helper failed: its kind, with no message."""
    if failure not in FAILURES[1:]:
        raise ValueError(f"no kind of failure {failure!r}")
    return Entry(key, arm, "", "", 0, 0, 0, 0, False, failure)


def entry_of(
    key: str,
    arm: str,
    result: Mapping[str, Any],
    observations: Mapping[str, Any],
    held_out: Callable[[str], bool],
) -> Entry:
    """The entry of a run from the result of `verify()` and the observations of its evidence;
    `held_out` says which tests of the sealed check count as held out."""
    checks = observations.get("checks", [])
    visible = [
        test
        for check in checks
        if check.get("name") == VISIBLE_CHECK
        for test in check.get("tests", [])
        if str(test["id"]).startswith(_module(VISIBLE))
    ]
    sealed = [test for test in observations.get("sealed") or [] if held_out(str(test["id"]))]
    ran = [test for check in checks for test in check.get("tests", [])]
    ran += list(observations.get("sealed") or [])
    failing = {str(test["id"]) for test in ran if test.get("after") in ("fail", "error")}
    state = str(result.get("state", ""))
    regression = result.get("regression")
    if isinstance(regression, Mapping):
        regression = regression.get("status")
    return Entry(
        key=key,
        arm=arm,
        state=state,
        regression=str(regression or ""),
        visible_passed=_passed(visible),
        visible_failed=len(visible) - _passed(visible),
        held_out_passed=_passed(sealed),
        held_out_failed=len(sealed) - _passed(sealed),
        xfail_only=state != "complete" and failing == {XFAIL},
        failure="",
    )


def in_held_out_conversion(test_id: str) -> bool:
    """Whether a test is one of the sealed conversion of S2."""
    return test_id.startswith(_module(HELD_OUT))


def turned_green_by(witness: Iterable[str]) -> Callable[[str], bool]:
    """Whether a test is one of those that the witness turned green, for S1."""
    chosen = frozenset(witness)
    return lambda test_id: test_id in chosen


def toml_of(entry: Entry) -> str:
    """The entry as a table `[[run]]` of TOML."""
    lines = ["[[run]]"]
    for field in fields(entry):
        value = getattr(entry, field.name)
        text = ("true" if value else "false") if isinstance(value, bool) else json.dumps(value)
        lines.append(f"{field.name} = {text}")
    return "\n".join(lines) + "\n\n"


def check_command(test: str, paths: Iterable[str]) -> str:
    """The command of the tests of an adaptation, on these paths only: its trailing arguments
    that are not options are dropped and the paths put in their place."""
    words = shlex.split(test)
    while words and not words[-1].startswith("-"):
        words.pop()
    return shlex.join([*words, *paths])


def _module(directory: str) -> str:
    return directory.replace("/", ".") + "."


def _passed(tests: list[Mapping[str, Any]]) -> int:
    return sum(1 for test in tests if test.get("after") == "pass")
