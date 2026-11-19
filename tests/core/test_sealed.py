# SDD-EARS: CORE-172 CORE-173 CORE-180 CORE-181 CORE-182 CORE-183 CORE-184 CORE-185
from collections.abc import Sequence
from pathlib import PurePosixPath

import pytest

from dokime.core.layout import RECIPIENTS, sealed_path
from dokime.core.repository import RefusalError
from dokime.core.sealed import SealedStore, read_recipients
from dokime.core.verdicts import Verdict

# The example of an X25519 recipient in the specification of age.
ALICE = "age1zvkyg2lqzraa2lnjvqej32nkuu0ues2s82hzrye869xeexvn73equnujwj"
BOB = "age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p"


def test_the_recipients_are_in_the_directory_of_the_harness() -> None:
    assert PurePosixPath(".dokime/recipients.txt") == RECIPIENTS


def test_the_sealed_batch_is_in_the_directory_of_the_change() -> None:
    assert sealed_path("invoice-rounding") == PurePosixPath(
        ".dokime/changes/invoice-rounding/sealed.age"
    )


def test_the_recipients_are_the_lines_that_are_not_empty_nor_comments() -> None:
    text = f"# the maintainer\n{ALICE}\n\n  {BOB}  \n# a second recipient\n"
    assert read_recipients(text) == ((ALICE, BOB), ())


@pytest.mark.parametrize(
    "line",
    [
        "age1pqx34nzsvr0rxjsgdn8zgyhfe8j7ceq5r9rdelkjuh3y235jzxshfg87pzf5zrq",
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl",
        ALICE[:-1],
        ALICE + "q",
        ALICE.upper(),
        "age1zvkyg2lqzraa2lnjvqej32nkuu0ues2s82hzrye869xeexvn73equnujwb",
        "AGE-SECRET-KEY-1GFPYYSJZGFPYYSJZGFPYYSJZGFPYYSJZGFPYYSJZGFPYYSJZGFPQ4EGAEX",
    ],
)
def test_a_line_that_is_not_an_x25519_recipient_is_reported_without_its_text(line: str) -> None:
    recipients, findings = read_recipients(f"{ALICE}\n{line}\n")
    assert recipients == (ALICE,)
    (finding,) = findings
    assert (finding.code, finding.verdict, finding.lines) == ("bad-recipient", Verdict.ERROR, (2,))
    assert line not in finding.message


@pytest.mark.parametrize("text", ["", "\n\n", "# only a comment\n"])
def test_a_file_without_recipients_is_reported(text: str) -> None:
    recipients, findings = read_recipients(text)
    assert recipients == ()
    assert [(f.code, f.verdict) for f in findings] == [("no-recipient", Verdict.ERROR)]


def test_a_repeated_recipient_is_reported_with_its_lines() -> None:
    recipients, findings = read_recipients(f"{ALICE}\n{BOB}\n{ALICE}\n")
    assert recipients == (ALICE, BOB)
    (finding,) = findings
    assert (finding.code, finding.verdict, finding.lines) == (
        "repeated-recipient",
        Verdict.ERROR,
        (1, 3),
    )


def test_the_port_offers_two_operations_seal_and_open() -> None:
    public = {name for name in vars(SealedStore) if not name.startswith("_")}
    assert public == {"seal", "open"}


class Refusing:
    """A store that refuses every operation, as the port allows."""

    def seal(self, content: bytes, recipients: Sequence[str]) -> bytes:
        raise RefusalError("not-a-recipient", "no recipient of the batch is here")

    def open(self, sealed: bytes) -> bytes:
        raise RefusalError("wrong-passphrase", "the identity does not open with it")


def test_a_refusal_of_the_store_carries_an_error() -> None:
    store: SealedStore = Refusing()
    with pytest.raises(RefusalError) as refused:
        store.open(b"x")
    assert refused.value.finding.verdict is Verdict.ERROR
