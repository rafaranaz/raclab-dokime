# Requirements of the `verify` scope

The gates of a change that arrives already made, and their aggregation
([`04-states-and-flows.md`](../architecture/04-states-and-flows.md)). `verify` runs the gates over
the ports that `interfaces` gives it: the audited repository, the verification runtime and the port
that observes. It imports `core`, `contract`, `oracle` and `packs`, and talks to no person and no
agent. Each requirement follows an EARS template and has at least one test that declares it in its
`SDD-EARS:` marker.

The result of a gate, the gates `protected-paths`, `baseline`, `visible-examples`,
`existing-tests` and `repeatability`, and the aggregation of the gates of a state are built.

## The result of a gate

- **VERIFY-001** The result of a gate shall carry the name of the gate, its verdict and its findings.
- **VERIFY-002** The verdict of the result of a gate shall be the summary of its findings, `PASS` when it has none.
- **VERIFY-003** The result of a gate shall carry its checks as one entry for each origin that has checks, with the number of its checks, in the order `existing`, `human`, `derived`, `model` ([ADR-0064](../adr/0064-the-evidence-of-a3-is-an-unsigned-statement-with-a-closed-predicate.md)).
- **VERIFY-004** If the checks given to a result name an origin outside those four, repeat an origin, break that order or give an origin fewer than one check, then the result shall refuse to be built with an error that names the checks.

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
- **VERIFY-045** When the examples of the contract have been observed, the gates `baseline` and `visible-examples` shall give as their checks the examples of the contract counted by their origin.
- **VERIFY-046** If the gate reports the finding of a refusal, or the contract has no example, then the gate shall give no checks.

## The gate `baseline` ([ADR-0016](../adr/0016-verification-in-a-container-on-base-plus-patch.md))

- **VERIFY-060** When a change is checked, the gate `baseline` shall observe the examples of the contract on the tree of the base commit as many times as `baseline.runs` of the policy says ([ADR-0017](../adr/0017-damage-outside-the-change-against-a-baseline.md)).
- **VERIFY-061** If an example of a requirement of kind `preserve` does not hold on the base, then the gate `baseline` shall report a finding with the code `preserved-example-fails-on-base` and the verdict `FAIL`.
- **VERIFY-062** If an example of a requirement of kind `new` or `change` holds on the base, then the gate `baseline` shall report a finding with the code `example-holds-on-base` and the verdict `ASK`.
- **VERIFY-063** If an example holds in some runs of the base and not in others, then the gate `baseline` shall report a finding with the code `example-varies-on-base` and the verdict `ASK`, instead of the findings of VERIFY-061 and VERIFY-062.
- **VERIFY-064** If an example holds in some runs of the base and not in others, then the gate `baseline` shall list it as unstable in its result.

## The gate `visible-examples` ([ADR-0013](../adr/0013-provenance-decides-what-a-check-can-do.md))

- **VERIFY-080** When a change is checked, the gate `visible-examples` shall observe the examples of the contract on the tree of the change of VERIFY-044.
- **VERIFY-081** If an example whose origin is not `model` does not hold, then the gate `visible-examples` shall report a finding with the code `example-fails` and the verdict `FAIL`.
- **VERIFY-082** If an example of origin `model` does not hold, then the gate `visible-examples` shall report a finding with the code `model-example-fails` and the verdict `ASK`.

## The gate `existing-tests` ([ADR-0017](../adr/0017-damage-outside-the-change-against-a-baseline.md), [ADR-0058](../adr/0058-existing-tests-runs-the-tests-of-the-base-on-the-code-of-the-patch.md))

A test is named as the report of the pack names it, `<class name>::<name>`. Known limit of
VERIFY-107: if a module `tests/test_a.py` and a package `tests/test_a/` live side by side, a test of
the package counts as of the module, since its class name starts with `tests.test_a.`; Python does
not import both well at once, so it is unlikely.

- **VERIFY-100** When a change is checked, the gate `existing-tests` shall run the tests of the pack on the tree of the base as many times as `baseline.runs` of the policy says.
- **VERIFY-101** When the base has run, the gate `existing-tests` shall count as passing in the baseline only a test that passed in every run of the base.
- **VERIFY-102** If the outcome of a test differs between the runs of the base, or the test is missing from some of them, then the gate `existing-tests` shall leave it out of the comparison and list it as unstable in its result.
- **VERIFY-103** When the base has run, the gate `existing-tests` shall run the tests of the pack once on the tree of the change of VERIFY-044.
- **VERIFY-104** If a test that passed in the baseline is in the run of the change and did not pass, then the gate `existing-tests` shall report a finding with the code `existing-test-fails` and the verdict `FAIL`.
- **VERIFY-105** If a test that passed in the baseline is not in the run of the change and is not of a file that the contract authorises, then the gate `existing-tests` shall report a finding with the code `existing-test-disappears` and the verdict `FAIL`.
- **VERIFY-106** If a test that passed in the baseline is not in the run of the change and is of a file that the contract authorises, then the gate `existing-tests` shall report a finding with the code `authorised-test-disappears` and the verdict `ASK`.
- **VERIFY-107** The gate `existing-tests` shall count a test as of a file when its class name is the path of the file with each `/` as a `.`, without the suffix `.py`, or starts with that and a `.`.
- **VERIFY-108** If a run of the tests ends with a finding, then the gate `existing-tests` shall report that finding, with the verdict `ERROR`.
- **VERIFY-109** When the run of the change has ended, the gate `existing-tests` shall give as its checks one entry of origin `existing` with the number of tests that passed in the baseline, and no entry when none passed.
- **VERIFY-110** If a run of the tests ends with a finding, then the gate `existing-tests` shall give no checks.

## The aggregation of a state ([ADR-0015](../adr/0015-a-gate-returns-one-of-four-verdicts.md), [ADR-0034](../adr/0034-a-state-closes-with-the-aggregated-verdict-of-its-gates.md))

A work state of the flow lists its gates, and closes with the aggregation of their verdicts. In this
version `verify` builds `baseline`, `protected-paths`, `existing-tests`, `visible-examples`,
`repeatability` and `sealed-examples`; the other gates of the table of [`04-states-and-flows.md`](../architecture/04-states-and-flows.md) are
not applicable, each with the block that builds it.

- **VERIFY-120** When the gates of a state have run, the aggregation shall give the verdict of the state by the precedence of ADR-0015 over the verdicts of the gates that ran.
- **VERIFY-121** When the gates of a state have run, the aggregation shall list every gate of the state in its order, as run with its result, or as not applicable with its reason.
- **VERIFY-122** When a gate of the state is one that this version does not build, the aggregation shall list it as not applicable, with the block or milestone that builds it as its reason.
- **VERIFY-123** If a gate of the state that this version builds has no result, then the aggregation shall give the verdict `ERROR` with a finding with the code `gate-missing`, naming the gate.
- **VERIFY-125** If a result is of a gate that is not of the state, then the aggregation shall give the verdict `ERROR` with a finding with the code `gate-not-of-the-state`, naming the gate.
- **VERIFY-124** If a gate of the state is not in the table of the gates, then the aggregation shall give the verdict `ERROR` with a finding with the code `gate-unknown`, naming the gate.
- **VERIFY-126** If two results are of the same gate, then the aggregation shall give the verdict `ERROR` with a finding with the code `gate-repeated`, naming the gate.
- **VERIFY-127** When a gate of the state that this version builds is given as not applicable with a reason, the aggregation shall list it as not applicable with that reason.
- **VERIFY-128** If a gate given as not applicable also has a result, then the aggregation shall give the verdict `ERROR` with a finding with the code `gate-repeated`, naming the gate.

## The gate `repeatability` ([ADR-0017](../adr/0017-damage-outside-the-change-against-a-baseline.md), [ADR-0054](../adr/0054-the-policy-is-an-optional-file-of-values.md))

The verification runs as many times as `verification.runs` of the policy says, and the gate asks
when two runs give different verdicts, as the table of the gates says
([`04-states-and-flows.md`](../architecture/04-states-and-flows.md#the-gates)). `interfaces` runs
the gates of the state `verifying` that many times and gives this gate their results; `verify`
compares them.

- **VERIFY-140** When the results of the runs of the verification are given, the gate `repeatability` shall compare, for each gate, the verdicts it gave in the runs.
- **VERIFY-141** If a gate gave different verdicts in two runs, then the gate `repeatability` shall report a finding with the code `verdict-varies` and the verdict `ASK` that names the gate and its verdict in each run, in the order of the runs.
- **VERIFY-142** If a gate has a result in some runs and not in others, or twice in one run, then the gate `repeatability` shall report a finding with the code `runs-differ` and the verdict `ERROR` that names the gate.
- **VERIFY-143** If fewer than two runs are given, then the gate `repeatability` shall refuse them with an error that names how many were given.
- **VERIFY-144** When every gate gave the same verdict in every run, the gate `repeatability` shall pass with no finding.

## The sealed batch ([ADR-0014](../adr/0014-hidden-checks-are-held-out-approved-examples.md), [ADR-0072](../adr/0072-the-sealed-store-is-encrypted-with-age-for-a-list-of-recipients.md))

The sealed batch is what the sealed store encrypts: the held-out examples of a contract, each with
its salt and its text as approved, the seed of the split and the canary. The canary is a copy of a
held-out example whose expected value cannot hold; it detects a comparison that accepts what it
should not, the side of a false accept, and not an observer that makes everything fail, which gives
rejections and is the safe side.

- **VERIFY-150** When a sealed batch is made, the module shall give the canonical form of a mapping with `format` 1, the story, the base, the full name of the commit of the clean checkout that was sealed from, the seed, the ids of every example of the contract before the split in their order, the ids of the examples kept visible as already published, each held-out example with its id, its salt in hexadecimal and its text, each case that holds out nothing, and the canary.
- **VERIFY-151** When the canary of a batch is made, the module shall copy the held-out example that `random.Random(seed).choice` chooses in the order of the contract, with an id of its own and with only its first step, whose one expectation is a given text of 32 hexadecimal digits, as `stdout` at `cli` or as `returns` at `function`.
- **VERIFY-152** If the content of a sealed batch is not the canonical form of such a mapping, then the module shall refuse to read it, with the code `unreadable-batch`.
- **VERIFY-153** When a sealed batch is made, the module shall give each case that holds out nothing with its requirement, its name and its reason: `single-example` when the case has one example, `all-published` when every example of a case of two or more was kept visible as already published.

## The gate `sealed-examples` ([ADR-0014](../adr/0014-hidden-checks-are-held-out-approved-examples.md), [ADR-0073](../adr/0073-the-key-of-the-hold-out-lives-outside-ci-until-b4.md))

The gate runs on the tree of the change, after `visible-examples` passed; the flow of the audit
decides when. Where the key is not, the gate is not applicable.

- **VERIFY-160** If the sealed batch does not hold exactly the held-out examples of the contract, or the digest of the salt and the text of one of them is not the one that the contract gives, then the gate shall give a finding `sealed-batch-mismatch` of the verdict `ERROR`, and observe nothing.
- **VERIFY-161** When the digests of the batch hold, the gate shall read each held-out example from its text with the requirements of the contract, observe the held-out examples and the canary on the tree of the change, and compare each one with its observation.
- **VERIFY-162** If a held-out example does not hold, then the gate shall give a finding `sealed-example-fails` of the verdict `FAIL`, whose message is the words of the oracle for the agent: the requirement and the classes of the failure.
- **VERIFY-163** If a held-out example whose origin is `model` does not hold, then the gate shall give a finding `sealed-model-example-fails` of the verdict `ASK`, with the same words.
- **VERIFY-164** If the canary holds, then the gate shall give a finding `canary-passed` of the verdict `ERROR`, since the comparison accepts an expectation that cannot hold.
- **VERIFY-165** When the canary does not hold, the gate shall give no finding of it and count it as no check, so that the canary never counts as the failure of a requirement nor reaches the agent.
- **VERIFY-166** The gate shall give no finding whose message holds a value, an input or the identifier of a held-out example or of the canary.
- **VERIFY-167** The reason of the gate `sealed-examples` where the key is not shall be `the key is not here`.
- **VERIFY-168** When the digests of the batch hold, the gate shall draw the split again from the seed, the examples kept visible and the order of the batch, over the visible and the held-out examples, and if the examples it holds out, or the cases that hold out nothing with their reasons, differ from those of the batch, then give the finding `sealed-batch-mismatch` and observe nothing.

### What was already published

An example is published when a version of the contract of the story in the history has it, by its
id or by its boundary, target and steps; the command that seals keeps such an example visible, and
the gate checks with the same function that the batch kept visible exactly those, and that no
held-out example was published since. These are limits, not guarantees: the content is compared as
YAML reads it, so an example published with a field added or a value spelt otherwise is not
recognised; a version under an earlier path, after a rename, is not read, nor one in a commit that
the start does not reach, nor a copy of an example in another file. And the history is read up to
the base of the change, so a held-out example published in a commit of the change and taken back
in another is not seen by its audit: where the project merges keeping the commits, by rebase or by
a merge commit, the next audit sees it, and with a squash merge no audit does.

- **VERIFY-169** When it is given the examples of a contract and the versions of the file of the contract, the verification shall count as published each example whose id, or whose boundary, target and steps as YAML reads them, an example of a version has.
- **VERIFY-170** When it reads the examples of a version of a contract, the verification shall take them from its list `examples` only, never from its list `held_out`.
- **VERIFY-171** If the base of the batch is not a commit reachable from the base of the change, then the gate shall give the finding `sealed-batch-mismatch` and observe nothing.
- **VERIFY-172** If the examples published in the versions of the contract of the story reachable from the base of the batch, among the visible examples and those of the batch, differ from the examples that the batch keeps visible, then the gate shall give the finding `sealed-batch-mismatch` and observe nothing.
- **VERIFY-173** If a held-out example is published in a version of the contract of the story reachable from the base of the change, then the gate shall give a finding `held-out-published` of the verdict `ERROR`, at the line of its entry in `held_out`, whose message says to replace the example and seal again, and observe nothing.
- **VERIFY-174** If the port of the repository or the port of the history of a file refuses while the gate reads the history, then the gate shall give the finding of the refusal, of the verdict `ERROR`, and observe nothing.

### When the gate applies

The entries `held_out` of the contract and the sealed batch are read from the base, as the
recipients are, so that a patch that takes them away does not make the gate not applicable. They go
together, which is decided without the key, so in CI as well: a pull request that takes away one of
them fails there, and does not pass as one without the key.

- **VERIFY-175** If the base has a sealed batch for the story and its contract has no entry in `held_out`, then the gate shall give a finding `sealed-batch-mismatch` of the verdict `ERROR`, whether the key is here or not.
- **VERIFY-176** If the contract has entries in `held_out` and the base has no sealed batch for the story, then the gate shall give a finding `sealed-batch-missing` of the verdict `ERROR`, whether the key is here or not.
- **VERIFY-177** When the contract has no entry in `held_out` and the base has no sealed batch for the story, the gate shall be not applicable with the reason `the contract holds out no example`, whether the key is here or not.
- **VERIFY-178** When the contract has entries in `held_out`, the base has a sealed batch for the story and the key is not here, the gate shall be not applicable with the reason `the key is not here`.
