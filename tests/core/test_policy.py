# SDD-EARS: CORE-110 CORE-111 CORE-112 CORE-113 CORE-114 CORE-115 CORE-116 CORE-117
import pytest

from dokime.core.canonical import digest
from dokime.core.policy import DEFAULTS, Policy, read_policy

FULL = "format: 1\nbaseline:\n  runs: 3\nverification:\n  runs: 4\n"


def codes(text: str) -> list[tuple[str, tuple[int, ...]]]:
    return [(finding.code, finding.lines) for finding in read_policy(text).findings]


def test_a_full_policy_is_read() -> None:
    read = read_policy(FULL)
    assert (read.policy, read.findings) == (
        Policy(baseline_runs=3, verification_runs=4, from_file=True),
        (),
    )


@pytest.mark.parametrize(
    ("text", "found"),
    [
        ("format: 1\nformat: 1\n", [("duplicate-key", (1, 2))]),
        ("format: 1\nbaseline: yes\n", [("ambiguous-value", (2,)), ("wrong-type", (2,))]),
        ("format: 1\ngates: []\n", [("unknown-field", (2,))]),
        ("baseline:\n  runs: 2\n", [("missing-field", (1,))]),
        ("format: 2\n", [("unknown-value", (1,))]),
        ("format: 1\nbaseline: 2\n", [("wrong-type", (2,))]),
        ("format: 1\nverification:\n  runs: '2'\n", [("wrong-type", (3,))]),
        ("format: 1\nverification:\n  runs: 2.5\n", [("wrong-type", (3,))]),
        ("format: 1\nbaseline:\n  runs: true\n", [("wrong-type", (3,))]),
        ("format: 1\nbaseline:\n  runs: 2\n  seeds: 1\n", [("unknown-field", (4,))]),
    ],
    ids=[
        "duplicate-key",
        "ambiguous",
        "unknown-field",
        "no-format",
        "format-2",
        "not-a-mapping",
        "runs-text",
        "runs-decimal",
        "runs-boolean",
        "unknown-inner",
    ],
)
def test_a_policy_is_read_by_the_strict_rules_and_its_table(
    text: str, found: list[tuple[str, tuple[int, ...]]]
) -> None:
    assert codes(text) == found


@pytest.mark.parametrize("runs", [1, 0, -2])
def test_fewer_than_two_runs_are_refused_naming_the_field(runs: int) -> None:
    read = read_policy(f"format: 1\nverification:\n  runs: {runs}\n")
    (finding,) = read.findings
    assert (finding.code, finding.lines, "runs" in finding.message) == ("wrong-type", (3,), True)


def test_two_runs_are_accepted() -> None:
    assert read_policy("format: 1\nbaseline:\n  runs: 2\n").findings == ()


@pytest.mark.parametrize("text", ["format: 2\n", "format: 1\nbaseline:\n  runs: 1\n", "- 1\n"])
def test_a_policy_with_a_finding_gives_no_policy(text: str) -> None:
    read = read_policy(text)
    assert (read.policy, bool(read.findings)) == (None, True)


@pytest.mark.parametrize(
    "text", ["format: 1\n", "format: 1\nbaseline: {}\n", "format: 1\nverification: {}\n"]
)
def test_an_absent_field_gets_its_default(text: str) -> None:
    assert read_policy(text).policy == Policy(baseline_runs=2, verification_runs=2, from_file=True)


def test_without_a_file_the_policy_is_the_defaults() -> None:
    assert (DEFAULTS.baseline_runs, DEFAULTS.verification_runs) == (2, 2)


def test_the_policy_says_whether_it_came_from_the_file() -> None:
    assert (DEFAULTS.from_file, read_policy("format: 1\n").policy) == (
        False,
        Policy(from_file=True),
    )


def test_the_normalised_form_holds_the_format_and_every_field_with_the_defaults() -> None:
    read = read_policy("format: 1\nbaseline:\n  runs: 3\n").policy
    assert read is not None
    assert read.normalised() == {"format": 1, "baseline": {"runs": 3}, "verification": {"runs": 2}}
    assert DEFAULTS.normalised() == {
        "format": 1,
        "baseline": {"runs": 2},
        "verification": {"runs": 2},
    }


def test_the_digest_of_the_policy_is_the_digest_of_its_normalised_form() -> None:
    read = read_policy(FULL).policy
    assert read is not None
    assert read.digest() == digest(read.normalised())
    assert read.digest() != DEFAULTS.digest()


def test_a_file_that_states_the_defaults_has_the_digest_of_the_defaults() -> None:
    read = read_policy("format: 1\n").policy
    assert read is not None
    assert read.digest() == DEFAULTS.digest()
