# SDD-EARS: INTERFACES-060 INTERFACES-061 INTERFACES-062 INTERFACES-063 INTERFACES-064
import json
from pathlib import Path

import pytest

from tests.interfaces.envs import env_check, use_doubles, write_pack
from tests.packs.doubles import BASE, FakeRepository, FakeRuntime
from tests.packs.loops import fixing_commit, not_a_witness, root


def test_the_programs_are_written_before_the_self_check_starts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "project"
    write_pack(project / ".dokime")
    repository = FakeRepository()
    one = fixing_commit(repository, root(repository), "one", 200)
    seen: list[str] = []

    def look(project_dir: Path, output: Path) -> None:
        seen.append(capsys.readouterr().out)

    use_doubles(monkeypatch, repository, FakeRuntime(while_running=look))
    env_check(capsys, one, "--project", str(project))
    assert seen[0].splitlines() == [
        "program git /usr/bin/git 2.47.3",
        "program podman /usr/bin/podman 5.4.2",
    ]


def test_each_candidate_is_written_with_its_commit_whether_it_is_a_witness_and_its_tests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "project"
    write_pack(project / ".dokime")
    repository = FakeRepository()
    one = fixing_commit(repository, root(repository), "one", 200)
    two = not_a_witness(repository, one, "two", 300)
    use_doubles(monkeypatch, repository, FakeRuntime())
    run = env_check(capsys, two, "--project", str(project))
    assert run.lines[2:4] == [
        f"candidate {two.text}: not a witness",
        f"candidate {one.text}: witness: tests/test_one.py, tests/test_root.py",
    ]


def test_the_line_of_a_candidate_is_written_before_the_next_candidate_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "project"
    write_pack(project / ".dokime")
    repository = FakeRepository()
    one = fixing_commit(repository, root(repository), "one", 200)
    two = not_a_witness(repository, one, "two", 300)
    written: list[str] = []

    def look(project_dir: Path, output: Path) -> None:
        written.append(capsys.readouterr().out)

    use_doubles(monkeypatch, repository, FakeRuntime(while_running=look))
    env_check(capsys, two, "--project", str(project))
    so_far = "".join(written[:3])
    assert f"candidate {two.text}: not a witness" in so_far
    assert one.text not in so_far


def test_a_finding_is_written_with_the_file_of_the_pack_and_the_verdict_ends_the_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "project"
    pack = write_pack(project / ".dokime")
    repository = FakeRepository()
    one = fixing_commit(repository, root(repository), "one", 200)
    use_doubles(monkeypatch, repository, FakeRuntime())
    run = env_check(capsys, one, "--project", str(project))
    assert run.lines[-2].startswith(f"{pack}: FAIL too-few-witnesses: 1 of 1 candidates")
    assert run.lines[-1] == "FAIL: 1 finding (1 fail)"
    assert run.code == 1


def test_two_witnesses_pass_with_no_findings_and_exit_0(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "project"
    write_pack(project / ".dokime")
    repository = FakeRepository()
    one = fixing_commit(repository, root(repository), "one", 200)
    two = fixing_commit(repository, one, "two", 300)
    use_doubles(monkeypatch, repository, FakeRuntime())
    run = env_check(capsys, two, "--project", str(project))
    assert (run.code, run.lines[-1]) == (0, "PASS: no findings")


def test_a_killed_run_is_an_error_and_exits_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "project"
    pack = write_pack(project / ".dokime")
    repository = FakeRepository()
    start = root(repository)
    files = dict(repository.commits[start][2])
    files |= {"ending": b"time-limit", "src/code.py": b"x", "tests/test_x.py": b"expects:x"}
    killed = repository.add("killed", 200, files, start)
    use_doubles(monkeypatch, repository, FakeRuntime())
    run = env_check(capsys, killed, "--project", str(project))
    assert run.code == 2
    assert run.lines[-2].startswith(f"{pack}: ERROR run-killed:")


def test_the_json_document_has_the_pack_the_verdict_the_programs_and_the_candidates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "project"
    pack = write_pack(project / ".dokime")
    repository = FakeRepository()
    one = fixing_commit(repository, root(repository), "one", 200)
    use_doubles(monkeypatch, repository, FakeRuntime())
    run = env_check(capsys, one, "--project", str(project), "--format", "json")
    document = json.loads(run.out)
    assert (document["pack"], document["verdict"]) == (str(pack), "FAIL")
    assert document["programs"][0] == {"name": "git", "path": "/usr/bin/git", "version": "2.47.3"}
    (candidate,) = document["candidates"]
    assert candidate["commit"] == one.text
    assert candidate["witness"] is True
    assert candidate["turned_green"] == ["tests/test_one.py", "tests/test_root.py"]
    for side in ("parent_side", "commit_side"):
        assert set(candidate[side]) == {"tree", "image", "base"}
        assert candidate[side]["base"] == BASE.platform.text
    assert [f["code"] for f in document["findings"]] == ["too-few-witnesses"]
