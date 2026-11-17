# SDD-EARS: PACKS-016 PACKS-022
import pytest

from dokime.packs.model import Section
from tests.packs.packs import only, seeded

PATHS = '  paths: ["tests/**", "src/**/test_*.py"]'
WITH = (
    PATHS
    + """
  config: ["pytest.ini", ".pytest.ini", "conftest.py"]
  sections:
    - file: pyproject.toml
      format: toml
      section: tool.pytest.ini_options
    - file: setup.cfg
      format: ini
      section: "tool:pytest"
"""
)


def test_a_pack_with_the_configuration_and_its_sections_is_read() -> None:
    checked = seeded(PATHS + "\n", WITH)
    assert checked.pack is not None
    assert checked.pack.config_paths == ("pytest.ini", ".pytest.ini", "conftest.py")
    assert checked.pack.sections == (
        Section(file="pyproject.toml", format="toml", name="tool.pytest.ini_options"),
        Section(file="setup.cfg", format="ini", name="tool:pytest"),
    )


def test_a_pack_without_them_is_read_with_none() -> None:
    checked = seeded(PATHS, PATHS)
    assert checked.pack is not None
    assert (checked.pack.config_paths, checked.pack.sections) == ((), ())


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
    only(seeded(PATHS + "\n", text), code)


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
    only(seeded(PATHS + "\n", WITH.replace(old, new)), "path-outside-project")


def test_a_configuration_path_is_neither_a_test_nor_code() -> None:
    checked = seeded(PATHS + "\n", WITH)
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
