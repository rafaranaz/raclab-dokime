"""The strict reader of contract and flow files.

The library only parses the text. What the text means is decided here: one document, text keys,
no anchors, aliases, tags or merge keys, and no value whose type depends on the reader.
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import cast

import yaml

from dokime.core.findings import Finding
from dokime.core.verdicts import Verdict

type Value = bool | int | float | str | list[Value] | dict[str, Value] | None

_JSON_NUMBER = re.compile(r"-?(0|[1-9][0-9]*)(\.(?P<decimals>[0-9]+))?([eE][-+]?[0-9]+)?")
_CONSTANTS: dict[str, Value] = {"true": True, "false": False, "null": None}
_EXPONENT = r"([eE][-+]?[0-9]+)?"
_AMBIGUOUS = re.compile(
    "|".join(
        [
            r"(?i:y|n|yes|no|on|off|true|false|null)|~",  # booleans or null for some readers
            r"",  # an empty value
            rf"[-+]?0[0-9]+(\.[0-9]*)?{_EXPONENT}",  # leading zeros
            r"[-+]?0[xX][0-9a-fA-F_]+|[-+]?0[oO][0-7_]+|[-+]?0[bB][01_]+",  # other bases
            r"[-+]?[0-9][0-9_]*_[0-9_]*(\.[0-9_]*)?",  # digits with underscores
            rf"\+[0-9]+(\.[0-9]*)?{_EXPONENT}",  # a leading plus sign
            rf"[-+]?\.[0-9]+{_EXPONENT}|[-+]?[0-9]+\.{_EXPONENT}",  # a bare dot
            r"[-+]?\.(?i:inf)|\.(?i:nan)",  # infinities and not-a-number
            r"[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}"  # dates, alone or followed by a time
            r"(([Tt]|[ \t]+)[0-9]{1,2}:[0-9]{2}:[0-9]{2}(\.[0-9]*)?"
            r"([ \t]*(Z|[-+][0-9]{1,2}(:[0-9]{2})?))?)?",
            r"[-+]?[0-9][0-9_]*(:[0-5]?[0-9])+(\.[0-9_]*)?",  # times in base sixty
        ]
    )
)


type Path = tuple[str | int, ...]


@dataclass(frozen=True)
class Reading:
    """What a text holds, every problem found while reading it, and where each part is.

    `lines` gives the line where each key of a mapping and each item of a sequence starts. A part
    is addressed by its path from the root: the keys and the positions that lead to it.
    """

    value: Value
    findings: tuple[Finding, ...]
    lines: Mapping[Path, int] = field(default_factory=dict, compare=False)


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
    root = cast(yaml.Node, yaml.compose(text, Loader=yaml.SafeLoader))
    walk.lines[()] = _line(root.start_mark)
    value = walk.value(root, ())
    return Reading(value=value, findings=_in_order(walk.findings), lines=walk.lines)


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
    """Builds the value of a tree of nodes and collects its findings and the line of each part."""

    findings: list[Finding] = field(default_factory=list)
    lines: dict[Path, int] = field(default_factory=dict)

    def value(self, node: yaml.Node, path: Path) -> Value:
        if isinstance(node, yaml.MappingNode):
            return self._mapping(node, path)
        if isinstance(node, yaml.SequenceNode):
            return [self._part(item, (*path, index)) for index, item in enumerate(node.value)]
        return self._scalar(cast(yaml.ScalarNode, node))

    def _part(self, node: yaml.Node, path: Path, start: yaml.Node | None = None) -> Value:
        """Read a part of a mapping or of a sequence and note the line where it starts."""
        self.lines[path] = _line((start or node).start_mark)
        return self.value(node, path)

    def _mapping(self, node: yaml.MappingNode, path: Path) -> dict[str, Value]:
        result: dict[str, Value] = {}
        seen: dict[str, list[int]] = {}
        for key, item in node.value:
            line = _line(key.start_mark)
            if not isinstance(key, yaml.ScalarNode):
                self.findings.append(_fail("key-not-text", "a key must be a text", line))
                left_out = _Walk()
                left_out.value(item, ())
                self.findings.extend(left_out.findings)
                continue
            self._layout(key)
            if key.value == "<<" and not key.style:
                message = "the merge key << is not allowed; write the keys where they are used"
                self.findings.append(_fail("merge-key", message, line))
            seen.setdefault(key.value, []).append(line)
            result[key.value] = self._part(item, (*path, key.value), start=key)
        for name, lines in seen.items():
            if len(lines) > 1:
                message = f"the key {name!r} appears {len(lines)} times in the same mapping"
                self.findings.append(_fail("duplicate-key", message, *lines))
        return result

    def _scalar(self, node: yaml.ScalarNode) -> Value:
        text: str = node.value
        self._layout(node)
        if node.style:
            return text
        if text in _CONSTANTS:
            return _CONSTANTS[text]
        number = _JSON_NUMBER.fullmatch(text)
        if number is None:
            if _AMBIGUOUS.fullmatch(text):
                self._ambiguous(node, "YAML readers disagree on its type")
            return text
        decimals = number["decimals"]
        if decimals is None:
            return int(text) if text.lstrip("-").isdigit() else float(text)
        if len(decimals) > 1 and decimals.endswith("0"):
            self._ambiguous(node, "read as a number it loses its last zero")
            return text
        return float(text)

    def _ambiguous(self, node: yaml.ScalarNode, reason: str) -> None:
        message = (
            f"the value {node.value!r} is ambiguous: {reason}; put it in quotes if it is a text"
        )
        self.findings.append(_fail("ambiguous-value", message, _line(node.start_mark)))

    def _layout(self, node: yaml.ScalarNode) -> None:
        """Check the layout of a scalar: only a literal block may take several lines."""
        line = _line(node.start_mark)
        if node.style == "|":
            self._block(node.value, line)
        elif node.style == ">" or _line(node.end_mark) > line:
            message = (
                "a text on several lines is joined with spaces; write it as a literal block (|)"
            )
            self.findings.append(_fail("text-on-several-lines", message, line))

    def _block(self, text: str, line: int) -> None:
        if not text.endswith("\n") or text.endswith("\n\n"):
            message = "a literal block must end in exactly one newline; write it with | alone"
            self.findings.append(_fail("block-ending", message, line))
        for index, written in enumerate(text.split("\n"), start=1):
            if written != written.rstrip(" \t"):
                message = "a line of a literal block ends in a space or a tab"
                self.findings.append(_fail("trailing-whitespace", message, line + index))
