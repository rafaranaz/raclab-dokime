# SDD-EARS: ORACLE-040 ORACLE-041 ORACLE-042 ORACLE-043 ORACLE-044 ORACLE-050 ORACLE-051
import random

import pytest

from dokime.contract.model import Contract, Example, Requirement, Step
from dokime.oracle.compare import Comparison, Difference
from dokime.oracle.holdout import feedback, split


def requirement(name: str) -> Requirement:
    return Requirement(id=name, kind="change", text="t", source="written", replaces=None, line=1)


def example(name: str, requirement: str, case: str) -> Example:
    return Example(
        id=name,
        requirement=requirement,
        case=case,
        boundary="cli",
        target="cmd",
        description=None,
        origin="human",
        steps=(Step(input={"args": [name]}, expect={"stdout": f"out of {name}\n"}),),
        line=1,
    )


def contract(*examples: Example, requirements: tuple[str, ...] = ("a", "b", "c")) -> Contract:
    return Contract(
        story="s",
        may_modify_tests=(),
        requirements=tuple(requirement(r) for r in requirements),
        examples=examples,
        relations=(),
    )


CONTRACT = contract(
    example("E-01", "a", "one"),
    example("E-02", "a", "two"),
    example("E-03", "a", "one"),
    example("E-04", "b", "one"),
    example("E-05", "a", "one"),
    example("E-06", "a", "two"),
    example("E-07", "c", "solo"),
)


def ids(examples: tuple[Example, ...]) -> list[str]:
    return [e.id for e in examples]


@pytest.mark.parametrize("seed", [0, 1, 7, 20261119])
def test_one_example_of_each_case_of_two_or_more_is_held_out(seed: int) -> None:
    held = split(CONTRACT, seed).held_out
    cases = sorted((e.requirement, e.case) for e in held)
    assert cases == [("a", "one"), ("a", "two")]


@pytest.mark.parametrize("seed", [0, 1, 7, 20261119])
def test_every_example_not_held_out_stays_visible_in_order(seed: int) -> None:
    done = split(CONTRACT, seed)
    held = set(ids(done.held_out))
    assert ids(done.visible) == [e.id for e in CONTRACT.examples if e.id not in held]
    assert "E-04" in ids(done.visible)
    assert "E-07" in ids(done.visible)


def test_the_choice_is_that_of_random_with_the_seed() -> None:
    chance = random.Random(20261119)  # noqa: S311 - a draw anyone can repeat, not a secret
    expected = [chance.choice(["E-01", "E-03", "E-05"]), chance.choice(["E-02", "E-06"])]
    held = ids(split(CONTRACT, 20261119).held_out)
    assert sorted(held) == sorted(expected)
    assert held == [e.id for e in CONTRACT.examples if e.id in expected]


def test_the_same_seed_gives_the_same_split() -> None:
    assert split(CONTRACT, 42) == split(CONTRACT, 42)


def test_the_requirements_without_a_held_out_example_are_named() -> None:
    assert split(CONTRACT, 3).without_holdout == ("b", "c")


@pytest.mark.parametrize("seed", [-1, 1.5, "7", True, None])
def test_a_seed_that_is_not_a_natural_integer_is_refused(seed: object) -> None:
    with pytest.raises(ValueError, match="seed") as refused:
        split(CONTRACT, seed)  # type: ignore[arg-type]
    assert repr(seed) in str(refused.value)


def test_the_words_name_the_requirement_and_the_classes_of_failure() -> None:
    held = example("E-05", "a", "one")
    comparison = Comparison(
        example="E-05",
        differences=(
            Difference(1, "stdout", "out of E-05\n", "secret output\n"),
            Difference(1, "exit", 0, 3),
            Difference(2, "files/report.txt", "expected text", "not written"),
            Difference(3, "step", None, "time-limit"),
        ),
    )
    words = feedback(held, comparison)
    assert words == ("the requirement a fails a held-out example: stdout, exit, files, time-limit")
    for leak in ("E-05", "out of", "secret", "report.txt", "expected text"):
        assert leak not in words


def test_a_crash_is_its_class_without_its_signal() -> None:
    held = example("E-05", "a", "one")
    comparison = Comparison(
        example="E-05", differences=(Difference(1, "step", None, "crashed by the signal 9"),)
    )
    assert feedback(held, comparison) == "the requirement a fails a held-out example: crashed"


def test_each_class_is_named_once() -> None:
    held = example("E-05", "a", "one")
    comparison = Comparison(
        example="E-05",
        differences=(Difference(1, "stdout", "x", "y"), Difference(2, "stdout", "z", "w")),
    )
    assert feedback(held, comparison) == "the requirement a fails a held-out example: stdout"
