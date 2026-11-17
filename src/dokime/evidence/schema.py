"""Read the bytes of evidence back against the schema of its predicate (ADR-0064).

The bytes have to be JSON with whole numbers only, in the canonical form of ADR-0062, and their
value has to meet the closed schema of the predicate: no unknown field, no `null`, every required
field, and each value of its type, closed list or pattern. Every place that breaks the schema is a
finding of its own, in the order of the statement.
"""

import json
import re
from collections import Counter
from collections.abc import Callable, Mapping

from dokime.core.canonical import NotCanonicalError, canonical
from dokime.core.findings import Finding
from dokime.core.repository import CommitName, TreeName
from dokime.core.runtime import Digest
from dokime.core.verdicts import Verdict

STATEMENT = "https://in-toto.io/Statement/v1"
PREDICATE = "https://github.com/rafaranaz/raclab-dokime/attestation/conformance/v0.1"
ORIGINS = ("existing", "human", "derived", "model")
"""The origins of the checks of a gate, in the order a gate lists them."""
NAME = re.compile(r"[A-Za-z][A-Za-z0-9]*(-[A-Za-z0-9]+)*")
"""A name, as the story or the id of a requirement or an example."""
NOT_CHECKED = (
    "no-holdout",
    "requirement-without-example",
    "only-model-checks",
    "gate-skipped",
    "test-excluded-unstable",
    "test-excluded-network",
    "boundary-not-supported",
    "best-effort-secrecy",
    "outside-threat-model",
    "example-unstable",
)
"""The closed list of the codes of what was not checked."""
_SHA256 = re.compile(r"[0-9a-f]{64}")

type Place = tuple[str | int, ...]
type Rule = Callable[["_Check", object, Place], None]


class _NotWholeJsonError(ValueError):
    """The bytes are not JSON of whole numbers."""


def read_back(data: bytes) -> tuple[Finding, ...]:
    """Every finding of the bytes of evidence: none when they meet the schema."""
    try:
        value = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_unique,
            parse_float=_refuse,
            parse_constant=_refuse,
        )
    except (UnicodeDecodeError, ValueError, RecursionError) as error:
        return (_error("evidence-not-json", f"the evidence is not JSON of whole numbers: {error}"),)
    try:
        written = canonical(value).encode("utf-8")
    except NotCanonicalError as error:
        return (_error("evidence-not-canonical", f"the evidence is not canonical: {error}"),)
    if written != data:
        return (_error("evidence-not-canonical", "the evidence is not in the canonical form"),)
    check = _Check()
    _statement(check, value, ())
    return tuple(
        _error("evidence-schema", f"the evidence does not meet the schema at {where}")
        for where in check.problems
    )


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    repeated = [key for key, count in Counter(key for key, _ in pairs).items() if count > 1]
    if repeated:
        raise _NotWholeJsonError(f"the key {repeated[0]!r} is repeated")
    return dict(pairs)


def _refuse(text: str) -> object:
    raise _NotWholeJsonError(f"the number {text} is not whole")


def _error(code: str, message: str) -> Finding:
    return Finding(code=code, message=message, verdict=Verdict.ERROR)


class _Check:
    """The places where a value breaks the schema, in the order they are met."""

    def __init__(self) -> None:
        self.problems: list[str] = []

    def bad(self, place: Place, why: str) -> None:
        named = "/".join(str(part) for part in place) or "the root"
        self.problems.append(f"{named}: {why}")


def _fields(required: Mapping[str, Rule], optional: Mapping[str, Rule] | None = None) -> Rule:
    allowed = optional or {}

    def rule(check: _Check, value: object, place: Place) -> None:
        if not isinstance(value, dict):
            check.bad(place, "is not a mapping")
            return
        for key in value:
            if key not in required and key not in allowed:
                check.bad((*place, key), "is not a field of the schema")
        for key, inner in required.items():
            if key in value:
                inner(check, value[key], (*place, key))
            else:
                check.bad((*place, key), "is missing")
        for key, inner in allowed.items():
            if key in value:
                inner(check, value[key], (*place, key))

    return rule


def _list(each: Rule, *, at_least: int = 0) -> Rule:
    def rule(check: _Check, value: object, place: Place) -> None:
        if not isinstance(value, list):
            check.bad(place, "is not a list")
            return
        if len(value) < at_least:
            check.bad(place, f"has fewer than {at_least} entries")
        for position, entry in enumerate(value):
            each(check, entry, (*place, position))

    return rule


def _matches(why: str, accepts: Callable[[str], bool]) -> Rule:
    def rule(check: _Check, value: object, place: Place) -> None:
        if not isinstance(value, str) or not accepts(value):
            check.bad(place, why)

    return rule


def _builds(kind: Callable[[str], object]) -> Callable[[str], bool]:
    def accepts(text: str) -> bool:
        try:
            kind(text)
        except ValueError:
            return False
        return True

    return accepts


def _is(constant: object) -> Rule:
    def rule(check: _Check, value: object, place: Place) -> None:
        if type(value) is not type(constant) or value != constant:
            check.bad(place, f"is not {json.dumps(constant)}")

    return rule


def _whole(at_least: int) -> Rule:
    def rule(check: _Check, value: object, place: Place) -> None:
        if type(value) is not int or value < at_least:
            check.bad(place, f"is not a whole number of at least {at_least}")

    return rule


def _code(text: str) -> object:
    return Finding(code=text, message="a code", verdict=Verdict.ERROR)


_TEXT = _matches("is not a text that is not empty", bool)
_NAME = _matches("is not a name", lambda text: NAME.fullmatch(text) is not None)
_DIGEST = _matches("is not a digest", _builds(Digest))
_VERDICT = _matches("is not a verdict", lambda text: text in {v.value for v in Verdict})
_FOUND = _matches("is not the verdict of a finding", lambda text: text in {"FAIL", "ASK", "ERROR"})
_UNTRUSTED = _fields({"label": _TEXT, "text": _matches("is not a text", lambda _: True)})
_FINDING = _fields(
    {
        "code": _matches("is not a code", _builds(_code)),
        "verdict": _FOUND,
        "lines": _list(_whole(1)),
        "untrusted": _list(_fields({"label": _is("message"), "text": _TEXT}), at_least=1),
    }
)
_RAN = _fields(
    {"gate": _NAME, "status": _is("run"), "verdict": _VERDICT, "findings": _list(_FINDING)},
    {
        "checks": _list(
            _fields(
                {"origin": _matches("is not an origin", ORIGINS.__contains__), "total": _whole(1)}
            ),
            at_least=1,
        )
    },
)
_NOT_APPLICABLE = _fields({"gate": _NAME, "status": _is("not-applicable"), "reason": _TEXT})


def _gate(check: _Check, value: object, place: Place) -> None:
    status = value.get("status") if isinstance(value, dict) else None
    (_NOT_APPLICABLE if status == "not-applicable" else _RAN)(check, value, place)


def _gates(check: _Check, value: object, place: Place) -> None:
    _list(_gate)(check, value, place)
    if isinstance(value, list):
        names = [gate.get("gate") for gate in value if isinstance(gate, dict)]
        counted = Counter(name for name in names if isinstance(name, str))
        for name in sorted(name for name, count in counted.items() if count > 1):
            check.bad(place, f"lists the gate {name!r} more than once")


_NOT_CHECKED = _fields(
    {
        "code": _matches("is not a code of what was not checked", NOT_CHECKED.__contains__),
        "what": _NAME,
        "reason": _TEXT,
    },
    {"untrusted": _list(_UNTRUSTED, at_least=1)},
)
_PREDICATE = _fields(
    {
        "verdict": _VERDICT,
        "delivered": _is(False),
        "independence": _is("self-attested"),
        "verifier": _fields({"harness": _TEXT, "ran_on": _is("developer")}),
        "contract": _fields({"story": _NAME}, {"digest": _DIGEST}),
        "inputs": _fields(
            {
                "base": _matches("is not the name of a commit", _builds(CommitName)),
                "policy": _fields(
                    {
                        "digest": _DIGEST,
                        "source": _matches(
                            "is not file or defaults", {"file", "defaults"}.__contains__
                        ),
                    }
                ),
            },
            {
                "image": _fields({"digest": _DIGEST}, {"platform": _DIGEST}),
                "pack": _fields({"digest": _DIGEST}),
                "probe": _DIGEST,
            },
        ),
        "gates": _gates,
        "human_decisions": _is([]),
        "not_checked": _list(_NOT_CHECKED),
        "ledger": _fields({"events": _whole(0)}, {"head": _DIGEST}),
    }
)
_SUBJECT = _fields(
    {
        "name": _is("tree"),
        "digest": _fields({"gitTree": _matches("is not the name of a tree", _builds(TreeName))}),
    }
)
_PATCH = _fields(
    {
        "name": _is("change.patch"),
        "digest": _fields(
            {"sha256": _matches("is not a SHA-256", lambda t: _SHA256.fullmatch(t) is not None)}
        ),
    }
)


def _subject(check: _Check, value: object, place: Place) -> None:
    if not isinstance(value, list):
        check.bad(place, "is not a list")
        return
    for position, rule in enumerate((_SUBJECT, _PATCH)):
        if position < len(value):
            rule(check, value[position], (*place, position))
        else:
            check.bad((*place, position), "is missing")
    for position in range(2, len(value)):
        check.bad((*place, position), "is not a subject of the schema")


_statement = _fields(
    {
        "_type": _is(STATEMENT),
        "subject": _subject,
        "predicateType": _is(PREDICATE),
        "predicate": _PREDICATE,
    }
)
