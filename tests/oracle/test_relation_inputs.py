# SDD-EARS: ORACLE-055 ORACLE-056 ORACLE-057 ORACLE-058 ORACLE-059
import pytest

from dokime.core.observation import Exited, Raised, Returned
from dokime.oracle.relations import in_order, items_of, repeated

RAISED = Raised(
    type="ValueError",
    qualified="builtins.ValueError",
    classes=("builtins.ValueError", "builtins.Exception", "builtins.object"),
    message="no",
)


def test_at_function_the_list_of_the_argument_named_is_permuted() -> None:
    given = {"args": [[1, 2, 3], "x"], "kwargs": {"key": [4, 5]}}
    assert items_of("function", given, "args[0]") == [1, 2, 3]
    assert items_of("function", given, "key") == [4, 5]
    assert in_order("function", given, "args[0]", (2, 0, 1)) == {
        "args": [[3, 1, 2], "x"],
        "kwargs": {"key": [4, 5]},
    }
    assert in_order("function", given, "key", (1, 0)) == {
        "args": [[1, 2, 3], "x"],
        "kwargs": {"key": [5, 4]},
    }
    assert given == {"args": [[1, 2, 3], "x"], "kwargs": {"key": [4, 5]}}


def test_at_cli_the_lines_of_stdin_or_of_a_file_are_permuted() -> None:
    given = {"args": ["sort"], "stdin": "b\na\nc\n", "files": {"in.txt": "1\n2"}}
    assert items_of("cli", given, "stdin") == ["b", "a", "c"]
    assert in_order("cli", given, "stdin", (2, 1, 0))["stdin"] == "c\na\nb\n"
    assert items_of("cli", given, "in.txt") == ["1", "2"]
    assert in_order("cli", given, "in.txt", (1, 0))["files"] == {"in.txt": "2\n1"}


@pytest.mark.parametrize(
    ("boundary", "given", "over"),
    [
        ("function", {"args": ["text"]}, "args[0]"),
        ("function", {"args": [[1]]}, "args[1]"),
        ("function", {"args": [[1]]}, "absent"),
        ("cli", {"args": []}, "stdin"),
        ("cli", {"files": {"a": "x"}}, "b"),
    ],
)
def test_an_input_that_is_absent_or_not_a_list_or_a_text_gives_nothing(
    boundary: str, given: dict[str, object], over: str
) -> None:
    assert items_of(boundary, given, over) is None


def test_idempotent_at_function_puts_the_return_in_the_argument_named() -> None:
    given = {"args": ["  a  ", 2], "kwargs": {"strip": True}}
    assert repeated("function", given, Returned("a"), "args[0]", None) == {
        "args": ["a", 2],
        "kwargs": {"strip": True},
    }
    assert repeated("function", {"args": ["x"]}, Returned("y"), None, None) == {"args": ["y"]}
    assert repeated("function", {"kwargs": {"t": "x"}}, Returned("y"), None, None) == {
        "kwargs": {"t": "y"}
    }


def test_idempotent_at_cli_puts_the_output_back_through_its_channel() -> None:
    given = {"args": ["fmt"], "stdin": "a  b\n", "files": {"doc.md": "# x"}}
    out = Exited(exit=0, stdout="a b\n", stderr="", files={"doc.md": "# x\n", "new.md": "n"})
    assert repeated("cli", given, out, None, "stdout") == {
        "args": ["fmt"],
        "stdin": "a b\n",
        "files": {"doc.md": "# x"},
    }
    assert repeated("cli", given, out, None, "files") == {
        "args": ["fmt"],
        "stdin": "a  b\n",
        "files": {"doc.md": "# x\n", "new.md": "n"},
    }


@pytest.mark.parametrize(
    ("boundary", "observed", "via"),
    [
        ("function", RAISED, None),
        ("cli", Exited(exit=1, stdout="", stderr="no"), "stdout"),
        ("cli", Returned("x"), "stdout"),
    ],
)
def test_a_source_that_did_not_succeed_has_no_follow_up(
    boundary: str, observed: object, via: str | None
) -> None:
    assert repeated(boundary, {"args": ["x"]}, observed, None, via) is None  # type: ignore[arg-type]


def test_an_order_for_an_input_that_has_nothing_to_permute_is_an_error() -> None:
    with pytest.raises(ValueError, match="nothing to permute"):
        in_order("function", {"args": ["text"]}, "args[0]", (0,))


def test_idempotent_at_a_function_of_several_arguments_without_over_has_no_follow_up() -> None:
    assert repeated("function", {"args": ["a", "b"]}, Returned("c"), None, None) is None
