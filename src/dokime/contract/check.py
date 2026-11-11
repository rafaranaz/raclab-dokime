"""The check of a contract: it validates its text and says what the contract lacks."""

from collections.abc import Callable, Iterator

from dokime.contract import shape
from dokime.contract.compare import compare
from dokime.contract.model import Checked, Contract, Example, Relation, Requirement
from dokime.contract.notes import Notes
from dokime.core.findings import Finding
from dokime.core.reading import Path, Value, read
from dokime.core.verdicts import Verdict

_SECTIONS = ("requirements", "examples", "relations")


def check(text: str) -> Checked:
    """Check the text of a contract and return it together with every finding.

    Every finding comes in one result, in the order of the lines. The contract is returned when no
    finding has the verdict `FAIL` or `ERROR`.
    """
    reading = read(text)
    if reading.value is None:
        return Checked(contract=None, findings=reading.findings)
    notes = Notes(reading, list(reading.findings))
    contract = _contract(notes, reading.value)
    findings = tuple(sorted(notes.findings, key=lambda finding: (finding.lines, finding.code)))
    stopped = any(finding.verdict in (Verdict.FAIL, Verdict.ERROR) for finding in findings)
    return Checked(contract=None if stopped else contract, findings=findings)


def _contract(notes: Notes, root: Value) -> Contract | None:
    if not isinstance(root, dict):
        notes.add("wrong-type", "a contract is a mapping", ())
        return None
    _blocks_outside_text(notes)
    shape.check_fields(notes, root, (), shape.CONTRACT)
    if root.get("requirements") == []:
        notes.add("empty-list", "a contract has at least one requirement", ("requirements",))
    requirements = _each(notes, root, "requirements", shape.requirement)
    examples = _each(notes, root, "examples", shape.example)
    relations = _each(notes, root, "relations", shape.relation)
    _repeated_ids(notes, root)
    _unknown_requirements(notes, root)
    _coverage(notes, root)
    notes.findings.extend(compare(examples))
    tests = root.get("may_modify_tests")
    return Contract(
        story=str(root.get("story")),
        may_modify_tests=tuple(str(test) for test in tests) if isinstance(tests, list) else (),
        requirements=tuple(requirements),
        examples=tuple(examples),
        relations=tuple(relations),
    )


def _each[Item: (Requirement, Example, Relation)](
    notes: Notes,
    root: dict[str, Value],
    section: str,
    check_one: Callable[[Notes, Value, Path], Item | None],
) -> list[Item]:
    """Check every item of a section and return those without a finding."""
    items = root.get(section)
    if not isinstance(items, list):
        return []
    checked = (check_one(notes, item, (section, index)) for index, item in enumerate(items))
    return [item for item in checked if item is not None]


def _items(root: dict[str, Value], section: str) -> Iterator[tuple[Path, dict[str, Value]]]:
    """The items of a section that are mappings, each with its path."""
    items = root.get(section)
    if isinstance(items, list):
        for index, item in enumerate(items):
            if isinstance(item, dict):
                yield (section, index), item


def _blocks_outside_text(notes: Notes) -> None:
    for path in sorted(notes.reading.blocks, key=notes.line):
        if not path or path[-1] != "$text":
            message = "a literal block is the value of $text, with its final_newline"
            notes.add("block-outside-text", message, path)


def _repeated_ids(notes: Notes, root: dict[str, Value]) -> None:
    for section in _SECTIONS:
        lines: dict[str, list[int]] = {}
        for path, item in _items(root, section):
            if isinstance(item.get("id"), str):
                lines.setdefault(str(item["id"]), []).append(notes.line((*path, "id")))
        for name, where in lines.items():
            if len(where) > 1:
                message = f"the id {name!r} appears {len(where)} times among the {section}"
                notes.add_at("duplicate-id", message, tuple(where))


def _requirement_ids(root: dict[str, Value]) -> list[str] | None:
    """The ids of the requirements, or nothing when one of them cannot be relied on."""
    items = root.get("requirements")
    if not isinstance(items, list):
        return None
    ids = [item.get("id") if isinstance(item, dict) else None for item in items]
    if not all(shape.is_name(name) for name in ids):
        return None
    return [str(name) for name in ids]


def _unknown_requirements(notes: Notes, root: dict[str, Value]) -> None:
    known = _requirement_ids(root)
    if known is None:
        return
    for section in ("examples", "relations"):
        for path, item in _items(root, section):
            name = item.get("requirement")
            if shape.is_name(name) and name not in known:
                message = f"the contract has no requirement {name!r}"
                notes.add("unknown-requirement", message, (*path, "requirement"))


def _coverage(notes: Notes, root: dict[str, Value]) -> None:
    """Ask about the requirements that no example of a person supports."""
    if not isinstance(root.get("examples"), list):
        return
    examples = [item for _, item in _items(root, "examples")]
    seen: set[str] = set()
    for path, item in _items(root, "requirements"):
        name = item.get("id")
        if not isinstance(name, str) or not shape.is_name(name) or name in seen:
            continue
        seen.add(name)
        origins = [one.get("origin") for one in examples if one.get("requirement") == name]
        if not origins:
            message = f"the requirement {name!r} has no example"
            notes.findings.append(_ask("requirement-without-example", message, notes.line(path)))
        elif all(origin == "model" for origin in origins):
            message = f"the requirement {name!r} has only examples proposed by a model"
            notes.findings.append(_ask("only-model-examples", message, notes.line(path)))


def _ask(code: str, message: str, line: int) -> Finding:
    return Finding(code=code, message=message, verdict=Verdict.ASK, lines=(line,))
