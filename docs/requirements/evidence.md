# Requirements of the `evidence` scope

The evidence of a run
([`03-data-and-evidence.md`](../architecture/03-data-and-evidence.md#the-evidence)). In A3 it is the
in-toto statement alone, without an envelope, with the predicate v0.1 of
[ADR-0064](../adr/0064-the-evidence-of-a3-is-an-unsigned-statement-with-a-closed-predicate.md).
`evidence` imports nothing but `core` and decides no verdict: it records the verdicts it is given.
`interfaces` gives it the run and writes its bytes outside the tree they describe. Each requirement
follows an EARS template and has at least one test that declares it in its `SDD-EARS:` marker.

The statement of a run, its predicate, its canonical bytes and their reading back against the
schema of the predicate are built; signing and verifying come with block E.

## The statement

- **EVIDENCE-001** When a run is built into evidence, the builder shall give an in-toto Statement v1 with the `_type` `https://in-toto.io/Statement/v1`, the `predicateType` `https://github.com/rafaranaz/raclab-dokime/attestation/conformance/v0.1` and the subjects `tree`, with the `gitTree` of the tree of the base with the whole patch, and `change.patch`, with the `sha256` of the bytes of the patch.
- **EVIDENCE-002** When a run is built into evidence, the builder shall give its bytes as the canonical form of [ADR-0062](../adr/0062-a-digest-is-taken-over-a-restricted-canonical-json.md) of the statement in UTF-8.
- **EVIDENCE-003** When a run is built into evidence, the builder shall give its digest as `sha256:` and the hexadecimal SHA-256 of its bytes, which the event `evidence.built` records.
- **EVIDENCE-004** When a run is built into evidence, the builder shall name its file `<story>.statement.json` after the story of the run.
- **EVIDENCE-005** If the story, a requirement or an unstable example is not a name of letters and digits in words joined by hyphens, starting with a letter, then the builder shall refuse the run with an error that names it.

## The predicate

- **EVIDENCE-020** The predicate shall carry the `verdict` of the run as it is given, `delivered` as `false`, `independence` as `self-attested`, and `verifier` with the `harness` version given and `ran_on` as `developer`.
- **EVIDENCE-021** The predicate shall carry `contract` with the `story` and, when the contract file was read, its `digest` as `sha256:` and the SHA-256 of the bytes of the file.
- **EVIDENCE-022** The predicate shall carry in `inputs` the `base`, the name of the base commit, and the `policy`, with the `digest` of the normalised form of the effective policy and its `source`, `file` or `defaults`.
- **EVIDENCE-023** Where the run reached them, the predicate shall carry in `inputs` the `image` with its `digest` and the `platform` of its base image when it has one, the `pack` with the `digest` as `sha256:` and the SHA-256 of the bytes of its file, and the `probe` with the digest of the program that observes.
- **EVIDENCE-024** The predicate shall carry `human_decisions` as an empty list, and `ledger` with the `head`, the hash of the last event of the ledger given, and the number of its `events`.
- **EVIDENCE-025** If the run does not fill a field, then the builder shall leave the field out, never writing it as `null`.

## The gates

- **EVIDENCE-040** The predicate shall list in `gates` every gate of the run, in the order given.
- **EVIDENCE-041** When a gate ran, the builder shall write its entry with `gate`, `status` as `run`, the `verdict` given, its `findings` and, when it has checks, `checks` with one `origin` and `total` for each origin.
- **EVIDENCE-042** When a gate does not apply, the builder shall write its entry with `gate`, `status` as `not-applicable` and its `reason`.
- **EVIDENCE-043** When a finding is written, the builder shall write its `code`, its `verdict`, its `lines` and, in `untrusted`, the one entry with the `label` `message` and the whole message as its `text`.
- **EVIDENCE-044** If two gates of the run have the same name, then the builder shall refuse the run with an error that names the gate.
- **EVIDENCE-045** If a check names an origin other than `existing`, `human`, `derived` or `model`, or has a total below one, then the builder shall refuse the run with an error that names the check.

## What was not checked

- **EVIDENCE-060** When the run has a contract, the builder shall list in `not_checked` one entry `no-holdout` for each requirement, with the requirement in `what`.
- **EVIDENCE-061** When a requirement of the contract has no example, the builder shall list in `not_checked` one entry `requirement-without-example`, with the requirement in `what`.
- **EVIDENCE-062** When every example of a requirement is of origin `model`, the builder shall list in `not_checked` one entry `only-model-checks`, with the requirement in `what`.
- **EVIDENCE-063** When a gate that ran left out unstable tests, the builder shall list in `not_checked` one entry `test-excluded-unstable` for each, with the gate in `what` and the name of the test in `untrusted` with the `label` `test`.
- **EVIDENCE-064** When a gate that ran found unstable examples, the builder shall list in `not_checked` one entry `example-unstable` for each, with the example in `what`.
- **EVIDENCE-065** When the gate `existing-tests`, `baseline` or `visible-examples` ran, the builder shall list in `not_checked` one entry `outside-threat-model` for it, with the gate in `what`.
- **EVIDENCE-066** The builder shall list `not_checked` by code in the order `no-holdout`, `requirement-without-example`, `only-model-checks`, `test-excluded-unstable`, `example-unstable`, `outside-threat-model`, the entries of each code in the order of the requirements or of the gates.
- **EVIDENCE-067** When an entry of `not_checked` is listed, the builder shall give it a `reason` in words of its own for its code.

## Reading the bytes back

- **EVIDENCE-080** When bytes of evidence are read back, the reader shall give no finding for the bytes that the builder gives for a run.
- **EVIDENCE-081** If the bytes are not JSON in UTF-8, or hold a repeated key, a number that is not whole, `NaN` or an infinity, then the reader shall report a finding with the code `evidence-not-json` and the verdict `ERROR`.
- **EVIDENCE-082** If the bytes are JSON but differ from the canonical form of their value, then the reader shall report a finding with the code `evidence-not-canonical` and the verdict `ERROR`.
- **EVIDENCE-083** If a field of the statement is unknown, a required field is missing, or a field holds `null`, a value of another type, or a value outside its closed list or its pattern, then the reader shall report a finding with the code `evidence-schema` and the verdict `ERROR` that names the place of the field.
- **EVIDENCE-084** When the bytes break the schema in more than one place, the reader shall report one finding for each place, in the order of the statement.
- **EVIDENCE-085** If the bytes that the builder gives for a run do not read back without a finding, then the builder shall refuse the run with an error that lists the findings.
- **EVIDENCE-086** If no gate of the predicate ran, or its verdict is not the one that the precedence of [ADR-0015](../adr/0015-a-gate-returns-one-of-four-verdicts.md) gives over the verdicts of the gates that ran, then the reader shall report a finding with the code `evidence-schema` and the verdict `ERROR` that names `predicate/verdict`.
