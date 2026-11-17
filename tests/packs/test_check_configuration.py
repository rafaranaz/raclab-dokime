# SDD-EARS: PACKS-012 PACKS-016 PACKS-017 PACKS-022
import pytest

from dokime.packs.model import Section
from tests.packs.packs import only, seeded

CONFIG = '  config: ["pytest.ini"]\n'
WITH = """  config: ["pytest.ini", ".pytest.ini", "conftest.py"]
  sections:
    - file: pyproject.toml
      format: toml
      section: tool.pytest.ini_options
    - file: setup.cfg
      format: ini
      section: "tool:pytest"
"""


def test_a_pack_with_the_configuration_and_its_sections_is_read() -> None:
    checked = seeded(CONFIG, WITH)
    assert checked.pack is not None
    assert checked.pack.config_paths == ("pytest.ini", ".pytest.ini", "conftest.py")
    assert checked.pack.sections == (
        Section(file="pyproject.toml", format="toml", name="tool.pytest.ini_options"),
        Section(file="setup.cfg", format="ini", name="tool:pytest"),
    )


def test_a_pack_without_sections_is_read_with_none() -> None:
    checked = seeded(CONFIG, CONFIG)
    assert checked.pack is not None
    assert (checked.pack.config_paths, checked.pack.sections) == (("pytest.ini",), ())


@pytest.mark.parametrize(
    ("old", "new", "code"),
    [
        ("format: toml", "format: yaml", "unknown-value"),
        ("      section: tool.pytest.ini_options\n", "", "missing-field"),
        ("      format: toml\n", "      format: toml\n      key: x\n", "unknown-field"),
        (
            'config: ["pytest.ini", ".pytest.ini", "conftest.py"]',
            "config: pytest.ini",
            "wrong-type",
        ),
        ('section: "tool:pytest"', 'section: "a\\nb"', "wrong-type"),
    ],
)
def test_a_section_that_does_not_fit_its_table_is_found(old: str, new: str, code: str) -> None:
    text = WITH.replace(old, new)
    assert text != WITH
    only(seeded(CONFIG, text), code)


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ('".pytest.ini"', '"/etc/pytest.ini"'),
        ('".pytest.ini"', '"../pytest.ini"'),
        ("file: setup.cfg", "file: ../setup.cfg"),
        ("file: pyproject.toml", "file: /pyproject.toml"),
    ],
)
def test_a_configuration_outside_the_project_is_found(old: str, new: str) -> None:
    only(seeded(CONFIG, WITH.replace(old, new)), "path-outside-project")


def test_a_configuration_path_is_neither_a_test_nor_code() -> None:
    checked = seeded(CONFIG, WITH)
    assert checked.pack is not None
    pack = checked.pack
    assert (
        pack.is_test("pytest.ini"),
        pack.is_config("pytest.ini"),
        pack.is_code("pytest.ini"),
    ) == (
        False,
        True,
        False,
    )
    assert (pack.is_config("src/a.py"), pack.is_code("src/a.py")) == (False, True)
    assert (pack.is_config("tests/conftest.py"), pack.is_test("tests/conftest.py")) == (False, True)


def test_a_pack_without_the_configuration_of_its_tests_is_found_naming_it() -> None:
    finding = only(seeded('  config: ["pytest.ini"]\n', ""), "missing-field")
    assert "config" in finding.message


def test_a_pack_with_an_empty_configuration_is_found() -> None:
    only(seeded('  config: ["pytest.ini"]', "  config: []"), "empty-list")
