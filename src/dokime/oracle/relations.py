"""The follow-ups of a relation and whether each gives what its source gave (ADR-0076).

A relation runs on the visible examples of its requirement at its target. `order-insensitive`
permutes the items of the input that `over` names, a list at `function` or the lines of a text at
`cli`: its follow-ups are the reversed order, when it gives another input, and up to the number of
the policy of other orders drawn with the seed. Two orders that give the same input count once, the
order of the source is never one, and there are never more than the distinct inputs that the items
allow. The draw takes nothing but the seed, so the same seed gives the same orders in the same
order. `idempotent` runs again on its own output, through the channel that the relation declares;
a source that did not succeed has no follow-up. The oracle runs nothing: it builds inputs and
compares observations.
"""

import json
import random
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from math import factorial, prod

from dokime.contract.model import Relation
from dokime.core.observation import Exited, Raised, Returned, StepObservation

_POSITION = re.compile(r"args\[(0|[1-9][0-9]*)\]")
_ENUMERATED = 5000
"""Up to this many distinct inputs, the orders are drawn from all of them; beyond, by shuffling."""


def orders(items: Sequence[object], seed: int, permutations: int) -> tuple[tuple[int, ...], ...]:
    """The follow-up orders of `order-insensitive`, as indices of the items of the source."""
    keys = [_key(item) for item in items]
    source = tuple(keys)
    counts = Counter(keys)
    others = factorial(len(keys)) // prod(factorial(count) for count in counts.values()) - 1
    found: list[tuple[int, ...]] = []
    seen = {source}
    backwards = tuple(range(len(keys) - 1, -1, -1))
    if _input(keys, backwards) not in seen:
        found.append(backwards)
        seen.add(_input(keys, backwards))
    wanted = min(permutations, others - len(found))
    if wanted <= 0:
        return tuple(found)
    chance = random.Random(seed)  # noqa: S311 - a draw anyone can repeat from the seed, not a secret
    if others <= _ENUMERATED or 2 * wanted >= others:
        left = [order for order in _distinct(keys) if _input(keys, order) not in seen]
        found.extend(chance.sample(left, wanted))
        return tuple(found)
    while wanted:
        order = list(range(len(keys)))
        chance.shuffle(order)
        given = _input(keys, order)
        if given not in seen:
            seen.add(given)
            found.append(tuple(order))
            wanted -= 1
    return tuple(found)


def _key(item: object) -> str:
    """The value of an item as a text, so that items equal in value and type are one."""
    return json.dumps(item, sort_keys=True, default=repr)


def _input(keys: Sequence[str], order: Sequence[int]) -> tuple[str, ...]:
    return tuple(keys[i] for i in order)


def _distinct(keys: Sequence[str]) -> list[tuple[int, ...]]:
    """One order for each distinct input that the items allow, in a fixed order."""
    ranks = sorted(set(keys))
    sequence = sorted(ranks.index(key) for key in keys)
    found = []
    while True:
        places: dict[int, list[int]] = {}
        for index, key in enumerate(keys):
            places.setdefault(ranks.index(key), []).append(index)
        taken = {rank: iter(indices) for rank, indices in places.items()}
        found.append(tuple(next(taken[rank]) for rank in sequence))
        if not _next(sequence):
            return found


def _next(sequence: list[int]) -> bool:
    """Turn a sequence into the next one in lexicographic order, and say whether there was one."""
    pivot = next((i for i in range(len(sequence) - 2, -1, -1) if sequence[i] < sequence[i + 1]), -1)
    if pivot < 0:
        return False
    swap = next(j for j in range(len(sequence) - 1, pivot, -1) if sequence[j] > sequence[pivot])
    sequence[pivot], sequence[swap] = sequence[swap], sequence[pivot]
    sequence[pivot + 1 :] = reversed(sequence[pivot + 1 :])
    return True


def items_of(boundary: str, given: Mapping[str, object], over: str) -> list[object] | None:
    """The items that `order-insensitive` permutes in an input, or none."""
    if boundary == "function":
        value = _argument(given, over)
        return list(value) if isinstance(value, list) else None
    text = _text(given, over)
    return None if text is None else list(_lines(text))


def in_order(
    boundary: str, given: Mapping[str, object], over: str, order: Sequence[int]
) -> dict[str, object]:
    """The input of a follow-up of `order-insensitive`: the source with its items in that order."""
    items = items_of(boundary, given, over)
    if items is None:
        raise ValueError(f"the input names nothing to permute with {over!r}")
    permuted = [items[i] for i in order]
    if boundary == "function":
        return _with_argument(given, over, permuted)
    text = _text(given, over) or ""
    rejoined = "\n".join(str(line) for line in permuted) + ("\n" if text.endswith("\n") else "")
    return _with_text(given, over, rejoined)


def repeated(
    boundary: str,
    given: Mapping[str, object],
    observed: StepObservation,
    over: str | None,
    via: str | None,
) -> dict[str, object] | None:
    """The input of the follow-up of `idempotent`, or none when the source did not succeed."""
    if boundary == "function":
        if not isinstance(observed, Returned):
            return None
        name = over if over is not None else _only_argument(given)
        return None if name is None else _with_argument(given, name, observed.value)
    if not isinstance(observed, Exited) or observed.exit != 0:
        return None
    if via == "stdout":
        return {**given, "stdin": observed.stdout}
    files = given.get("files")
    return {
        **given,
        "files": {**(dict(files) if isinstance(files, dict) else {}), **observed.files},
    }


def holds(
    relation: Relation,
    boundary: str,
    source: StepObservation,
    follow: StepObservation,
    *,
    source_given: Mapping[str, object] | None = None,
    follow_given: Mapping[str, object] | None = None,
) -> bool:
    """Whether a follow-up gives what its source gave."""
    if boundary == "function":
        if isinstance(source, Returned) and isinstance(follow, Returned):
            return _key(source.value) == _key(follow.value)
        if isinstance(source, Raised) and isinstance(follow, Raised):
            return source.qualified == follow.qualified
        return False
    if not (isinstance(source, Exited) and isinstance(follow, Exited)):
        return False
    if relation.relation == "idempotent" and relation.via == "stdout":
        return (source.exit, source.stdout) == (follow.exit, follow.stdout)
    if relation.relation == "idempotent":
        return dict(source.files) == dict(follow.files)
    produced = _produced(relation.over, source, source_given, follow, follow_given)
    return (source.exit, source.stdout, produced[0]) == (follow.exit, follow.stdout, produced[1])


def _produced(
    over: str | None,
    source: Exited,
    source_given: Mapping[str, object] | None,
    follow: Exited,
    follow_given: Mapping[str, object] | None,
) -> tuple[dict[str, str], dict[str, str]]:
    """The files of each run of `order-insensitive` to compare: the file that `over` names, which
    the follow-up receives permuted on purpose, is left out when each run leaves it as received."""
    left, right = dict(source.files), dict(follow.files)
    if over is None or over == "stdin":
        return left, right
    kept = all(
        _text(given or {}, over) == files.get(over)
        for given, files in ((source_given, left), (follow_given, right))
    )
    if kept:
        left.pop(over, None)
        right.pop(over, None)
    return left, right


def words(relation: Relation, example: str) -> str:
    """The words for the agent when a relation does not hold: where, and no value."""
    return (
        f"the requirement {relation.requirement} does not keep the relation"
        f" {relation.relation} on the visible example {example}"
    )


def _argument(given: Mapping[str, object], name: str) -> object:
    position = _POSITION.fullmatch(name)
    if position is not None:
        args = given.get("args")
        index = int(position.group(1))
        return args[index] if isinstance(args, list) and index < len(args) else None
    kwargs = given.get("kwargs")
    return kwargs.get(name) if isinstance(kwargs, dict) else None


def _with_argument(given: Mapping[str, object], name: str, value: object) -> dict[str, object]:
    changed = dict(given)
    position = _POSITION.fullmatch(name)
    if position is not None:
        args = list(changed.get("args") or [])  # type: ignore[call-overload]
        args[int(position.group(1))] = value
        changed["args"] = args
    else:
        kwargs = dict(changed.get("kwargs") or {})  # type: ignore[call-overload]
        kwargs[name] = value
        changed["kwargs"] = kwargs
    return changed


def _only_argument(given: Mapping[str, object]) -> str | None:
    args = given.get("args")
    kwargs = given.get("kwargs")
    positional = len(args) if isinstance(args, list) else 0
    named = list(kwargs) if isinstance(kwargs, dict) else []
    if positional == 1 and not named:
        return "args[0]"
    if positional == 0 and len(named) == 1:
        return str(named[0])
    return None


def _text(given: Mapping[str, object], over: str) -> str | None:
    if over == "stdin":
        value = given.get("stdin")
    else:
        files = given.get("files")
        value = files.get(over) if isinstance(files, dict) else None
    return value if isinstance(value, str) else None


def _with_text(given: Mapping[str, object], over: str, text: str) -> dict[str, object]:
    if over == "stdin":
        return {**given, "stdin": text}
    files = given.get("files")
    return {**given, "files": {**(dict(files) if isinstance(files, dict) else {}), over: text}}


def _lines(text: str) -> list[str]:
    lines = text.split("\n")
    return lines[:-1] if text.endswith("\n") else lines
