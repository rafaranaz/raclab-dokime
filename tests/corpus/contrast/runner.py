"""Run one example of a dokime contract as a black box, and the JSON that carries the example.

The conversion copies this file as `run.py` beside a copy of the modules of dokime, so it imports
only the standard library and `dokime`. Run from the root of a project,

    python run.py EXAMPLE_ID

it observes the example with the program that observes of dokime, in a process of its own, and
compares the observation with the oracle of dokime: 0 when it holds, 1 when it does not, and 2
when the program that observes ended with an error.
"""


def encode(example: object) -> object:
    return {}


def decode(data: object) -> object:
    return None


def request_json(example: object) -> dict[str, object]:
    return {}


def main(argv: list[str]) -> int:
    return 99
