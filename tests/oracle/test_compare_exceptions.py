# SDD-EARS: ORACLE-020 ORACLE-021 ORACLE-022 ORACLE-023
import pytest

from dokime.contract.expectations import Contains, Expected
from dokime.core.observation import Raised
from dokime.oracle.compare import compare
from tests.oracle.examples import example, observed, raised

PYTHON = raised("builtins", "TypeError", "builtins.Exception")
SUBCLASS = raised("semver.errors", "BadPart", "builtins.TypeError", "builtins.Exception")
IMPOSTOR = raised("semver.errors", "TypeError", "builtins.Exception")


def holds(expected: str, exception: Raised, message: Expected = None) -> bool:
    expect: dict[str, Expected] = {"type": expected}
    if message is not None:
        expect["message"] = message
    return compare(example("function", {"raises": expect}), observed(exception)).holds


def test_a_type_without_a_module_is_read_as_the_class_of_builtins() -> None:
    assert holds("TypeError", PYTHON)
    assert not holds("TypeError", IMPOSTOR)


def test_a_type_with_a_module_is_read_as_its_full_name() -> None:
    assert holds("semver.errors.TypeError", IMPOSTOR)
    assert not holds("semver.errors.TypeError", PYTHON)
    assert holds("semver.errors.BadPart", SUBCLASS)


@pytest.mark.parametrize(
    ("expected", "exception", "held"),
    [
        ("TypeError", SUBCLASS, True),
        ("Exception", PYTHON, True),
        ("Exception", IMPOSTOR, True),
        ("ValueError", PYTHON, False),
        ("BaseException", SUBCLASS, True),
    ],
)
def test_a_type_holds_for_any_class_of_the_mro_observed(
    expected: str, exception: Raised, held: bool
) -> None:
    assert holds(expected, exception) is held


def test_a_message_has_to_hold_as_well() -> None:
    exception = raised("builtins", "TypeError", "builtins.Exception", message="not 'NoneType'")
    assert holds("TypeError", exception, Contains("NoneType"))
    assert holds("TypeError", exception, "not 'NoneType'")
    assert not holds("TypeError", exception, Contains("int"))


def test_an_expected_exception_that_is_not_a_mapping_is_an_error_of_the_caller() -> None:
    with pytest.raises(TypeError, match="mapping"):
        compare(example("function", {"raises": "TypeError"}), observed(PYTHON))
