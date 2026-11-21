# SDD-EARS: ORACLE-060 ORACLE-061
import pytest

from dokime.contract.model import Relation
from dokime.core.observation import Exited, Raised, Returned
from dokime.oracle.relations import holds, words

GIVEN: dict[str, object] = {"args": [[1, 2]]}
"""The input of both runs, which these comparisons do not depend on."""


def relation(kind: str, via: str | None = None) -> Relation:
    return Relation("L1", "R-sort", kind, "p:f", "args[0]", 9, via=via)


def raised(name: str) -> Raised:
    return Raised(
        type=name, qualified=f"builtins.{name}", classes=(f"builtins.{name}",), message="m"
    )


@pytest.mark.parametrize(
    ("source", "follow", "expected"),
    [
        (Returned([1, 2]), Returned([1, 2]), True),
        (Returned([1, 2]), Returned([2, 1]), False),
        (Returned(1), Returned(1.0), False),
        (Returned(True), Returned(1), False),
        (raised("ValueError"), raised("ValueError"), True),
        (raised("ValueError"), raised("TypeError"), False),
        (Returned(1), raised("ValueError"), False),
    ],
)
def test_at_function_the_same_return_or_exception_holds(
    source: object, follow: object, expected: bool
) -> None:
    found = holds(
        relation("order-insensitive"),
        "function",
        source,  # type: ignore[arg-type]
        follow,  # type: ignore[arg-type]
        source_given=GIVEN,
        follow_given=GIVEN,
    )
    assert found is expected


def ran(exit: int = 0, stdout: str = "x\n", files: dict[str, str] | None = None) -> Exited:
    return Exited(
        exit=exit, stdout=stdout, stderr="noise", files={"f": "v"} if files is None else files
    )


SOURCE = ran()


@pytest.mark.parametrize(
    ("kind", "via", "follow", "expected"),
    [
        ("idempotent", "stdout", ran(), True),
        ("idempotent", "stdout", ran(stdout="y\n"), False),
        ("idempotent", "stdout", ran(exit=1), False),
        ("idempotent", "stdout", ran(files={"f": "changed"}), True),
        ("idempotent", "files", ran(stdout="other\n"), True),
        ("idempotent", "files", ran(files={"f": "changed"}), False),
        ("order-insensitive", None, ran(), True),
        ("order-insensitive", None, ran(files={"f": "changed"}), False),
        ("order-insensitive", None, ran(stdout="y\n"), False),
        ("order-insensitive", None, ran(exit=2), False),
    ],
)
def test_at_cli_what_is_compared_follows_the_relation_and_its_channel(
    kind: str, via: str | None, follow: Exited, expected: bool
) -> None:
    found = holds(
        relation(kind, via), "cli", SOURCE, follow, source_given=GIVEN, follow_given=GIVEN
    )
    assert found is expected


def test_the_words_for_the_agent_name_the_requirement_the_relation_and_the_example() -> None:
    said = words(relation("order-insensitive"), "E-0007")
    assert "R-sort" in said
    assert "order-insensitive" in said
    assert "E-0007" in said
    assert "[" not in said


def test_at_cli_an_observation_that_is_not_a_run_does_not_hold() -> None:
    found = holds(
        relation("order-insensitive"),
        "cli",
        SOURCE,
        Returned("x"),
        source_given=GIVEN,
        follow_given=GIVEN,
    )
    assert found is False
