# Requirements of the `verify` scope

The gates of a change that arrives already made, and their aggregation
([`04-states-and-flows.md`](../architecture/04-states-and-flows.md)). `verify` runs the gates over
the ports that `interfaces` gives it: the audited repository, the verification runtime and the port
that observes. It imports `core`, `contract`, `oracle` and `packs`, and talks to no person and no
agent. Each requirement follows an EARS template and has at least one test that declares it in its
`SDD-EARS:` marker.

The result of a gate, and the gates `protected-paths`, `baseline`, `visible-examples` and
`existing-tests`, are built; the aggregation comes in the next increment.

## The result of a gate

- **VERIFY-001** The result of a gate shall carry the name of the gate, its verdict and its findings.
- **VERIFY-002** The verdict of the result of a gate shall be the summary of its findings, `PASS` when it has none.

## The gate `protected-paths` ([ADR-0016](../adr/0016-verification-in-a-container-on-base-plus-patch.md), [ADR-0056](../adr/0056-the-pack-names-the-configuration-of-its-tests.md), [ADR-0059](../adr/0059-a-mixed-file-protects-the-section-that-configures-the-tests.md))

A change that arrives already made is a patch on a base commit. The protected paths are the tests
of the pack (`tests.paths`), the configuration of its tests (`tests.config`), the sections of its
mixed files (`tests.sections`) and the directory of the harness, `.dokime/`, which holds the
policy, the pack, the contract and the flow. The contract authorises some of them in
`may_modify_tests`.

- **VERIFY-020** When a change is checked, the gate `protected-paths` shall compare the tree of the base with the tree of the base with the patch applied, file by file.
- **VERIFY-021** When the gate compares the two trees, the gate shall read their files without following links, comparing a file by its bytes and whether it is executable, and a link by its target.
- **VERIFY-022** If the patch adds, changes or removes a path of the tests or of the configuration of the tests that the contract does not authorise, then the gate shall report a finding with the code `protected-path` that names the path and why it is protected.
- **VERIFY-023** If the patch changes a mixed file of a section of the pack, then the gate shall report the finding of VERIFY-022 only when the section changed, by the rules of `packs`.
- **VERIFY-024** If the patch adds, changes or removes a path under `.dokime/`, then the gate shall report the finding of VERIFY-022 whatever the contract authorises.
- **VERIFY-025** When an entry of `may_modify_tests` names a path, the gate shall count as authorised only that path; for a mixed file, only its section.
- **VERIFY-026** The gate shall give the verdict `FAIL` to each finding it reports.
- **VERIFY-027** If the patch does not apply on the base, then the gate shall report a finding with the verdict `ERROR` and the code of the refusal of the repository.

## The examples observed on a tree ([ADR-0012](../adr/0012-examples-are-observations-at-a-boundary.md), [ADR-0063](../adr/0063-a-program-of-sandbox-observes-the-examples-inside-the-zone.md))

The gates `baseline` and `visible-examples` observe the examples of the contract on a tree, through
the port that observes, in the image that the pack built, and compare each one with the oracle.

- **VERIFY-040** When the examples of a contract are observed on a tree, the gate shall extract the tree into a directory of its own and ask the port that observes for every example of the contract, in its order, with the inputs of its steps and nothing of what they expect.
- **VERIFY-041** If the repository or the port that observes refuses, then the gate shall report the finding of the refusal, with the verdict `ERROR`.
- **VERIFY-042** When the gate reports a finding on an example, the gate shall give the line of the example and name the example, its requirement and the parts of its steps that did not hold, quoting each value within 200 characters.
- **VERIFY-043** If the contract has no example, then the gate shall pass without asking the port that observes.
- **VERIFY-044** When a change is checked, the gates `visible-examples` and `existing-tests` shall use as the tree of the change the base with the patch applied, with the paths of the tests and of the configuration of the tests taken from the base, except those that the contract authorises in `may_modify_tests` ([ADR-0058](../adr/0058-existing-tests-runs-the-tests-of-the-base-on-the-code-of-the-patch.md)).

## The gate `baseline` ([ADR-0016](../adr/0016-verification-in-a-container-on-base-plus-patch.md))

- **VERIFY-060** When a change is checked, the gate `baseline` shall observe the examples of the contract on the tree of the base commit.
- **VERIFY-061** If an example of a requirement of kind `preserve` does not hold on the base, then the gate `baseline` shall report a finding with the code `preserved-example-fails-on-base` and the verdict `FAIL`.
- **VERIFY-062** If an example of a requirement of kind `new` or `change` holds on the base, then the gate `baseline` shall report a finding with the code `example-holds-on-base` and the verdict `ASK`.

## The gate `visible-examples` ([ADR-0013](../adr/0013-provenance-decides-what-a-check-can-do.md))

- **VERIFY-080** When a change is checked, the gate `visible-examples` shall observe the examples of the contract on the tree of the change of VERIFY-044.
- **VERIFY-081** If an example whose origin is not `model` does not hold, then the gate `visible-examples` shall report a finding with the code `example-fails` and the verdict `FAIL`.
- **VERIFY-082** If an example of origin `model` does not hold, then the gate `visible-examples` shall report a finding with the code `model-example-fails` and the verdict `ASK`.

## The gate `existing-tests` ([ADR-0017](../adr/0017-damage-outside-the-change-against-a-baseline.md), [ADR-0058](../adr/0058-existing-tests-runs-the-tests-of-the-base-on-the-code-of-the-patch.md))

A test is named as the report of the pack names it, `<class name>::<name>`.

- **VERIFY-100** When a change is checked, the gate `existing-tests` shall run the tests of the pack on the tree of the base as many times as `baseline.runs` of the policy says.
- **VERIFY-101** When the base has run, the gate `existing-tests` shall count as passing in the baseline only a test that passed in every run of the base.
- **VERIFY-102** If the outcome of a test differs between the runs of the base, or the test is missing from some of them, then the gate `existing-tests` shall leave it out of the comparison and list it as unstable in its result.
- **VERIFY-103** When the base has run, the gate `existing-tests` shall run the tests of the pack once on the tree of the change of VERIFY-044.
- **VERIFY-104** If a test that passed in the baseline is in the run of the change and did not pass, then the gate `existing-tests` shall report a finding with the code `existing-test-fails` and the verdict `FAIL`.
- **VERIFY-105** If a test that passed in the baseline is not in the run of the change and is not of a file that the contract authorises, then the gate `existing-tests` shall report a finding with the code `existing-test-disappears` and the verdict `FAIL`.
- **VERIFY-106** If a test that passed in the baseline is not in the run of the change and is of a file that the contract authorises, then the gate `existing-tests` shall report a finding with the code `authorised-test-disappears` and the verdict `ASK`.
- **VERIFY-107** The gate `existing-tests` shall count a test as of a file when its class name is the path of the file with each `/` as a `.`, without the suffix `.py`, or starts with that and a `.`.
- **VERIFY-108** If a run of the tests ends with a finding, then the gate `existing-tests` shall report that finding, with the verdict `ERROR`.
