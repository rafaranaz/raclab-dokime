"""The order of the history in which the self-check looks for candidates (ADR-0044).

No commit comes before a commit that descends from it. Among the commits that can come next, the
one with the later commit date goes first, and on equal dates the one that became able to come
next earlier. A commit becomes able when every commit that descends from it has been placed; the
parents of a commit become able in the order the commit names them. Commits without exactly one
parent are left out at the end, so that they still take part in the order.
"""

import heapq
from collections.abc import Iterable

from dokime.core.repository import CommitName, HistoryCommit


def order_history(history: Iterable[HistoryCommit]) -> tuple[HistoryCommit, ...]:
    """Order a history from its newest commit, without the commits that lack exactly one parent."""
    by_name = {commit.name: commit for commit in history}
    children: dict[CommitName, int] = dict.fromkeys(by_name, 0)
    for commit in by_name.values():
        for parent in commit.parents:
            if parent in children:
                children[parent] += 1
    able: list[tuple[int, int, str]] = []
    became_able = 0
    for name in sorted((n for n, count in children.items() if count == 0), key=lambda n: n.text):
        heapq.heappush(able, (-by_name[name].date, became_able, name.text))
        became_able += 1
    placed: list[HistoryCommit] = []
    while able:
        _, _, text = heapq.heappop(able)
        commit = by_name[CommitName(text)]
        placed.append(commit)
        for parent in commit.parents:
            if parent not in children:
                continue
            children[parent] -= 1
            if children[parent] == 0:
                heapq.heappush(able, (-by_name[parent].date, became_able, parent.text))
                became_able += 1
    return tuple(commit for commit in placed if len(commit.parents) == 1)
