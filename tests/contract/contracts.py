"""A valid contract to seed defects into, and helpers to read the result of a check."""

from dokime.contract.check import check
from dokime.contract.model import Checked
from dokime.core.findings import Finding

VALID = """\
format: 1
story: invoice-rounding
may_modify_tests: [tests/test_totals.py]

requirements:
  - id: round-total-once
    kind: new
    text: When an invoice has lines in several currencies, the system shall round the total once.
    source: written
  - id: keep-empty-invoices
    kind: preserve
    text: While an invoice has no lines, the system shall return a total of zero.
    source: written

examples:
  - id: E-0001
    requirement: round-total-once
    case: normal
    boundary: function
    target: billing.totals:invoice_total
    origin: human
    steps:
      - input:
          args: [[3.335, 6.695]]
          kwargs: {currency: EUR}
        expect:
          returns: {total: {$approx: 10.03, tolerance: 0.005}, currency: EUR}
  - id: E-0002
    requirement: round-total-once
    case: normal
    boundary: cli
    target: invoice total
    description: Two lines in euros whose sum needs rounding.
    origin: human
    steps:
      - input:
          args: [invoice.json]
          files:
            invoice.json: {$json: {lines: [3.335, 6.695]}}
        expect:
          exit: 0
          stdout:
            $text: |
              total: 10.03
            final_newline: true
  - id: E-0003
    requirement: keep-empty-invoices
    case: empty
    boundary: function
    target: billing.totals:invoice_total
    origin: human
    steps:
      - input: {args: [[]]}
        expect: {returns: {total: 0, currency: EUR}}

relations:
  - id: L1
    requirement: round-total-once
    relation: order-insensitive
    target: billing.totals:invoice_total
    over: lines
"""


def seeded(old: str, new: str, text: str = VALID) -> Checked:
    """Check the valid contract after replacing one piece of its text."""
    assert text.count(old) == 1, f"{old!r} appears {text.count(old)} times"
    return check(text.replace(old, new))


def line_of(piece: str, text: str = VALID) -> int:
    """The line where a piece of the valid contract starts."""
    assert text.count(piece) == 1, f"{piece!r} appears {text.count(piece)} times"
    return text[: text.index(piece)].count("\n") + 1


def codes(checked: Checked) -> list[str]:
    return [finding.code for finding in checked.findings]


def only(checked: Checked, code: str) -> Finding:
    """The single finding of a check, which has to have this code."""
    assert codes(checked) == [code], [(f.code, f.lines, f.message) for f in checked.findings]
    return checked.findings[0]
