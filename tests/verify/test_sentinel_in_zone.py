# SDD-EARS: VERIFY-191 VERIFY-192
from dokime.core.verdicts import Verdict
from tests.verify.gates import codes
from tests.verify.sealed_contracts import IMPOSSIBLE, batch_of, held, run, split

PAIR = (("E-h1", held("E-h1")), ("E-h2", held("E-h2")))
HOLDS: dict[str, object] = {"E-h1": 2, "E-h2": 2}


def sentinel_in_zone(files: dict[str, str | tuple[str, str]]) -> None:
    contract, sealed = split(*PAIR)
    result, observer = run(contract, batch_of(contract, sealed), HOLDS, files=files)
    assert codes(list(result.findings)) == [("sentinel-in-zone", Verdict.ERROR)]
    assert all(IMPOSSIBLE not in found.message for found in result.findings)
    assert observer.calls == []


def test_the_value_in_a_file_of_the_change_is_an_error_and_nothing_is_observed() -> None:
    sentinel_in_zone({"src/q.py": f"EXPECTED = '{IMPOSSIBLE}'\n"})


def test_the_value_in_the_path_of_a_file_is_an_error() -> None:
    sentinel_in_zone({f"src/{IMPOSSIBLE}.txt": "x"})


def test_the_value_as_the_target_of_a_link_is_an_error_and_the_link_is_not_followed() -> None:
    sentinel_in_zone({"src/link": ("->", f"/nowhere/{IMPOSSIBLE}")})


def test_the_value_in_a_file_that_is_not_text_is_an_error() -> None:
    sentinel_in_zone({"data.bin": "\x00\xff" + IMPOSSIBLE})


def test_the_value_in_a_request_is_an_error() -> None:
    leaked = held("E-h1").replace("args: [", f"args: ['{IMPOSSIBLE}', ")
    contract, sealed = split(("E-h1", leaked), ("E-h2", held("E-h2")))
    result, observer = run(contract, batch_of(contract, sealed), HOLDS)
    assert codes(list(result.findings)) == [("sentinel-in-zone", Verdict.ERROR)]
    assert all(IMPOSSIBLE not in found.message for found in result.findings)
    assert observer.calls == []


def test_a_part_of_the_value_is_not_the_value() -> None:
    contract, sealed = split(*PAIR)
    files: dict[str, str | tuple[str, str]] = {"src/q.py": IMPOSSIBLE[:31]}
    result, observer = run(contract, batch_of(contract, sealed), HOLDS, files=files)
    assert result.findings == ()
    assert len(observer.calls) == 1
