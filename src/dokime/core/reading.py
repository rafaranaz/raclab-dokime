"""The strict reader of contract and flow files.

The library only parses the text. What the text means is decided here: one document, text keys,
no anchors, aliases, tags or merge keys, and no value whose type depends on the reader.
"""

import re
from dataclasses import dataclass, field

import yaml

from dokime.core.findings import Finding
from dokime.core.verdicts import Verdict

type Value = bool | int | float | str | list[Value] | dict[str, Value] | None

_JSON_NUMBER = re.compile(r"-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][-+]?[0-9]+)?")
_CONSTANTS: dict[str, Value] = {"true": True, "false": False, "null": None}


@dataclass(frozen=True)
class Reading:
    """What a text holds and every problem found while reading it."""

    value: Value
    findings: tuple[Finding, ...]


def read(text: str) -> Reading:
    """Read the text of a contract or of a flow file by the strict rules.

    The value is missing when the text is not YAML, does not hold exactly one document or has an
    anchor or an alias. Otherwise it comes together with every finding.
    """
    try:
        events = list(yaml.parse(text, Loader=yaml.SafeLoader))
    except yaml.YAMLError as error:
        return _stopped([_not_yaml(error, text)])
    documents = sum(isinstance(event, yaml.DocumentStartEvent) for event in events)
    if documents != 1:
        message = f"the text holds {documents} documents; it must hold exactly one"
        return _stopped([_fail("not-one-document", message)])
    shared = [finding for event in events if (finding := _anchor_or_alias(event))]
    if shared:
        return _stopped(shared)
    walk = _Walk()
    walk.findings.extend(finding for event in events if (finding := _tag(event)))
    value = walk.value(yaml.compose(text, Loader=yaml.SafeLoader))
    return Reading(value=value, findings=_in_order(walk.findings))


def _fail(code: str, message: str, *lines: int) -> Finding:
    return Finding(code=code, message=message, verdict=Verdict.FAIL, lines=lines)


def _stopped(findings: list[Finding]) -> Reading:
    return Reading(value=None, findings=_in_order(findings))


def _in_order(findings: list[Finding]) -> tuple[Finding, ...]:
    return tuple(sorted(findings, key=lambda finding: (finding.lines, finding.code)))


def _line(mark: object) -> int:
    """The line of a mark of the parser, counted from 1."""
    return int(getattr(mark, "line", 0)) + 1


def _not_yaml(error: yaml.YAMLError, text: str) -> Finding:
    if isinstance(error, yaml.MarkedYAMLError) and error.problem_mark is not None:
        return _fail(
            "not-yaml", f"the text is not YAML: {error.problem}", _line(error.problem_mark)
        )
    position = getattr(error, "position", 0)
    reason = getattr(error, "reason", "it cannot be read")
    return _fail("not-yaml", f"the text is not YAML: {reason}", text.count("\n", 0, position) + 1)


def _anchor_or_alias(event: yaml.Event) -> Finding | None:
    name = getattr(event, "anchor", None)
    if name is None:
        return None
    sign = "*" if isinstance(event, yaml.AliasEvent) else "&"
    message = f"{sign}{name}: anchors and aliases are not allowed; write the value where it is used"
    return _fail("anchor-or-alias", message, _line(event.start_mark))


def _tag(event: yaml.Event) -> Finding | None:
    tag = getattr(event, "tag", None)
    if tag is None:
        return None
    return _fail(
        "tag", f"the tag {tag} is not allowed; write the value alone", _line(event.start_mark)
    )


@dataclass
class _Walk:
    """Builds the value of a tree of nodes and collects the findings of its nodes."""

    findings: list[Finding] = field(default_factory=list)

    def value(self, node: yaml.Node | None) -> Value:
        if isinstance(node, yaml.MappingNode):
            return self._mapping(node)
        if isinstance(node, yaml.SequenceNode):
            return [self.value(item) for item in node.value]
        if isinstance(node, yaml.ScalarNode):
            return self._scalar(node)
        return None

    def _mapping(self, node: yaml.MappingNode) -> dict[str, Value]:
        result: dict[str, Value] = {}
        seen: dict[str, list[int]] = {}
        for key, item in node.value:
            line = _line(key.start_mark)
            if not isinstance(key, yaml.ScalarNode):
                self.findings.append(_fail("key-not-text", "a key must be a text", line))
                self.value(item)
                continue
            if key.value == "<<" and not key.style:
                message = "the merge key << is not allowed; write the keys where they are used"
                self.findings.append(_fail("merge-key", message, line))
            seen.setdefault(key.value, []).append(line)
            result[key.value] = self.value(item)
        for name, lines in seen.items():
            if len(lines) > 1:
                message = f"the key {name!r} appears {len(lines)} times in the same mapping"
                self.findings.append(_fail("duplicate-key", message, *lines))
        return result

    def _scalar(self, node: yaml.ScalarNode) -> Value:
        text: str = node.value
        if node.style:
            return text
        if text in _CONSTANTS:
            return _CONSTANTS[text]
        if _JSON_NUMBER.fullmatch(text):
            return int(text) if text.lstrip("-").isdigit() else float(text)
        return text
