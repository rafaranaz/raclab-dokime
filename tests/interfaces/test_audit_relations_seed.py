# SDD-EARS: INTERFACES-186
import pytest

from dokime.interfaces import audit_command


def test_the_seed_of_the_relations_is_drawn_from_the_randomness_of_the_system(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    drawn = iter([11, 12])
    monkeypatch.setattr(audit_command, "seed", lambda: next(drawn))
    assert (audit_command.relations_seed(), audit_command.relations_seed()) == (11, 12)
