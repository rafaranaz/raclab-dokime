"""What a run of an arm of R2 leaves on the machine where it ran: one entry of the results.

An entry holds the key of the case, the arm, the state and the regression that swarm-verify gave,
how many tests of the visible checks and of the held-out checks passed and did not pass, whether
the rejection comes only from the strict-xfail test of mdformat, and the kind of a failure of the
mount; no id of a test, no path and no log, so that it can leave that machine after review.
"""

import json
import shlex
from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass, fields
from pathlib import PurePosixPath
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
    visible: Collection[str],
    held_out: Collection[str],
) -> Entry:
    """The entry of a run from the result of `verify()` and the observations of its evidence;
    `visible` and `held_out` are the ids of the tests expected in the visible and sealed checks."""
    checks = observations.get("checks", [])
    shown = [
        test
        for check in checks
        if check.get("name") == VISIBLE_CHECK
        for test in check.get("tests", [])
        if str(test["id"]) in visible
    ]
    sealed = [test for test in observations.get("sealed") or [] if str(test["id"]) in held_out]
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
        visible_passed=_passed(shown),
        visible_failed=len(shown) - _passed(shown),
        held_out_passed=_passed(sealed),
        held_out_failed=len(sealed) - _passed(sealed),
        xfail_only=state != "complete" and failing == {XFAIL},
        failure="",
    )


def example_tests(directory: str, names: Iterable[str]) -> frozenset[str]:
    """The ids of the tests of the examples `names` of the conversion laid at `directory`."""
    return frozenset(
        f"{_module(directory)}test_dokime_examples::test_dokime_example[{name}]" for name in names
    )


def witness_tests(witness: Iterable[str], moved: Mapping[str, str]) -> frozenset[str]:
    """The ids of the tests that the witness turned green, for S1, under the path where its file
    was sealed: `moved` maps the path of a file at the witness to that path."""
    return frozenset(_renamed(test_id, moved) for test_id in witness)


def _renamed(test_id: str, moved: Mapping[str, str]) -> str:
    """The id of a test whose file was sealed at another path, as pytest gives it there: the dotted
    path of the file, and for a document of doctests also the name of the file after `::`."""
    module, _, rest = test_id.partition("::")
    for old, new in moved.items():
        if module == _dotted(old):
            if rest == PurePosixPath(old).name:
                rest = PurePosixPath(new).name
            return f"{_dotted(new)}::{rest}"
    return test_id


def _dotted(path: str) -> str:
    return path.removesuffix(".py").replace("/", ".")


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
