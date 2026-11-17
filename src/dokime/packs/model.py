"""The pack as the rest of the harness uses it, once its text has been checked."""

from dataclasses import dataclass
from pathlib import PurePosixPath

from dokime.core.findings import Finding, summarise
from dokime.core.verdicts import Verdict


@dataclass(frozen=True)
class Section:
    """A section of a file that holds the configuration of the tests with that of the project."""

    file: str
    format: str
    name: str


@dataclass(frozen=True)
class Pack:
    """How to build the environment of a verified project and how to run its tests."""

    name: str
    dockerfile: str
    command: tuple[str, ...]
    report: str
    test_paths: tuple[str, ...]
    config_paths: tuple[str, ...] = ()
    sections: tuple[Section, ...] = ()

    def is_test(self, path: str) -> bool:
        """Say whether a path of the project is a test: it matches a pattern of the test paths."""
        return any(PurePosixPath(path).full_match(pattern) for pattern in self.test_paths)

    def is_config(self, path: str) -> bool:
        """Say whether a path configures the tests: a pattern of the configuration, not a test."""
        matches = any(PurePosixPath(path).full_match(pattern) for pattern in self.config_paths)
        return matches and not self.is_test(path)

    def is_code(self, path: str) -> bool:
        """Say whether a path is code that is not a test: neither a test nor configuration."""
        return not self.is_test(path) and not self.is_config(path)


@dataclass(frozen=True)
class Checked:
    """The result of checking the text of a pack. The pack is missing when there is a finding."""

    pack: Pack | None
    findings: tuple[Finding, ...]

    @property
    def verdict(self) -> Verdict:
        """The verdict that the findings give: `PASS` when there are none."""
        return summarise(self.findings)
