# SDD-EARS: PACKS-023 PACKS-024 PACKS-025
import pytest

from dokime.packs.model import Section
from dokime.packs.sections import section_changed

INI = Section(file="setup.cfg", format="ini", name="tool:pytest")
TOML = Section(file="pyproject.toml", format="toml", name="tool.pytest.ini_options")

SETUP = b"""[metadata]
name = x

[tool:pytest]
addopts = -q
xfail_strict = true

[flake8]
max-line-length = 100
"""


def test_an_ini_section_that_keeps_its_text_is_unchanged_whatever_else_changes() -> None:
    after = SETUP.replace(b"name = x", b"name = y").replace(b"100", b"120")
    assert not section_changed(INI, SETUP, after)


@pytest.mark.parametrize(
    "after",
    [
        SETUP.replace(b"addopts = -q", b"addopts = -q --deselect tests/test_a.py"),
        SETUP.replace(b"addopts = -q", b"addopts = -q  # a comment"),
        SETUP.replace(b"xfail_strict = true", b"xfail_strict = true\nxfail_strict = false"),
        SETUP.replace(b"addopts", b"ADDOPTS"),
        SETUP + b"\n[tool:pytest]\n-p = no:randomly\n",
    ],
    ids=["an-option", "a-comment", "a-repeated-key", "the-case-of-a-key", "a-second-occurrence"],
)
def test_any_byte_changed_in_an_ini_section_is_a_change(after: bytes) -> None:
    assert section_changed(INI, SETUP, after)


def test_an_ini_section_that_appears_or_goes_is_a_change() -> None:
    without = b"[metadata]\nname = x\n"
    assert section_changed(INI, without, SETUP)
    assert section_changed(INI, SETUP, without)
    assert not section_changed(INI, without, None)
    assert not section_changed(INI, None, None)


PYPROJECT = b"""[project]
name = "x"

[tool.pytest.ini_options]
addopts = "--strict-markers"
xfail_strict = true
"""


def test_a_toml_section_with_the_same_value_is_unchanged_whatever_its_text() -> None:
    after = b"""[project]
name = "y"

[tool.pytest.ini_options]
xfail_strict    = true   # reordered and commented
addopts = '--strict-markers'
"""
    assert not section_changed(TOML, PYPROJECT, after)


def test_a_toml_section_defined_by_dotted_keys_in_another_table_is_seen() -> None:
    after = (
        PYPROJECT
        + b"""
[tool]
pytest.ini_options.addopts_more = "-p no:cacheprovider"
"""
    )
    assert section_changed(TOML, PYPROJECT, after)


def test_a_toml_section_that_appears_where_there_was_none_is_a_change() -> None:
    without = b'[project]\nname = "x"\n'
    added = without + b'\n[tool]\npytest.ini_options.addopts = "--deselect tests/test_a.py"\n'
    assert section_changed(TOML, without, added)
    assert section_changed(TOML, None, added)
    assert not section_changed(TOML, without, b'[project]\nname = "y"\n')


@pytest.mark.parametrize(
    ("section", "broken"),
    [(TOML, b"[tool.pytest.ini_options\n"), (TOML, b"\xff\xfe"), (INI, b"[tool:pytest]\n\xff\n")],
    ids=["not-toml", "toml-not-utf-8", "ini-not-utf-8"],
)
def test_a_file_that_cannot_be_read_counts_as_changed(section: Section, broken: bytes) -> None:
    good = PYPROJECT if section is TOML else SETUP
    assert section_changed(section, good, broken)
    assert section_changed(section, broken, good)
    assert section_changed(section, broken, broken)
