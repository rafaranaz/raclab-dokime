# SDD-EARS: CORPUS-100 CORPUS-101 CORPUS-102 CORPUS-108 CORPUS-109
"""The conversion of the examples of a contract into black-box checks for swarm-verify (R2, S2),
written for a small project of its own, never for the corpus."""

import json
import tomllib
from pathlib import Path

import pytest

from tests.corpus.contrast import runner
from tests.corpus.contrast.convert import ConversionError, convert
from tests.corpus.contrast.sample import (
    CONTRACT,
    CONTRAST,
    IDS,
    SOURCE,
    converted,
    examples,
    project,
)
from tests.corpus.projects import PROJECTS

__all__ = ["converted", "project"]
CORPUS = {one.name for one in PROJECTS}


def test_the_directory_holds_the_program_the_modules_the_examples_and_the_runner(
    converted: Path,
) -> None:
    assert (converted / "observe_program.py").read_bytes() == (
        SOURCE / "sandbox" / "observe_program.py"
    ).read_bytes()
    for module in ("core", "contract", "oracle", "sandbox"):
        for source in (SOURCE / module).glob("*.py"):
            copied = converted / "dokime" / module / source.name
            assert copied.read_bytes() == source.read_bytes(), copied
    assert sorted(p.name for p in (converted / "examples").iterdir()) == [f"{i}.json" for i in IDS]
    assert (converted / "run.py").read_bytes() == (CONTRAST / "runner.py").read_bytes()
    assert (converted / "test_dokime_examples.py").is_file()


def test_each_example_is_rebuilt_from_its_json_as_dokime_read_it(converted: Path) -> None:
    for name, example in examples().items():
        data = json.loads((converted / "examples" / f"{name}.json").read_text())
        assert runner.decode(data) == example


def test_an_existing_directory_is_refused_and_left_as_it_was(project: Path) -> None:
    out = project / "out"
    out.mkdir()
    with pytest.raises(ConversionError, match="exists"):
        convert(CONTRACT, ["E-1"], out)
    assert list(out.iterdir()) == []


def test_an_id_that_names_no_example_is_refused_and_nothing_is_written(project: Path) -> None:
    out = project / "out"
    with pytest.raises(ConversionError, match="E-9"):
        convert(CONTRACT, ["E-1", "E-9"], out)
    assert not out.exists()


def test_a_contract_that_cannot_be_read_is_refused_and_nothing_is_written(project: Path) -> None:
    out = project / "out"
    with pytest.raises(ConversionError, match="contract"):
        convert(CONTRACT.replace("format: 1", "format: 9"), ["E-1"], out)
    assert not out.exists()


def test_the_adaptations_give_only_their_fields_for_each_project() -> None:
    adaptations = tomllib.loads((CONTRAST / "adaptations.toml").read_text())
    assert adaptations, "no project"
    for name, entry in adaptations.items():
        assert sorted(entry) == ["files", "image", "minutes", "setup", "test"], name
        assert all(isinstance(text, str) for text in entry["files"].values()), name
        if name in CORPUS:
            assert isinstance(entry["minutes"], int), name
        else:
            assert entry["minutes"] == "not measured" or isinstance(entry["minutes"], int), name


FORBIDDEN = (
    "sealed.age",
    "sealed_store",
    "read_batch",
    "load_identity",
    "default_identity_path",
    "AgeSealedStore",
    "pyrage",
    "DOKIME_CORPUS_IDENTITY",
)


def test_the_code_of_the_contrast_opens_no_sealed_batch_and_uses_no_identity() -> None:
    for source in sorted(CONTRAST.glob("*.py")):
        text = source.read_text()
        found = [name for name in FORBIDDEN if name in text]
        assert found == [], (source.name, found)
