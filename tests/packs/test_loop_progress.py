# SDD-EARS: PACKS-073
from pathlib import Path

from dokime.packs.loop import Candidate, run_self_check
from tests.packs.doubles import FakeRepository, FakeRuntime, pack
from tests.packs.loops import PROGRAMS, dockerfile, fixing_commit, not_a_witness, root


def test_each_candidate_is_given_to_the_caller_before_the_next_one_runs(tmp_path: Path) -> None:
    repository = FakeRepository()
    one = fixing_commit(repository, root(repository), "one", 200)
    two = not_a_witness(repository, one, "two", 300)
    three = fixing_commit(repository, two, "three", 400)
    runtime = FakeRuntime()
    given: list[tuple[Candidate, int]] = []

    def note(candidate: Candidate) -> None:
        given.append((candidate, len(runtime.runs)))

    result = run_self_check(
        pack(), dockerfile(tmp_path), three, repository, runtime, PROGRAMS, on_candidate=note
    )
    assert [candidate for candidate, _ in given] == list(result.candidates)
    assert [candidate.commit for candidate, _ in given] == [three, two, one]
    assert [runs for _, runs in given] == [2, 4, 6]


def test_a_candidate_cut_short_by_an_error_is_not_given(tmp_path: Path) -> None:
    repository = FakeRepository()
    start = root(repository)
    files = dict(repository.commits[start][2])
    files |= {"ending": b"time-limit", "src/code.py": b"x", "tests/test_x.py": b"expects:x"}
    killed = repository.add("killed", 200, files, start)
    given: list[Candidate] = []
    run_self_check(
        pack(), dockerfile(tmp_path), killed, repository, FakeRuntime(), PROGRAMS, given.append
    )
    assert given == []
