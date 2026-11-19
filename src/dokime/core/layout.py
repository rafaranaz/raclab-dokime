"""Where the files of the harness are in a project (ADR-0027, ADR-0054).

The paths are relative to the root of the project; `core` gives them and opens nothing.
"""

import re
from pathlib import PurePosixPath

HARNESS = PurePosixPath(".dokime")
POLICY = HARNESS / "policy.yaml"
CHANGES = HARNESS / "changes"
CONTRACT = "contract.yaml"
RECIPIENTS = HARNESS / "recipients.txt"
SEALED = "sealed.age"

_NAME = re.compile(r"[A-Za-z][A-Za-z0-9]*(-[A-Za-z0-9]+)*")
"""A name, as the `story` of a contract: letters, digits and hyphens, starting with a letter."""


def change_directory(story: str) -> PurePosixPath:
    """The directory of the change of a story."""
    if _NAME.fullmatch(story) is None:
        raise ValueError(
            f"the story {story!r} is not a name:"
            " letters, digits and hyphens, starting with a letter"
        )
    return CHANGES / story


def contract_path(story: str) -> PurePosixPath:
    """The contract of the change of a story."""
    return change_directory(story) / CONTRACT


def sealed_path(story: str) -> PurePosixPath:
    """The sealed batch of the change of a story."""
    return change_directory(story) / SEALED
