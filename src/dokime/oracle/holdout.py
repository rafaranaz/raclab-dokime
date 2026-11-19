"""The split of the examples of a contract into visible and held-out (ADR-0014).

A case is the set of examples of one requirement that share a name of case. The split holds out one
example of each case that has two or more and keeps every other example visible, so that each case
keeps at least one. The example held out of a case is chosen with `random.Random(seed).choice` over
the examples of the case in the order of the contract, with one generator for the contract and the
cases in the order in which each first appears, so that the split can be drawn again from the seed
that is recorded. The seed itself comes from outside, since the randomness of the system is an
adapter of `platform`.

An example to keep visible, one already published that the caller finds in the history, is never
drawn: the draw of a case is among its other examples, and a case where none is left holds out
nothing. The split names every case that holds out nothing, by its requirement and its name.

On a held-out failure the agent receives the requirement and the classes of the differences, never
a value, an input or the identifier of the example.
"""

import random
from collections.abc import Collection
from dataclasses import dataclass

from dokime.contract.model import Contract, Example
from dokime.oracle.compare import Comparison, Difference


@dataclass(frozen=True)
class Split:
    """The examples of a contract, split with a seed."""

    visible: tuple[Example, ...]
    held_out: tuple[Example, ...]
    without_holdout: tuple[str, ...]
    cases_without_holdout: tuple[tuple[str, str], ...] = ()


def split(contract: Contract, seed: int, keep_visible: Collection[str] = ()) -> Split:
    """Hold out one example of each case with two or more, chosen by the seed."""
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError(f"the seed of a split is an integer of at least 0, not {seed!r}")
    known = {e.id for e in contract.examples}
    strangers = sorted(set(keep_visible) - known)
    if strangers:
        raise ValueError(f"the examples to keep visible {strangers} are not of the contract")
    cases: dict[tuple[str, str], list[Example]] = {}
    for example in contract.examples:
        cases.setdefault((example.requirement, example.case), []).append(example)
    chance = random.Random(seed)  # noqa: S311 - a draw anyone can repeat from the seed, not a secret
    held = set()
    for examples in cases.values():
        drawable = [e for e in examples if e.id not in keep_visible]
        if len(examples) >= 2 and drawable:
            held.add(chance.choice(drawable).id)
    holding = {e.requirement for e in contract.examples if e.id in held}
    return Split(
        visible=tuple(e for e in contract.examples if e.id not in held),
        held_out=tuple(e for e in contract.examples if e.id in held),
        without_holdout=tuple(r.id for r in contract.requirements if r.id not in holding),
        cases_without_holdout=tuple(
            case for case, examples in cases.items() if not any(e.id in held for e in examples)
        ),
    )


def feedback(example: Example, comparison: Comparison) -> str:
    """The words for the agent when a held-out example fails, without any value."""
    classes = list(dict.fromkeys(_class(d) for d in comparison.differences))
    return f"the requirement {example.requirement} fails a held-out example: {', '.join(classes)}"


def _class(difference: Difference) -> str:
    """The class of a difference: its part, `files` for a file, or why a step was not seen."""
    if difference.part.startswith("files/"):
        return "files"
    if difference.part == "step":
        return "time-limit" if difference.observed == "time-limit" else "crashed"
    return difference.part
