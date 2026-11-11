# SDD-EARS: CORE-042
from dokime.core.reading import read

TEXT = """\
story: rounding
steps:
  - input:
      body: |
        one
        two
    expect:
      returns:
        $text: |
          one
        final_newline: true
      stdout: "quoted\\ntext\\n"
"""


def test_the_paths_of_the_literal_blocks_are_given() -> None:
    assert read(TEXT).blocks == {
        ("steps", 0, "input", "body"),
        ("steps", 0, "expect", "returns", "$text"),
    }


def test_a_quoted_text_with_newlines_is_not_a_literal_block() -> None:
    reading = read(TEXT)
    assert isinstance(reading.value, dict)
    assert ("steps", 0, "expect", "stdout") not in reading.blocks


def test_a_literal_block_in_a_sequence_and_at_the_root_is_given() -> None:
    assert read("- |\n  one\n- two\n").blocks == {(0,)}
    assert read("|\n  one\n").blocks == {()}


def test_a_text_without_literal_blocks_has_none() -> None:
    assert read("a: 1\nb: [x, y]\n").blocks == frozenset()


def test_a_literal_block_left_out_of_the_value_is_not_given() -> None:
    assert read("a: 1\n? [x]\n: |\n  one\n").blocks == frozenset()
