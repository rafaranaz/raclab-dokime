# SDD-EARS: CORE-079 CORE-080
import re

import pytest

from dokime.core.runtime import Digest

HEX = "0123456789abcdef" * 4


def test_a_digest_of_sha256_and_64_lowercase_hexadecimal_characters_is_accepted() -> None:
    assert Digest(f"sha256:{HEX}").text == f"sha256:{HEX}"


@pytest.mark.parametrize(
    "text",
    [
        "",
        HEX,
        f"sha256:{HEX[:-1]}",
        f"sha256:{HEX}0",
        f"sha256:{HEX.upper()}",
        f"sha512:{HEX}",
        f"SHA256:{HEX}",
        f" sha256:{HEX}",
        f"sha256:{HEX[:-1]}g",
    ],
)
def test_a_digest_that_is_not_sha256_and_64_lowercase_hexadecimal_is_rejected_quoting_it(
    text: str,
) -> None:
    with pytest.raises(ValueError, match=re.escape(repr(text))):
        Digest(text)
