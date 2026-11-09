# SDD-EARS: REPO-060 REPO-061 REPO-062
from pathlib import Path

from tests.repo.conftest import GitRunner, write
from tools.check_translations import check, header_for, is_documentation, main, source_hash

README = "# Title\n\nEnglish text.\n"


def stamped(source_name: str, source_text: str, body: str = "# Título\n") -> str:
    return f"{header_for(source_name, source_text)}\n{body}"


def test_documentation_is_human_facing_markdown_outside_tooling() -> None:
    assert is_documentation("README.md")
    assert is_documentation("docs/adr/0001-x.md")
    assert not is_documentation("README.es.md")
    assert not is_documentation("docs/requirements/repo.md")
    assert not is_documentation("CLAUDE.md")
    assert not is_documentation(".claude/skills/tdd/SKILL.md")
    assert not is_documentation(".github/pull_request_template.md")
    assert not is_documentation("src/dokime/README.md")


def test_accepts_a_translation_stamped_with_the_current_source() -> None:
    files = {"README.md": README, "README.es.md": stamped("README.md", README)}
    assert check(files) == []


def test_reports_a_missing_translation() -> None:
    findings = check({"README.md": README})
    assert [(f.path, f.message) for f in findings] == [
        ("README.md", "missing Spanish translation README.es.md")
    ]


def test_reports_an_out_of_date_translation_with_the_current_hash() -> None:
    files = {"README.md": README + "More.\n", "README.es.md": stamped("README.md", README)}
    findings = check(files)
    assert len(findings) == 1
    assert "out of date" in findings[0].message
    assert source_hash(README + "More.\n") in findings[0].message


def test_rejects_a_translation_without_source() -> None:
    findings = check({"docs/x.es.md": stamped("x.md", README)})
    assert [f.path for f in findings] == ["docs/x.es.md"]
    assert "no English source" in findings[0].message


def test_rejects_a_translation_without_header() -> None:
    findings = check({"README.md": README, "README.es.md": "# Título\n"})
    assert len(findings) == 1
    assert "header" in findings[0].message


def test_rejects_a_header_naming_another_source() -> None:
    files = {"README.md": README, "README.es.md": stamped("OTHER.md", README)}
    assert any("header" in f.message for f in check(files))


def test_main_checks_tracked_documentation(repo: Path, git: GitRunner) -> None:
    write(repo, "README.md", README)
    write(repo, "README.es.md", stamped("README.md", README))
    git(repo, "add", ".")
    assert main([], root=repo) == 0
    write(repo, "README.md", README + "Changed.\n")
    assert main([], root=repo) == 1
