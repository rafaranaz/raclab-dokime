"""Turn examples of a dokime contract into black-box checks that swarm-verify can run (R2, S2)."""

from pathlib import Path


class ConversionError(Exception):
    """The conversion refused: the message says why, and nothing was written."""


def convert(contract_text: str, ids: list[str], out: Path) -> None:
    """Write into `out` the checks of the examples `ids` of the contract."""
