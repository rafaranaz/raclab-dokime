"""The channel of each relation, checked against the visible examples it runs on (ADR-0076).

The boundary of a relation is that of the visible examples of its requirement at its target. Its
channel is declared, never deduced: `via` says how `idempotent` gives its output back at `cli`, and
`over` names the argument of a function, or `stdin` or a file of the input at `cli`.
"""

import keyword
import re
from collections.abc import Sequence

from dokime.contract.model import Example, Relation
from dokime.core.findings import Finding
from dokime.core.verdicts import Verdict

_POSITION = re.compile(r"args\[(0|[1-9][0-9]*)\]")


def channels(
    relations: tuple[Relation, ...],
    examples: tuple[Example, ...],
    requirements: frozenset[str],
    every_example_read: bool,
) -> list[Finding]:
    """The findings of the channel of each relation, in the order of the relations; none while an
    example did not read or names an unknown requirement, since a relation could then lack a source
    it has, and none for a relation of an unknown requirement, which has a finding of its own."""
    if not every_example_read:
        return []
    findings: list[Finding] = []
    for one in relations:
        if one.requirement not in requirements:
            continue
        sources = [
            e for e in examples if (e.requirement, e.target) == (one.requirement, one.target)
        ]
        if not sources:
            message = (
                f"no visible example of the requirement {one.requirement!r} has the target of the"
                f" relation {one.id!r}, so nothing tells its boundary nor feeds it"
            )
            findings.append(_found("relation-without-example", message, one, Verdict.ASK))
            continue
        boundaries = sorted({e.boundary for e in sources})
        if len(boundaries) > 1:
            message = (
                f"the examples of the relation {one.id!r} are at the boundaries"
                f" {', '.join(boundaries)}, so its target names more than one thing"
            )
            findings.append(_found("relation-target-ambiguous", message, one))
            continue
        findings.extend(_of_boundary(one, boundaries[0], sources))
    return findings


def _of_boundary(one: Relation, boundary: str, sources: list[Example]) -> list[Finding]:
    found: list[Finding] = []
    at_cli = boundary == "cli"
    if one.via is not None and not (one.relation == "idempotent" and at_cli):
        message = f"the relation {one.id!r} has via, which only idempotent at cli has"
        found.append(_found("relation-via-not-allowed", message, one))
    if one.relation == "idempotent" and at_cli and one.via is None:
        message = f"the relation {one.id!r} is idempotent at cli and says no via: stdout or files"
        found.append(_found("relation-needs-via", message, one))
    inputs = [step.input for e in sources for step in e.steps]
    if boundary == "function":
        found.extend(_at_function(one, inputs))
    elif at_cli and one.over is not None:
        files = {name for given in inputs for name in _mapping(given.get("files"))}
        if one.relation == "idempotent" or (one.over != "stdin" and one.over not in files):
            message = (
                f"the over {one.over!r} of the relation {one.id!r} is not stdin nor a file of the"
                " input of its examples, or the relation is idempotent at cli, which has via"
            )
            found.append(_found("bad-over", message, one))
    return found


def _at_function(one: Relation, inputs: Sequence[object]) -> list[Finding]:
    positional = [len(_list(_mapping(given).get("args"))) for given in inputs]
    named = {name for given in inputs for name in _mapping(_mapping(given).get("kwargs"))}
    if one.over is None:
        counts = [
            p + len(_mapping(_mapping(g).get("kwargs")))
            for p, g in zip(positional, inputs, strict=True)
        ]
        if one.relation == "idempotent" and any(count > 1 for count in counts):
            message = (
                f"the relation {one.id!r} is idempotent at a function of more than one argument"
                " and says no over: the argument that receives the output"
            )
            return [_found("relation-needs-over", message, one)]
        return []
    position = _POSITION.fullmatch(one.over)
    if position is not None:
        names = any(count > int(position.group(1)) for count in positional)
    else:
        names = one.over.isidentifier() and not keyword.iskeyword(one.over) and one.over in named
    if names:
        return []
    message = (
        f"the over {one.over!r} of the relation {one.id!r} is not args[N] nor a keyword argument"
        " that an example of its requirement at its target gives"
    )
    return [_found("bad-over", message, one)]


def _mapping(value: object) -> dict[str, object]:
    return {str(k): v for k, v in value.items()} if isinstance(value, dict) else {}


def _list(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


def _found(code: str, message: str, one: Relation, verdict: Verdict = Verdict.FAIL) -> Finding:
    return Finding(code=code, message=message, verdict=verdict, lines=(one.line,))
