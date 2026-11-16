"""The policy of a project: the values the harness reads from `.dokime/policy.yaml` (ADR-0054).

The file is optional. Without it the effective policy is the defaults; with it, a field it leaves
out takes its default. Either way the evidence records the digest of the normalised form, which
holds the format and every field with its value, so a field added later changes the digest in a
way that can be explained.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from dokime.core.canonical import digest
from dokime.core.findings import Finding
from dokime.core.reading import Value, read
from dokime.core.shape import Field, Notes, check_fields, one_of

FORMAT = 1
MINIMUM_RUNS = 2
"""With one run, an unstable test or a verdict that varies cannot be seen."""


@dataclass(frozen=True)
class Policy:
    """The effective policy, read from the file or made of the defaults."""

    baseline_runs: int = 2
    verification_runs: int = 2
    from_file: bool = False

    def normalised(self) -> dict[str, object]:
        """The form whose digest the evidence records: the format and every field."""
        return {
            "format": FORMAT,
            "baseline": {"runs": self.baseline_runs},
            "verification": {"runs": self.verification_runs},
        }

    def digest(self) -> str:
        """The digest of the normalised form."""
        return digest(self.normalised())


DEFAULTS = Policy()


@dataclass(frozen=True)
class CheckedPolicy:
    """The policy a text holds, or none when it has a finding, and every finding of the text."""

    policy: Policy | None
    findings: tuple[Finding, ...]


def _is_runs(value: object) -> bool:
    return type(value) is int and value >= MINIMUM_RUNS


def _is_mapping(value: object) -> bool:
    return isinstance(value, dict)


_RUNS = f"a whole number of at least {MINIMUM_RUNS}"
_POLICY: Mapping[str, Field] = {
    "format": one_of(FORMAT),
    "baseline": Field("a mapping", _is_mapping, mandatory=False),
    "verification": Field("a mapping", _is_mapping, mandatory=False),
}
_SECTION: Mapping[str, Field] = {"runs": Field(_RUNS, _is_runs, mandatory=False)}


def read_policy(text: str) -> CheckedPolicy:
    """Read the text of a policy file by the strict rules and the table of its fields."""
    reading = read(text)
    if reading.value is None:
        return CheckedPolicy(policy=None, findings=reading.findings)
    notes = Notes(reading, list(reading.findings))
    runs = _runs(notes, reading.value)
    findings = tuple(sorted(notes.findings, key=lambda finding: (finding.lines, finding.code)))
    if findings or runs is None:
        return CheckedPolicy(policy=None, findings=findings)
    baseline, verification = runs
    return CheckedPolicy(
        policy=Policy(baseline_runs=baseline, verification_runs=verification, from_file=True),
        findings=(),
    )


def _runs(notes: Notes, root: Value) -> tuple[int, int] | None:
    if not isinstance(root, dict):
        notes.add("wrong-type", "a policy is a mapping", ())
        return None
    check_fields(notes, root, (), _POLICY)
    found: list[int] = []
    for name, default in (
        ("baseline", DEFAULTS.baseline_runs),
        ("verification", DEFAULTS.verification_runs),
    ):
        section = root.get(name, {})
        if not isinstance(section, dict):
            return None
        check_fields(notes, section, (name,), _SECTION)
        runs = section.get("runs", default)
        found.append(runs if isinstance(runs, int) and _is_runs(runs) else default)
    return found[0], found[1]
