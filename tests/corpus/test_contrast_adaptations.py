# SDD-EARS: CORPUS-110 CORPUS-111
"""The adaptations of the projects of the corpus for swarm-verify (R2)."""

import re
import tomllib

from tests.corpus.cases import ACTIVE
from tests.corpus.contrast.sample import CONTRAST

ADAPTATIONS = tomllib.loads((CONTRAST / "adaptations.toml").read_text())
PINNED = re.compile(r"[^@\s]+@sha256:[0-9a-f]{64}")


def test_every_project_with_a_case_has_an_adaptation() -> None:
    with_cases = {case.project for case in ACTIVE}
    assert with_cases, "no case"
    assert sorted(with_cases - set(ADAPTATIONS)) == []


def test_the_image_of_every_adaptation_is_pinned_by_its_digest() -> None:
    for name, entry in ADAPTATIONS.items():
        assert PINNED.fullmatch(entry["image"]), name
