"""The randomness of the system, for the seed of a split, the salts and the canary (ADR-0014).

It comes from `secrets`, the randomness of the operating system, and never from a value that a
person chooses: with a seed of one's own, one could try seeds until the split suits.
"""

import secrets


def random_bytes(count: int) -> bytes:
    """As many random bytes as asked, from the randomness of the system."""
    if count < 1:
        raise ValueError(f"random bytes are asked by the one at least, not {count}")
    return secrets.token_bytes(count)


SEED_BITS = 53
"""The bits of a seed: the largest whole number that the canonical form of ADR-0062 holds is
2**53 - 1, and the seed is written in the sealed batch."""


def seed() -> int:
    """A natural integer of 53 random bits, from the randomness of the system."""
    return secrets.randbits(SEED_BITS)
