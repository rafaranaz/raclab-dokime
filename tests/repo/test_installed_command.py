# SDD-EARS: REPO-110
import shutil
import subprocess
from importlib.metadata import entry_points

from dokime.interfaces.cli import main
from tools._common import DEFAULT_ROOT

CONTRACT = DEFAULT_ROOT / "tests/contract/fixtures/escape-pipe-in-markdown-tables.contract.yaml"


def test_the_package_installs_a_command_named_dokime_that_is_the_command_line() -> None:
    commands = entry_points(group="console_scripts", name="dokime")
    assert [command.value for command in commands] == ["dokime.interfaces.cli:main"]
    assert next(iter(commands)).load() is main


def test_the_installed_command_checks_a_contract() -> None:
    dokime = shutil.which("dokime")
    assert dokime is not None
    run = subprocess.run(
        [dokime, "contract", "check", str(CONTRACT)], capture_output=True, text=True, check=False
    )
    assert (run.returncode, run.stdout, run.stderr) == (0, "PASS: no findings\n", "")
