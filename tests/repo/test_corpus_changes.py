# SDD-EARS: REPO-169 REPO-170 REPO-171 REPO-172 REPO-173
import subprocess
from pathlib import Path

import pytest

from tools import corpus_changes
from tools.corpus_changes import changed_files, runs


@pytest.mark.parametrize(
    ("files", "expected"),
    [
        (["docs/ROADMAP.md", "docs/adr/0077-x.es.md"], False),
        (["docs/requirements/repo.md"], True),
        (["docs/ROADMAP.md", "tools/x.py"], True),
        (["README.md"], True),
        (["docs/architecture/diagram.mmd"], True),
        (["tests/corpus/README.md"], True),
        ([], True),
    ],
)
def test_the_corpus_runs_unless_every_file_is_text_under_docs(
    files: list[str], expected: bool
) -> None:
    assert runs(files) is expected


def git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repository), *arguments], capture_output=True, text=True, check=True
    ).stdout.strip()


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.email", "t@example.org")
    git(tmp_path, "config", "user.name", "t")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.md").write_text("a test that is long enough to be a rename\n" * 5)
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "base")
    return tmp_path


def test_a_file_moved_names_both_of_its_paths(repository: Path) -> None:
    base = git(repository, "rev-parse", "HEAD")
    (repository / "docs").mkdir()
    git(repository, "mv", "tests/test_x.md", "docs/test_x.md")
    git(repository, "commit", "-q", "-m", "move")
    files = changed_files(repository, base, "HEAD")
    assert sorted(files) == ["docs/test_x.md", "tests/test_x.md"]
    assert runs(files)


def decide(repository: Path, tmp_path: Path, *arguments: str) -> tuple[str, str]:
    output, summary = tmp_path / "output", tmp_path / "summary"
    code = corpus_changes.main(
        [
            "--repository",
            str(repository),
            "--output",
            str(output),
            "--summary",
            str(summary),
            *arguments,
        ]
    )
    assert code == 0
    return output.read_text(), summary.read_text()


def test_a_pull_request_of_text_does_not_run_the_corpus_and_lists_its_files(
    repository: Path, tmp_path: Path
) -> None:
    base = git(repository, "rev-parse", "HEAD")
    (repository / "docs").mkdir()
    (repository / "docs" / "NOTE.md").write_text("a note\n")
    git(repository, "add", ".")
    git(repository, "commit", "-q", "-m", "note")
    output, summary = decide(
        repository, tmp_path, "--event", "pull_request", "--base", base, "--head", "HEAD"
    )
    assert output == "run=false\n"
    assert "the corpus did not run: the pull request only changes text" in summary
    assert "docs/NOTE.md" in summary


def test_files_that_cannot_be_listed_run_the_corpus_and_say_why(
    repository: Path, tmp_path: Path
) -> None:
    output, summary = decide(
        repository, tmp_path, "--event", "pull_request", "--base", "0" * 40, "--head", "HEAD"
    )
    assert output == "run=true\n"
    assert "cannot be listed" in summary


def test_an_event_that_is_not_a_pull_request_runs_the_corpus(
    repository: Path, tmp_path: Path
) -> None:
    output, _ = decide(repository, tmp_path, "--event", "push", "--base", "", "--head", "HEAD")
    assert output == "run=true\n"
