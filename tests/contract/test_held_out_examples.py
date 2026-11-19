# SDD-EARS: CONTRACT-016 CONTRACT-030 CONTRACT-090 CONTRACT-091
from dokime.contract.check import check
from dokime.contract.model import HeldOut
from dokime.core.verdicts import Verdict
from tests.contract.contracts import VALID, codes, line_of, only

DIGEST = "sha256:" + "0" * 63 + "a"

SPLIT = VALID.replace(
    "\nrelations:",
    f"""
held_out:
  - id: E-0009
    requirement: round-total-once
    case: normal
    digest: {DIGEST}

relations:""",
)


def test_the_held_out_examples_are_returned_with_what_the_file_keeps() -> None:
    checked = check(SPLIT)
    assert checked.findings == ()
    assert checked.contract is not None
    assert checked.contract.held_out == (
        HeldOut(
            id="E-0009",
            requirement="round-total-once",
            case="normal",
            digest=DIGEST,
            line=line_of("  - id: E-0009", SPLIT),
        ),
    )


def test_a_contract_without_held_out_examples_has_none() -> None:
    checked = check(VALID)
    assert checked.contract is not None
    assert checked.contract.held_out == ()


def test_an_example_both_visible_and_held_out_is_in_clear() -> None:
    text = SPLIT.replace("  - id: E-0009", "  - id: E-0003")
    finding = only(check(text), "held-out-in-clear")
    assert finding.verdict is Verdict.ERROR
    assert finding.lines == (
        line_of("  - id: E-0003\n    requirement: keep", text),
        line_of("  - id: E-0003\n    requirement: round", text),
    )
    assert check(text).contract is None


def test_a_held_out_example_of_an_unknown_requirement_is_reported() -> None:
    text = SPLIT.replace(
        "    requirement: round-total-once\n    case: normal\n    digest",
        "    requirement: nowhere\n    case: normal\n    digest",
    )
    assert codes(check(text)) == ["unknown-requirement"]


def test_a_repeated_held_out_id_is_reported() -> None:
    entry = (
        "  - id: E-0009\n    requirement: round-total-once\n    case: normal\n"
        f"    digest: {DIGEST}\n"
    )
    text = SPLIT.replace(entry, entry + entry)
    assert codes(check(text)) == ["duplicate-id"]


def test_a_held_out_example_with_a_field_of_content_is_reported() -> None:
    text = SPLIT.replace(f"    digest: {DIGEST}\n", f"    digest: {DIGEST}\n    steps: []\n")
    assert codes(check(text)) == ["unknown-field"]


def test_a_digest_that_is_not_sha256_in_hexadecimal_is_reported() -> None:
    for wrong in ("sha256:ABC", "md5:" + "0" * 32, "sha256:" + "0" * 63, '"' + "0" * 64 + '"'):
        assert codes(check(SPLIT.replace(DIGEST, wrong))) == ["wrong-type"], wrong


def test_a_held_out_example_that_is_not_a_mapping_is_reported() -> None:
    entry = (
        "  - id: E-0009\n    requirement: round-total-once\n    case: normal\n"
        f"    digest: {DIGEST}\n"
    )
    text = SPLIT.replace(entry, "  - E-0009\n")
    assert codes(check(text)) == ["wrong-type"]
