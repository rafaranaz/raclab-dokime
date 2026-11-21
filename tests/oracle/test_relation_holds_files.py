# SDD-EARS: ORACLE-062
from dokime.contract.model import Relation
from dokime.core.observation import Exited
from dokime.oracle.relations import holds, in_order

OVER_A_FILE = Relation("L1", "R-sort", "order-insensitive", "sort lines", "input.txt", 9)
SOURCE_GIVEN = {"args": ["input.txt"], "files": {"input.txt": "b\na\n"}}
FOLLOW_GIVEN = in_order("cli", SOURCE_GIVEN, "input.txt", (1, 0))


def run(stdout: str, written: str, extra: dict[str, str] | None = None) -> Exited:
    return Exited(exit=0, stdout=stdout, stderr="", files={"input.txt": written, **(extra or {})})


def test_the_follow_up_input_is_the_file_permuted() -> None:
    assert FOLLOW_GIVEN["files"] == {"input.txt": "a\nb\n"}


def test_a_command_that_only_prints_the_lines_sorted_keeps_the_relation() -> None:
    source = run("a\nb\n", "b\na\n")
    follow = run("a\nb\n", "a\nb\n")
    assert holds(
        OVER_A_FILE, "cli", source, follow, source_given=SOURCE_GIVEN, follow_given=FOLLOW_GIVEN
    )


def test_a_command_that_sorts_the_file_in_place_keeps_the_relation() -> None:
    source = run("", "a\nb\n")
    follow = run("", "a\nb\n")
    assert holds(
        OVER_A_FILE, "cli", source, follow, source_given=SOURCE_GIVEN, follow_given=FOLLOW_GIVEN
    )


def test_a_command_that_rewrites_the_file_by_its_order_breaks_the_relation() -> None:
    source = run("", "a\nb\n")
    follow = run("", "b\na\n")
    assert not holds(
        OVER_A_FILE, "cli", source, follow, source_given=SOURCE_GIVEN, follow_given=FOLLOW_GIVEN
    )


def test_another_file_written_by_the_order_still_breaks_the_relation() -> None:
    source = run("", "b\na\n", {"out.txt": "b"})
    follow = run("", "a\nb\n", {"out.txt": "a"})
    assert not holds(
        OVER_A_FILE, "cli", source, follow, source_given=SOURCE_GIVEN, follow_given=FOLLOW_GIVEN
    )


def test_over_stdin_compares_every_file_that_the_runs_leave() -> None:
    by_stdin = Relation("L1", "R-sort", "order-insensitive", "sort lines", "stdin", 9)
    given = {"args": ["sort"], "stdin": "b\na\n"}
    source = Exited(exit=0, stdout="a\nb\n", stderr="", files={"log.txt": "b"})
    follow = Exited(exit=0, stdout="a\nb\n", stderr="", files={"log.txt": "a"})
    assert not holds(by_stdin, "cli", source, follow, source_given=given, follow_given=given)
