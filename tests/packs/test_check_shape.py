# SDD-EARS: PACKS-010 PACKS-011 PACKS-012 PACKS-013 PACKS-014 PACKS-015
import pytest

from dokime.packs.check import check
from tests.packs.packs import line_of, only, seeded


@pytest.mark.parametrize("text", ["- a\n", "just a text\n", "7\n"])
def test_a_pack_that_is_not_a_mapping_is_one_finding_and_nothing_else(text: str) -> None:
    assert only(check(text), "wrong-type").lines == (1,)


@pytest.mark.parametrize(
    ("old", "new", "code", "line"),
    [
        ("name: cachetools", "name: cachetools\nlevel: P1", "unknown-field", 3),
        ("  dockerfile: Dockerfile", "  dockerfile: Dockerfile\n  image: x", "unknown-field", 5),
        ("  report: report.xml", "  report: report.xml\n  shell: bash", "unknown-field", 8),
        ("name: cachetools\n", "", "missing-field", 1),
        ("  dockerfile: Dockerfile\n", "  {}\n", "missing-field", 3),
        ("  report: report.xml\n", "", "missing-field", 5),
        ("format: 1", 'format: "1"', "unknown-value", 1),
        ("name: cachetools", "name: cache tools", "wrong-type", 2),
        ("environment:\n  dockerfile: Dockerfile", "environment: Dockerfile", "wrong-type", 3),
        ("  dockerfile: Dockerfile", '  dockerfile: "a\\nb"', "wrong-type", 4),
        ("  report: report.xml", "  report: [a]", "wrong-type", 7),
        ("--junitxml, /dokime/out/report.xml]", "--junitxml, 3]", "wrong-type", 6),
        ('  paths: ["tests/**", "src/**/test_*.py"]', "  paths: tests", "wrong-type", 8),
        (
            "  command: [python, -m, pytest, --junitxml, /dokime/out/report.xml]",
            "  command: python -m pytest",
            "wrong-type",
            6,
        ),
    ],
)
def test_a_mapping_that_does_not_fit_the_table_gives_the_finding_of_the_shape_check(
    old: str, new: str, code: str, line: int
) -> None:
    assert only(seeded(old, new), code).lines == (line,)


def test_an_empty_test_command_is_a_finding() -> None:
    old = "[python, -m, pytest, --junitxml, /dokime/out/report.xml]"
    assert only(seeded(old, "[]"), "empty-list").lines == (line_of(old),)


def test_an_empty_list_of_test_paths_is_a_finding() -> None:
    old = '["tests/**", "src/**/test_*.py"]'
    assert only(seeded(old, "[]"), "empty-list").lines == (line_of(old),)


@pytest.mark.parametrize("path", ["/etc/Dockerfile", "../Dockerfile", "docker/../../Dockerfile"])
def test_a_dockerfile_outside_the_directory_of_the_pack_is_a_finding(path: str) -> None:
    checked = seeded("dockerfile: Dockerfile", f"dockerfile: {path}")
    assert only(checked, "path-outside-pack").lines == (4,)


@pytest.mark.parametrize("path", ["/var/report.xml", "../report.xml"])
def test_a_report_outside_the_output_directory_is_a_finding(path: str) -> None:
    assert only(seeded("report: report.xml", f"report: {path}"), "path-outside-output").lines == (
        7,
    )


@pytest.mark.parametrize("pattern", ["/tests/**", "../tests/**", "tests/../../x"])
def test_a_test_pattern_outside_the_project_is_a_finding(pattern: str) -> None:
    checked = seeded('"tests/**"', f'"{pattern}"')
    assert only(checked, "path-outside-project").lines == (8,)


def test_a_path_inside_a_directory_is_accepted() -> None:
    checked = seeded("dockerfile: Dockerfile", "dockerfile: docker/test.Dockerfile")
    assert checked.findings == ()
    assert checked.pack is not None
    assert checked.pack.dockerfile == "docker/test.Dockerfile"


def test_tests_that_are_not_a_mapping_are_one_finding() -> None:
    text = "format: 1\nname: x\nenvironment: {dockerfile: Dockerfile}\ntests: none\n"
    assert only(check(text), "wrong-type").lines == (4,)
