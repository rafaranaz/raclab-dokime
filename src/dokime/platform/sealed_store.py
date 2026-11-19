"""The sealed store with age (ADR-0072, ADR-0073).

The adapter of the port `SealedStore` of `core`, and the only module that imports pyrage. It seals
for X25519 recipients of age, which the caller reads from the base, and opens with one identity,
in memory. The identity is an age file encrypted with a passphrase, which the binary `age` reads as
an identity file too: its content is a secret key of age with the comments of `age-keygen`. It is
created with the permissions 0600, never over another file, and loaded with a finding when it is
more open, as ssh warns.

The passphrase comes only from a descriptor that the caller names or from the terminal of the
process without echo. Without both it is an error: `getpass` is not used, since without a terminal
it reads the standard input.
"""

import os
import stat
import termios
from collections.abc import Mapping, Sequence
from pathlib import Path

import pyrage
from pyrage import passphrase as with_passphrase
from pyrage import x25519

from dokime.core.findings import Finding
from dokime.core.repository import RefusalError
from dokime.core.verdicts import Verdict

_AGE = b"age-encryption.org/v1\n"
_IDENTITY = "dokime/identity.age"


class AgeSealedStore:
    """Seals for X25519 recipients of age, and opens with one identity, in memory."""

    def __init__(self, identity: x25519.Identity) -> None:
        self._identity = identity

    def seal(self, content: bytes, recipients: Sequence[str]) -> bytes:
        """Encrypt a content for the recipients, and give the sealed bytes."""
        if not recipients:
            raise RefusalError("bad-recipient", "there is no recipient to seal for")
        parsed = []
        for number, recipient in enumerate(recipients, start=1):
            try:
                parsed.append(x25519.Recipient.from_str(recipient))
            except pyrage.RecipientError:
                raise RefusalError(
                    "bad-recipient", f"the recipient {number} is not an X25519 recipient of age"
                ) from None
        return bytes(pyrage.encrypt(content, parsed))

    def open(self, sealed: bytes) -> bytes:
        """Decrypt sealed bytes in memory, and give their content."""
        if not sealed.startswith(_AGE):
            raise RefusalError("unreadable-batch", "the sealed batch is not a file of age")
        try:
            return bytes(pyrage.decrypt(sealed, [self._identity]))
        except pyrage.DecryptError as error:
            if "No matching keys" in str(error):
                raise RefusalError(
                    "not-a-recipient", "the identity here is not a recipient of the sealed batch"
                ) from None
            raise RefusalError(
                "unreadable-batch", "the sealed batch is not a file of age that opens"
            ) from None


def create_identity(path: Path, passphrase: str) -> str:
    """Write a new identity encrypted with a passphrase, and give its recipient."""
    if not passphrase:
        raise RefusalError("empty-passphrase", "the passphrase of a new identity is empty")
    if path.exists() or path.is_symlink():
        raise RefusalError("identity-exists", f"there is already a file at {path}")
    _directories(path.parent)
    identity = x25519.Identity.generate()
    recipient = str(identity.to_public())
    text = f"# created by dokime\n# public key: {recipient}\n{identity}\n"
    sealed = bytes(with_passphrase.encrypt(text.encode(), passphrase))
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        view = memoryview(sealed)
        while view:
            view = view[os.write(descriptor, view) :]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return recipient


def _directories(directory: Path) -> None:
    """Make the directories that are missing, each with the permissions 0700."""
    missing = []
    while not directory.exists():
        missing.append(directory)
        directory = directory.parent
    for made in reversed(missing):
        made.mkdir(mode=0o700)
        made.chmod(0o700)


def load_identity(path: Path, passphrase: str) -> tuple[AgeSealedStore, tuple[Finding, ...]]:
    """Load an identity with its passphrase, and give the store that opens with it."""
    try:
        data = path.read_bytes()
        permissions = stat.S_IMODE(path.stat().st_mode)
    except FileNotFoundError:
        raise RefusalError("no-identity", f"there is no identity at {path}") from None
    try:
        text = bytes(with_passphrase.decrypt(data, passphrase)).decode()
    except (pyrage.DecryptError, UnicodeDecodeError):
        raise RefusalError(
            "wrong-passphrase", "the passphrase does not open the identity"
        ) from None
    keys = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]
    try:
        (key,) = keys
        identity = x25519.Identity.from_str(key)
    except (ValueError, pyrage.IdentityError):
        raise RefusalError(
            "bad-identity", "the identity does not hold exactly one secret key of age"
        ) from None
    findings: tuple[Finding, ...] = ()
    if permissions & 0o077:
        findings = (
            Finding(
                code="open-identity",
                message=f"the identity at {path} has the permissions {permissions:o}, not 600",
                verdict=Verdict.ASK,
            ),
        )
    return AgeSealedStore(identity), findings


def default_identity_path(environ: Mapping[str, str]) -> Path:
    """The path of the identity when none is given."""
    data = environ.get("XDG_DATA_HOME", "")
    base = Path(data) if data else Path(environ.get("HOME", "~")) / ".local" / "share"
    return base / _IDENTITY


def read_passphrase(descriptor: int | None, terminal: str = "/dev/tty") -> str:
    """The passphrase, from a descriptor or from the terminal without echo."""
    if descriptor is not None:
        return _line(descriptor).decode()
    try:
        tty = os.open(terminal, os.O_RDWR | os.O_NOCTTY)
    except OSError:
        raise RefusalError(
            "no-passphrase-source",
            "there is no terminal to type the passphrase and no descriptor was given",
        ) from None
    try:
        before = termios.tcgetattr(tty)
        quiet = list(before)
        quiet[3] &= ~termios.ECHO
        termios.tcsetattr(tty, termios.TCSAFLUSH, quiet)
        try:
            os.write(tty, b"passphrase of the identity: ")
            return _line(tty).decode()
        finally:
            termios.tcsetattr(tty, termios.TCSAFLUSH, before)
            os.write(tty, b"\n")
    finally:
        os.close(tty)


def _line(descriptor: int) -> bytes:
    """The bytes of a descriptor up to its first newline, without it, or up to its end."""
    read = bytearray()
    while True:
        byte = os.read(descriptor, 1)
        if not byte or byte == b"\n":
            return bytes(read)
        read += byte
