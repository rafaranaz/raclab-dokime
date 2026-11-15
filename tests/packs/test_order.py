# SDD-EARS: PACKS-040 PACKS-041 PACKS-042 PACKS-043
import hashlib
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from dokime.core.repository import CommitName, HistoryCommit
from dokime.packs.order import order_history

HEX = re.compile(r"[0-9a-f]{40}")
SHORT: dict[str, str] = {}


def full(name: str) -> CommitName:
    """A commit name for a short name of a test, or the name itself when it is already one."""
    if HEX.fullmatch(name):
        return CommitName(name)
    text = hashlib.sha1(name.encode(), usedforsecurity=False).hexdigest()
    SHORT[text] = name
    return CommitName(text)


def commit(name: str, date: int, *parents: str) -> HistoryCommit:
    return HistoryCommit(name=full(name), date=date, parents=tuple(full(p) for p in parents))


def names(history: tuple[HistoryCommit, ...]) -> list[str]:
    return [SHORT.get(c.name.text, c.name.text) for c in history]


def test_the_example_of_adr_0044_breaks_equal_dates_by_when_each_became_able() -> None:
    history = [
        commit("R", 900),
        commit("C", 1000, "R"),
        commit("B", 1000, "R"),
        commit("A", 1000, "C"),
        commit("D", 1000, "A", "B"),
    ]
    history = [history[i] for i in (3, 0, 4, 2, 1)]
    assert names(order_history(history)) == ["A", "B", "C"]


def test_no_commit_comes_before_one_that_descends_from_it_even_when_older() -> None:
    history = [
        commit("old-child", 100, "parent"),
        commit("parent", 500, "root"),
        commit("root", 50),
    ]
    assert names(order_history(history)) == ["old-child", "parent"]


def test_of_two_commits_that_can_come_next_the_later_one_goes_first() -> None:
    history = [
        commit("root", 10),
        commit("base", 20, "root"),
        commit("early", 30, "base"),
        commit("late", 40, "base"),
        commit("merge", 50, "early", "late"),
    ]
    assert names(order_history(history)) == ["late", "early", "base"]


def test_a_commit_without_exactly_one_parent_is_left_out() -> None:
    history = [
        commit("root", 10),
        commit("other-root", 15),
        commit("one", 20, "root"),
        commit("merge", 30, "one", "other-root"),
        commit("octopus", 40, "merge", "root", "other-root"),
    ]
    assert names(order_history(history)) == ["one"]


def git(directory: Path, *args: str, env: dict[str, str] | None = None) -> str:
    done = subprocess.run(
        ["git", "-C", str(directory), *args], capture_output=True, text=True, check=True, env=env
    )
    return done.stdout.strip()


def identity(date: int) -> dict[str, str]:
    return {
        **os.environ,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.com",
        "GIT_AUTHOR_DATE": f"{date} +0000",
        "GIT_COMMITTER_DATE": f"{date} +0000",
    }


class Numbers:
    """A fixed sequence of numbers from a seed, so that each generated history is the same."""

    def __init__(self, seed: int) -> None:
        self.state = seed + 1

    def below(self, limit: int) -> int:
        self.state = (self.state * 1103515245 + 12345) % 2**31
        return self.state % limit


def random_repository(directory: Path, seed: int) -> str:
    """A repository of merges and equal dates, built with commit-tree and fixed dates."""
    numbers = Numbers(seed)
    git(directory, "init", "-q")
    tree = git(directory, "write-tree")
    made: list[str] = []
    for index in range(41):
        count = 1 if numbers.below(4) else 2
        chosen = {made[numbers.below(len(made))] for _ in range(count)} if made else set()
        parents = made[-3:] if index == 40 else sorted(chosen)
        date = 1_700_000_000 + numbers.below(12) * 60
        arguments = ["commit-tree", tree, "-m", str(index)]
        for parent in parents:
            arguments += ["-p", parent]
        made.append(git(directory, *arguments, env=identity(date)))
    return made[-1]


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
@pytest.mark.parametrize("seed", range(6))
def test_the_order_is_the_one_of_git_rev_list_date_order_without_merges_and_roots(
    tmp_path: Path, seed: int
) -> None:
    tip = random_repository(tmp_path, seed)
    listed = git(tmp_path, "log", "--format=%H %ct %P", tip).splitlines()
    history = [
        commit(fields[0], int(fields[1]), *fields[2:])
        for fields in (line.split() for line in listed)
    ]
    expected = [
        name
        for name in git(tmp_path, "rev-list", "--date-order", "--no-merges", tip).splitlines()
        if git(tmp_path, "rev-list", "--parents", "-n", "1", name).count(" ") == 1
    ]
    assert names(order_history(history)) == expected
