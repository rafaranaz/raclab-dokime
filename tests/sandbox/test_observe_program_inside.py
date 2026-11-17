# SDD-EARS: SANDBOX-097 SANDBOX-098 SANDBOX-099 SANDBOX-101 SANDBOX-102
"""The functions of the program that observes, called inside the process of the tests.

The other tests run the program in processes of its own, which coverage does not measure, as for
the program that reads the reports; these call its functions here.
"""

import os
import sys
from pathlib import Path

import pytest

from dokime.sandbox import observe_program


def test_a_value_is_observed_as_returned_or_by_its_type() -> None:
    assert observe_program._call(lambda value: value, {"args": [[1, 2.5]]}) == {
        "returned": [1, 2.5]
    }
    assert observe_program._call(lambda: {1}, {}) == {"not_json": "set"}
    assert observe_program._call(lambda: float("inf"), {}) == {"not_json": "float"}


def test_an_exception_is_observed_with_its_classes() -> None:
    def fails() -> None:
        raise KeyError("k")

    (raised,) = observe_program._call(fails, {}).values()
    assert (raised["qualified"], raised["classes"][1]) == (
        "builtins.KeyError",
        "builtins.LookupError",
    )


def test_a_target_is_found_by_its_module_and_its_dotted_path() -> None:
    assert observe_program._target("os.path:join") is os.path.join
    with pytest.raises(TypeError, match="not a function"):
        observe_program._target("os:sep")


def test_a_command_runs_in_the_working_directory_and_its_files_are_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "deep.txt").write_bytes(b"\xff")
    (tmp_path / "link").symlink_to(tmp_path / "sub")
    script = "import sys; print(open('given.txt').read()); sys.exit(1)"
    seen = observe_program._command(
        f"{sys.executable} -c {script!r}", {"files": {"given.txt": "g"}}
    )
    assert (seen["exit"], seen["stdout"]) == (1, "g\n")
    assert seen["files"] == {"given.txt": "g", "sub/deep.txt": "�"}
