# SDD-EARS: CORPUS-075
"""The intent sentence of each good case, in a file apart from the files of the cases."""

import re
import tomllib
from pathlib import Path
from typing import Any

import pytest

from tests.corpus.cases import CASES, Case

INTENTS = Path(__file__).parent / "intents.toml"
SOURCE = re.compile(r"(issue|pr):https://github\.com/\S+|commit:[0-9a-f]{40}|maintainer")
FIELDS = {"intent", "source", "skipped", "seen_contract"}


def intents() -> dict[str, Any]:
    if not INTENTS.exists():
        return {}
    return tomllib.loads(INTENTS.read_text())


GOOD = [case for case in CASES if case.good]


@pytest.mark.parametrize("case", GOOD, ids=lambda case: case.key)
def test_each_good_case_has_an_intent_with_a_valid_source(case: Case) -> None:
    entry = intents().get(case.key)
    assert isinstance(entry, dict), case.key
    assert set(entry) <= FIELDS
    assert isinstance(entry["intent"], str)
    assert entry["intent"].strip()
    assert SOURCE.fullmatch(entry["source"]), entry["source"]
    if "seen_contract" in entry:
        assert entry["source"] == "maintainer"
        assert isinstance(entry["seen_contract"], bool)


def test_only_good_cases_have_an_intent() -> None:
    assert set(intents()) <= {case.key for case in GOOD}
