# Requirements of the `core` scope

Domain types that every module shares. This first increment holds what the contract check of
milestone A1 needs: the verdicts of a gate and the findings that explain them. Each requirement
follows an EARS template and has at least one test that declares it in its `SDD-EARS:` marker.

## Verdicts ([ADR-0015](../adr/0015-a-gate-returns-one-of-four-verdicts.md))

- **CORE-001** The verdict type shall have exactly the values `PASS`, `FAIL`, `ASK` and `ERROR`.
- **CORE-002** When any verdict of a round is `ERROR`, the aggregation shall return `ERROR`.
- **CORE-003** When no verdict of a round is `ERROR` and any is `FAIL`, the aggregation shall return `FAIL`.
- **CORE-004** When no verdict of a round is `ERROR` or `FAIL` and any is `ASK`, the aggregation shall return `ASK`.
- **CORE-005** When every verdict of a round is `PASS`, the aggregation shall return `PASS`.
- **CORE-006** If a round has no verdicts, then the aggregation shall raise an error that says the round is empty.
- **CORE-007** The aggregation shall return the same verdict for any order of the same verdicts.

## Findings

- **CORE-010** The finding shall carry a code, a message, a location and a verdict.
- **CORE-011** If a finding is given the verdict `PASS`, then the finding shall be rejected with an error naming the verdict.
- **CORE-012** If a finding has an empty code or an empty message, then the finding shall be rejected with an error naming the empty field.
- **CORE-013** When a list of findings is summarised, the summary shall be the aggregation of their verdicts.
- **CORE-014** When a list of findings is empty, the summary shall be `PASS`.
