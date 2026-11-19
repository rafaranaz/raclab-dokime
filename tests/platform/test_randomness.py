# SDD-EARS: PLATFORM-120 PLATFORM-121 PLATFORM-122
import pytest

from dokime.core.canonical import canonical
from dokime.platform.randomness import random_bytes, seed


@pytest.mark.parametrize("count", [1, 16, 32])
def test_as_many_random_bytes_as_asked(count: int) -> None:
    assert len(random_bytes(count)) == count


def test_random_bytes_differ_from_one_ask_to_the_next() -> None:
    assert len({random_bytes(16) for _ in range(20)}) == 20


def test_a_seed_is_a_natural_integer_that_the_canonical_form_holds() -> None:
    drawn = [seed() for _ in range(200)]
    assert all(isinstance(s, int) and 0 <= s < 2**53 for s in drawn)
    assert len(set(drawn)) == 200
    for value in drawn:
        canonical({"seed": value})


@pytest.mark.parametrize("count", [0, -1])
def test_fewer_than_one_byte_is_refused(count: int) -> None:
    with pytest.raises(ValueError, match=str(count)):
        random_bytes(count)
