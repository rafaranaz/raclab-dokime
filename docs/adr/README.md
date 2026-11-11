# Architecture decision records

*Leer en [español](README.es.md).*

Every decision with consequences is recorded in an ADR: a short file with the context, the
decision, the alternatives considered and the consequences. Accepted ADRs are not edited: if the
decision changes, a new one supersedes the previous one. The
[adr](../../.claude/skills/adr/SKILL.md) skill describes the format.

| No. | Decision | Status |
|---|---|---|
| [0001](0001-record-decisions-in-adrs.md) | Record decisions in ADRs | Accepted |
| [0002](0002-new-repository-ported-by-module.md) | New repository, ported module by module | Superseded by 0008 |
| [0003](0003-rules-enforced-in-ci.md) | Rules are enforced in CI; skills only guide | Accepted |
| [0004](0004-history-out-of-the-code.md) | History lives in git and in the ADRs, not in the code | Accepted |
| [0005](0005-languages.md) | English for code, bilingual documentation and a bilingual product | Accepted |
| [0006](0006-linear-history-and-closed-scopes.md) | Linear history with rebase and closed commit scopes | Accepted |
| [0007](0007-mit-license.md) | MIT license | Accepted |
| [0008](0008-built-new-nothing-is-ported.md) | The product is built new; nothing is ported | Accepted |
| [0009](0009-verification-and-evidence-layer.md) | The product is a verification and evidence layer around existing coding agents | Accepted |
| [0010](0010-threat-model.md) | The threat model names what is defended and what is not | Accepted |
| [0011](0011-contract-of-requirements-and-approved-examples.md) | A contract is EARS requirements plus examples approved by a person | Accepted |
| [0012](0012-examples-are-observations-at-a-boundary.md) | An example is an observation at a boundary, compared outside the subject's process | Accepted |
| [0013](0013-provenance-decides-what-a-check-can-do.md) | The origin of a check decides what its failure can do | Accepted |
| [0014](0014-hidden-checks-are-held-out-approved-examples.md) | Hidden checks are approved examples held out by case, plus approved relations | Accepted |
| [0015](0015-a-gate-returns-one-of-four-verdicts.md) | A gate returns one of four verdicts | Accepted |
| [0016](0016-verification-in-a-container-on-base-plus-patch.md) | Verification runs in a container without network, on the base commit plus the patch | Accepted |
| [0017](0017-damage-outside-the-change-against-a-baseline.md) | Damage outside the change is found by comparing against a baseline | Accepted |
| [0018](0018-the-flow-is-a-state-machine-in-a-yaml-file.md) | The flow is a state machine declared in a YAML file | Accepted |
| [0019](0019-the-harness-launches-the-installed-agent-through-files.md) | The harness launches the installed agent and talks to it through files | Accepted |
| [0020](0020-agent-isolation-is-optional-adoption-is-a-ladder.md) | Isolating the agent is optional; adoption climbs a ladder | Accepted |
| [0021](0021-the-agent-disputes-a-check-instead-of-editing-it.md) | The agent disputes a check instead of editing it | Accepted |
| [0022](0022-model-calls-of-the-harness-go-through-a-port.md) | The model calls of the harness go through a port with three routes | Accepted |
| [0023](0023-evidence-is-an-attestation-bound-to-the-tree.md) | Evidence is an in-toto attestation bound to the resulting tree | Accepted |
| [0024](0024-approval-attestation-and-commit-are-signed-separately.md) | Approval, attestation and commit are signed separately | Accepted |
| [0025](0025-the-interview-works-on-files-and-ends-by-coverage.md) | The interview works on files and ends by coverage | Accepted |
| [0026](0026-formal-consistency-is-checked-per-requirement.md) | Formal consistency is checked per requirement, and its findings ask | Accepted |
| [0027](0027-memory-has-one-layout-and-three-scopes.md) | Memory has one layout, two storages and three scopes | Accepted |
| [0028](0028-language-support-is-a-declarative-pack-with-levels.md) | Language support is a declarative pack with support levels | Accepted |
| [0029](0029-build-order-starts-with-auditing.md) | The build order starts with auditing a change that already exists | Accepted |
| [0030](0030-the-harness-is-measured-on-a-corpus-with-known-verdicts.md) | The harness is measured on a corpus with known verdicts | Accepted |
| [0031](0031-modules-depend-only-on-core.md) | Modules depend only on core; adapters are imported only by the composition root | Accepted |
| [0032](0032-bilingual-interaction-signs-what-was-shown.md) | The person works in their language, and the approval signs what was shown | Accepted |
| [0033](0033-a-specification-from-another-tool-enters-as-proposals.md) | A specification from another tool enters as proposals | Accepted |
| [0034](0034-a-state-closes-with-the-aggregated-verdict-of-its-gates.md) | A state closes with the aggregated verdict of its gates | Accepted |
| [0035](0035-the-flow-is-loaded-and-validated-in-core.md) | The flow is loaded and validated in core | Accepted |
