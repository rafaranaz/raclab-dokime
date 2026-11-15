# SDD-EARS: PACKS-050 PACKS-060 PACKS-061 PACKS-062 PACKS-063 PACKS-064 PACKS-065 PACKS-066
from pathlib import Path

from dokime.core.verdicts import Verdict
from tests.packs.doubles import CODE, FakeRepository, FakeRuntime
from tests.packs.loops import (
    fixing_commit,
    not_a_witness,
    only_documentation,
    root,
    self_check,
)


def test_the_candidates_are_looked_at_in_the_order_of_the_history(tmp_path: Path) -> None:
    repository = FakeRepository()
    first = fixing_commit(repository, root(repository), "first", 200)
    documentation = only_documentation(repository, first, "docs", 300)
    last = not_a_witness(repository, documentation, "last", 400)
    result = self_check(tmp_path, repository, FakeRuntime(), last)
    assert [c.commit for c in result.candidates] == [last, first]


def test_the_parent_side_has_the_code_of_the_parent_and_the_tests_of_the_commit(
    tmp_path: Path,
) -> None:
    repository = FakeRepository()
    start = root(repository)
    fix = fixing_commit(repository, start, "fix", 200)
    (candidate,) = self_check(tmp_path, repository, FakeRuntime(), fix).candidates
    parent_files = repository.trees[candidate.parent_side.tree]
    assert parent_files[CODE] == b"root"
    assert parent_files["tests/test_fix.py"] == b"expects:fix"
    assert parent_files["tests/test_root.py"] == b"expects:fix"


def test_the_commit_side_has_the_tree_of_the_commit(tmp_path: Path) -> None:
    repository = FakeRepository()
    fix = fixing_commit(repository, root(repository), "fix", 200)
    (candidate,) = self_check(tmp_path, repository, FakeRuntime(), fix).candidates
    assert repository.trees[candidate.commit_side.tree] == repository.commits[fix][2]


def test_the_second_witness_ends_the_loop(tmp_path: Path) -> None:
    repository = FakeRepository()
    one = fixing_commit(repository, root(repository), "one", 200)
    two = fixing_commit(repository, one, "two", 300)
    three = fixing_commit(repository, two, "three", 400)
    runtime = FakeRuntime()
    result = self_check(tmp_path, repository, runtime, three)
    assert [c.commit for c in result.candidates] == [three, two]
    assert (result.findings, len(runtime.runs)) == ((), 4)


def test_ten_candidates_end_the_loop(tmp_path: Path) -> None:
    repository = FakeRepository()
    commit = root(repository)
    for index in range(12):
        commit = not_a_witness(repository, commit, f"n{index}", 200 + index)
    result = self_check(tmp_path, repository, FakeRuntime(), commit)
    assert len(result.candidates) == 10
    assert [f.code for f in result.findings] == ["too-few-witnesses"]


def test_a_finding_with_the_verdict_error_ends_the_loop_with_it(tmp_path: Path) -> None:
    repository = FakeRepository()
    early = fixing_commit(repository, root(repository), "early", 200)
    files = dict(repository.commits[early][2]) | {"ending": b"memory-limit"}
    files[CODE], files["tests/test_late.py"] = b"late", b"expects:late"
    late = repository.add("late", 300, files, early)
    runtime = FakeRuntime()
    result = self_check(tmp_path, repository, runtime, late)
    assert [(f.code, f.verdict) for f in result.findings] == [("run-killed", Verdict.ERROR)]
    assert result.verdict is Verdict.ERROR
    assert result.candidates == ()
    # both sides of the newest candidate ran; the next candidate would have added two more
    assert len(runtime.runs) == 2


def test_a_refusal_of_a_port_ends_the_loop_with_its_finding(tmp_path: Path) -> None:
    repository = FakeRepository(refuse="change")
    fix = fixing_commit(repository, root(repository), "fix", 200)
    runtime = FakeRuntime()
    result = self_check(tmp_path, repository, runtime, fix)
    assert [(f.code, f.verdict) for f in result.findings] == [("unknown-commit", Verdict.ERROR)]
    assert runtime.builds == []


def test_the_dockerfile_is_read_once_from_the_working_copy(tmp_path: Path) -> None:
    repository = FakeRepository()
    one = fixing_commit(repository, root(repository), "one", 200)
    two = fixing_commit(repository, one, "two", 300)

    def change_the_working_copy(project: Path, output: Path) -> None:
        (tmp_path / "pack" / "Dockerfile").write_text("FROM changed-during-the-run\n")

    runtime = FakeRuntime(while_running=change_the_working_copy)
    self_check(tmp_path, repository, runtime, two)
    assert {text for text, _, _ in runtime.builds} == {"FROM the-working-copy\n"}
    assert len(runtime.builds) == 4
