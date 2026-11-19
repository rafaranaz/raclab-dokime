"""The recipients of the sealed batches and the port of the sealed store (ADR-0072, ADR-0073).

A file of recipients follows the format of age: one recipient per line, with empty lines and lines
that start with `#` ignored. It holds only X25519 recipients, the type of the identity of ADR-0073:
the Bech32 encoding, with the human-readable part `age`, of a key of 32 bytes, which is `age1` and
58 characters whose checksum holds (BIP-173). A finding never quotes a line, since a line that is
not a recipient may be a secret key pasted by mistake.
"""

import re
from collections.abc import Sequence
from typing import Protocol

from dokime.core.findings import Finding
from dokime.core.verdicts import Verdict

_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
_RECIPIENT = re.compile(rf"age1[{_CHARSET}]{{58}}")
_GENERATOR = (0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3)
_HRP = [ord(c) >> 5 for c in "age"] + [0] + [ord(c) & 31 for c in "age"]
"""The human-readable part `age`, expanded as BIP-173 does before the checksum."""


def read_recipients(text: str) -> tuple[tuple[str, ...], tuple[Finding, ...]]:
    """The recipients of a file of recipients, and the findings of its reading."""
    recipients: list[str] = []
    lines: dict[str, list[int]] = {}
    findings: list[Finding] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if not _is_recipient(line):
            findings.append(
                Finding(
                    code="bad-recipient",
                    message=f"line {number} is not an X25519 recipient of age",
                    verdict=Verdict.ERROR,
                    lines=(number,),
                )
            )
            continue
        if line not in lines:
            recipients.append(line)
        lines.setdefault(line, []).append(number)
    for recipient, numbers in lines.items():
        if len(numbers) > 1:
            findings.append(
                Finding(
                    code="repeated-recipient",
                    message=f"the recipient {recipient} appears more than once",
                    verdict=Verdict.ERROR,
                    lines=tuple(numbers),
                )
            )
    if not recipients and not findings:
        findings.append(
            Finding(
                code="no-recipient",
                message="the file of recipients gives no recipient",
                verdict=Verdict.ERROR,
            )
        )
    return tuple(recipients), tuple(findings)


def _is_recipient(line: str) -> bool:
    """Whether a line is the Bech32 encoding of an X25519 recipient, with its checksum."""
    if _RECIPIENT.fullmatch(line) is None:
        return False
    data = [_CHARSET.index(character) for character in line[4:]]
    return _polymod([*_HRP, *data]) == 1


def _polymod(values: list[int]) -> int:
    """The checksum of Bech32 over the expanded human-readable part and the data (BIP-173)."""
    check = 1
    for value in values:
        top = check >> 25
        check = (check & 0x1FFFFFF) << 5 ^ value
        for bit, generator in enumerate(_GENERATOR):
            if (top >> bit) & 1:
                check ^= generator
    return check


class SealedStore(Protocol):
    """The port of the sealed store. Every operation may raise a `RefusalError`."""

    def seal(self, content: bytes, recipients: Sequence[str]) -> bytes:
        """Encrypt a content for the recipients, and give the sealed bytes."""
        ...

    def open(self, sealed: bytes) -> bytes:
        """Decrypt sealed bytes in memory, and give their content."""
        ...
