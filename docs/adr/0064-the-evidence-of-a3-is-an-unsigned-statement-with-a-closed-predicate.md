# ADR-0064 · The evidence of A3 is an unsigned statement with a closed predicate

**Status:** accepted

## Context

[ADR-0023](0023-evidence-is-an-attestation-bound-to-the-tree.md) decides that the evidence is an
in-toto statement in a DSSE envelope, with a predicate of our own, and leaves as a consequence that
"the fields of the predicate have to be fixed before the first block writes evidence". A3 is that
block: `audit` verifies a change that arrives already made and writes its evidence. The signatures
are of block E, and so are the approvals of contracts. Several fields of the example of
[`03-data-and-evidence.md`](../architecture/03-data-and-evidence.md#the-evidence) have nothing to
hold in A3: there is no agent, no attempt, no sealed example, no flow file and no repeated run.

The findings of the gates quote text that dokime did not write: the observed and expected values of
an example, the names of tests, paths of the patch. From A4 the evidence goes to pull requests,
where people and agents read it, and a quoted value can carry Markdown or instructions for a model
(T3 of [ADR-0010](0010-threat-model.md)).

## Decision

**The envelope and the file.**

- **In A3 the evidence is the in-toto Statement v1 alone, without an envelope.** The DSSE envelope
  and its signatures arrive with block E.
- **The file is named `<story>.statement.json`.** The suffix `.intoto.jsonl` is kept for the
  bundles of signed envelopes of block E.
- **Its bytes are the canonical form of
  [ADR-0062](0062-a-digest-is-taken-over-a-restricted-canonical-json.md)**, and the event
  `evidence.built` of the ledger holds the digest of those bytes.
- **The module `evidence` builds the bytes and reads them back against its schema**; the module
  that writes them puts them outside the tree they describe, as `03-data-and-evidence.md` says.
- **The command that verifies an evidence file is built in block E**, since the first thing it
  checks is the signatures.

**The statement.**

- **`subject`** holds the tree, as `{"gitTree": …}`, and `change.patch`, as `{"sha256": …}`. The
  tree is that of the base with the whole patch applied, the result of the change. It is not the
  composed tree of [ADR-0058](0058-existing-tests-runs-the-tests-of-the-base-on-the-code-of-the-patch.md),
  which is how a gate runs.
- **`predicateType`** is `https://github.com/rafaranaz/raclab-dokime/attestation/conformance/v0.1`.

**The predicate v0.1 has a closed schema.** An unknown field is refused. A field that A3 cannot
fill is absent, never `null`. A field the run did not reach is also absent, such as the image when
the environment could not be built; the gate whose finding stopped the run says why.

| Field | In A3 |
|---|---|
| `verdict` | The verdict of the aggregation of the state ([ADR-0015](0015-a-gate-returns-one-of-four-verdicts.md)). |
| `delivered` | `false`: `audit` delivers nothing. |
| `independence` | `self-attested`. |
| `verifier` | `harness`, the version of the package, and `ran_on`, `developer`. |
| `contract` | `story`, and `digest`: `sha256:` and the SHA-256 of the bytes of the contract file. `approval` is absent until block E. |
| `inputs.base` | The name of the base commit. |
| `inputs.image` | `digest`, of the image built, and `platform`, the digest of the manifest of the platform of the base image as the runtime gives it; `platform` is absent when the final stage starts from `scratch`. |
| `inputs.pack` | `digest`, `sha256:` and the SHA-256 of the bytes of the pack file. `level` is absent until the levels exist. |
| `inputs.policy` | `digest`, of the normalised form of the effective policy, and `source`, `file` or `defaults` ([ADR-0054](0054-the-policy-is-an-optional-file-of-values.md)). |
| `inputs.probe` | The digest of the program that observes the examples ([ADR-0063](0063-a-program-of-sandbox-observes-the-examples-inside-the-zone.md)). |
| `gates` | Every gate of the state, in its order, as the aggregation lists it. |
| `human_decisions` | `[]`. |
| `not_checked` | Mandatory, filled mechanically. |
| `ledger` | `head`, the hash of the last event before `evidence.built`, and `events`, how many there are up to it. |

`author`, `attempts`, `repeated`, `inputs.flow`, `inputs.seeds` and `informative` are absent in A3.
Each one arrives with the block that has something to put in it, and the version of the predicate
changes then.

**Each gate.**

- A gate that ran has `gate`, `status: "run"`, its `verdict` and its `findings`. It also has
  `checks`, one entry for each origin with the number of its checks (`existing` for the tests;
  `human`, `derived` or `model` for the examples), when the gate runs checks.
- A gate that does not apply has `gate`, `status: "not-applicable"` and its `reason`.
- A finding has `code`, `verdict`, `lines` and `untrusted`.
  - **The part of a finding that can be trusted is what dokime fixes**: its `code`, its `verdict`
    and its `lines`. In the rest of the predicate, so are the identifiers that the strict reader of
    the contract has checked against its pattern, such as the story and the ids of requirements
    and examples.
  - **`untrusted` holds texts that may carry what dokime did not write**, as a list of
    `{label, text}`. The label is a word of dokime. The text is data, and whoever shows it must
    escape it.
  - **In A3 the whole message of a finding goes to `untrusted`, with the label `message`**, since
    the messages of the modules mix the words of dokime with text quoted from the contract, the
    tree, the patch or what ran in the zone.

**What was not checked in A3.** Each entry has `code`, `what`, `reason` and, when it names
something dokime did not write, `untrusted`.

| Code | One entry for | Reason |
|---|---|---|
| `no-holdout` | Each requirement | There are no sealed examples until block B. |
| `requirement-without-example` | Each requirement without an example | From the contract. |
| `only-model-checks` | Each requirement whose examples are all of origin `model` | From the contract. |
| `test-excluded-unstable` | Each test whose outcome varied between the runs of the base; its name goes in `untrusted` | [ADR-0017](0017-damage-outside-the-change-against-a-baseline.md). |
| `example-unstable` | Each example whose outcome varied between the runs of the base | A new code of the list, which the architecture says "starts with" the codes it names. |
| `outside-threat-model` | `existing-tests` | The tests run in the process of the code under test ([ADR-0010](0010-threat-model.md)). |
| `outside-threat-model` | `baseline` and `visible-examples`, one entry each | The code under test runs in the process that observes it, and can rewrite what is observed ([ADR-0063](0063-a-program-of-sandbox-observes-the-examples-inside-the-zone.md)). |

## Basis

Verified in the specifications:

- An [in-toto Statement v1](https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md)
  requires `_type`, `subject`, each entry with its `digest`, and `predicateType`. The `predicate`
  is optional.
- [`gitTree`](https://github.com/in-toto/attestation/blob/main/spec/v1/digest_set.md) is a digest
  algorithm of the list, in lowercase hexadecimal, valid for any tree.
- A DSSE envelope without signatures does not verify. The
  [protocol](https://github.com/secure-systems-lab/dsse/blob/master/protocol.md) rejects when the
  accepted keys are fewer than the threshold, and the
  [validation model](https://github.com/in-toto/attestation/blob/main/docs/validation.md) of in-toto
  rejects when there are no attesters. Some implementations build an empty envelope as a step
  before signing ([atlas-cli](https://docs.rs/atlas-cli/0.3.0/src/atlas_cli/in_toto/dsse.rs.html)),
  and others refuse it when they verify
  ([nono](https://docs.rs/crate/nono/0.42.0/source/src/trust/dsse.rs)).
- The [bundle specification](https://github.com/in-toto/attestation/blob/main/spec/v1/bundle.md)
  says that "Bundles SHOULD use the suffix `.intoto.jsonl`" and that each line "SHOULD be an
  Envelope". The session that reviews the work found tools that already name a DSSE envelope
  `<sha>.intoto.json`.
- The [verification summary of SLSA](https://slsa.dev/spec/v1.1/verification_summary) has only
  `PASSED` and `FAILED` and no place for what was not checked, as the architecture already said.

Looked for and not found: a specification or a tool that defines how an unsigned statement is kept
as a final file. The specification neither forbids it nor describes it.

Reasoning, without a test:

- **The name.** A statement named `.intoto.json` would look signed to a reader and to tools of the
  ecosystem.
- **Absent and not `null`.** A `null` can be read as "checked and empty", and the schema stays
  closed either way.
- **The whole message in `untrusted`.** Whoever shows the evidence escapes that field and shows
  as they are only the fields that dokime fixes, instead of guessing which part of a text came
  from the code under test. The cost is that the words of dokime are escaped too.
- **`ran_on` is `developer`.** Nothing tells a run in CI apart until the independence
  `ci-verified` exists.
- **The digest of the contract and of the pack is that of their bytes.** That is what a person
  reads and, in block E, approves. Neither has a normalised form, and the canonical form of
  ADR-0062 is for values, not for files.

The test that would confirm the decision is a verifier of in-toto reading the statement once
block E wraps it in an envelope. It runs in block E.

## Alternatives considered

- **A DSSE envelope with `signatures: []`.** It looks like a signed format, and every verifier
  rejects it.
- **The name `<story>.intoto.json`.** It suggests a signed envelope, which is what the first
  alternative discards.
- **JSON with readable formatting.** Its digest would depend on how it is formatted, and the ledger
  would hold a digest of bytes that have a second encoding.
- **Every field present, with `null` where it does not apply.** A `null` reads as an answer.
- **Only the verdict of each gate, as in the example of the architecture, with the reasons in the
  ledger.** A `FAIL` without its reason is of little use in a pull request, and the ledger is not
  next to it.
- **The findings with the quoted text inside a trusted `message`, as today.** Whoever shows them
  cannot tell what to escape.
- **The fine separation now: a `message` with only the words of dokime, and each module passing the
  text it quotes to `untrusted`.** It is the better form, and it costs a change of `Finding` in
  `core` and seven pull requests, one for each module whose findings quote text that dokime did not
  write: `contract`, `packs`, `oracle`, `sandbox`, `platform`, `verify` and `interfaces`. It is
  left for later: in A4, when the evidence is shown in pull requests, or in each module when it is
  touched for another reason.
- **The verification summary of SLSA as the predicate.** It has no place for what was not checked.
- **The command that verifies, built now without signatures.** Half of what it checks would wait
  for block E, and its interface would change then.

## Consequences

- The predicate v0.1 is fixed for A3. A block that adds a field changes the version, and an evidence
  file of v0.1 stays readable as such.
- The evidence of A3 is not signed, so anyone can write one by hand. It says `self-attested`, and T6
  of ADR-0010 stays outside the threat model.
- `Finding` in `core` and the modules that quote do not change in A3. The fine separation of the
  message is noted in the roadmap, before A4.
- The result of a gate in `verify` gains its checks by origin.
- `audit` writes the file outside the tree. Where it writes by default is decided in `interfaces`.
- The verification of an evidence file waits for block E. Until then, `evidence` only reads back what
  it writes.
