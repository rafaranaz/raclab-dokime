# ADR-0075 · The predicate v0.3 records the hold-out

**Status:** accepted

## Context

In block B the gate `sealed-examples` runs where the key of the hold-out is
([ADR-0073](0073-the-key-of-the-hold-out-lives-outside-ci-until-b4.md)): it reads the sealed batch,
checks it against the contract and the history of the contract, and observes the held-out examples
and the canary on the tree of the change. The predicate v0.2
([ADR-0069](0069-the-predicate-v0-2-adds-what-a4-records.md)) has no place for what the reader of
the evidence needs to tell a pass with a hidden part from a pass without one:

- **which cases hold out an example and which do not**, and why: a case of a single example has
  nothing to hold out, and a case whose examples were all published before the seal keeps them all
  visible
  ([ADR-0014](0014-hidden-checks-are-held-out-approved-examples.md));
- **which examples were kept visible** as already published;
- **which sealed batch** the gate checked.

`not_checked` of v0.1 and v0.2 has the code `no-holdout`, one entry for each requirement with the
reason "There are no sealed examples until block B"
([ADR-0064](0064-the-evidence-of-a3-is-an-unsigned-statement-with-a-closed-predicate.md)). Its
grain is the requirement, and a hold-out is decided by case. Its closed list also has the code
`best-effort-secrecy`, with no row that says when it is written.

The hold-out has two parts of different strength. **The barrier** is what dokime does and checks:
the command that seals never writes a held-out example into the tree of the project; the batch is
encrypted for the recipients of the base
([ADR-0072](0072-the-sealed-store-is-encrypted-with-age-for-a-list-of-recipients.md)) with a key
outside CI; the agent never receives a value, an input or the identifier of a held-out example; the
gate checks that the batch is the one that the contract names, by the salted digest of each held-out
example, by the split drawn again from the seed, by its base in the history of the change and by the
examples kept visible drawn again from that base; and the canary detects a comparison that accepts
an expectation that cannot hold. **The detection of a held-out example already published** is best
effort: it reads the versions of the contract of the story in the history, and has limits.

## Decision

**The rule.** The evidence of a sealed run says, case by case, whether the case has a hidden part
and why not, without a value of any example; it lists as not checked each limit of the detection of
what was published. The barrier is not listed as not checked, since the gate checks it: a broken
barrier is a finding of the gate, `sealed-batch-mismatch` or `canary-passed`; and a held-out example
that the detection finds published is a finding too, `held-out-published`.

**The mechanism in B1.** The predicate type
`https://github.com/rafaranaz/raclab-dokime/attestation/conformance/v0.3` is the closed schema of
v0.2 with these additions, each absent when the run does not fill it, never `null`; the rule of
ADR-0069 holds: no field and no code of an earlier version changes what it means.

| Addition | What it holds |
|---|---|
| `holdout` of the gate `sealed-examples` | Present when the gate observed, that is, when the batch passed its checks. `batch`, the digest `sha256:` of the bytes of `sealed.age`; `held`, each case that holds out an example, as `{requirement, case}`; `kept_visible`, the ids of the examples kept visible as already published; `without_holdout`, each case that holds out nothing, as `{requirement, case, motive}`, with `motive` one of `single-example` and `all-published`. Each list in the order of the contract. No id of a held-out example, no value, no input. |
| The code `case-without-holdout` of `not_checked` | One entry for each case of `without_holdout`: the requirement in `what`, the case in a new field `case`, and as its reason "the case has a single example" or "every example of the case was published before the seal". |
| The row of `best-effort-secrecy` of `not_checked` | When the gate observed, one entry for each limit of the detection, with `sealed-examples` in `what`: the content of an example is compared as YAML reads it, so one published with a field added or a value spelt otherwise is not recognised; a version under an earlier path, after a rename, is not read; a commit that only other refs reach is not read; a copy of an example in another file is not looked for; and the audit reads the history up to the base of the pull request, so a held-out example published in a commit of the pull request and taken back in another is not seen by that audit: a project that merges keeping the commits, by rebase or by a merge commit, has the next audit see it, and with a squash merge no audit does. |

- **One code, one grain.** The builder of v0.3 does not write `no-holdout`, which keeps its meaning
  of v0.1 and v0.2, one entry per requirement, in the files of those versions. A case without a
  hidden part is `case-without-holdout`.
- **Where the key is not**, the gate is not applicable with the reason `the key is not here`
  (VERIFY-167), and the evidence has no `holdout`, no `case-without-holdout` and no
  `best-effort-secrecy`: nothing of the hold-out was checked, which the gate says once. The cases
  without a hidden part are not listed either, although the visible contract would tell them:
  listing them would report a coverage that the run does not have. A run that stopped before the
  gate lists it as not reached, likewise.
- **The order of `not_checked`** is that of EVIDENCE-066 with `case-without-holdout` in the place of
  `no-holdout` and `best-effort-secrecy` last; the entries of `case-without-holdout` in the order
  of the cases in the contract, and those of `best-effort-secrecy` in the order of the table.
- `evidence` writes v0.3 from B1 on; its reader reads each file with the schema of its own version
  and refuses any other predicate type.

## Basis

Reasoning, without a test of its own. The grain of the hold-out is the case (ADR-0014), so the
evidence has to name the case; a code with one grain per version keeps every older file meaning what
it meant, which is the rule of ADR-0069. The cases and the ids are names that the strict reader of
the contract checks against their pattern, so they are trusted fields (ADR-0064). The limits are
those that the requirements of `platform` and `verify` already state; the evidence only lists them.
The test is the reader of `evidence`, which reads back a file of each version, and a run of the gate
whose evidence lists each case of the contract once, in `held` or in `without_holdout`.

## Alternatives considered

- **`no-holdout` by case in v0.3.** It would change what a code of an earlier version means, which
  ADR-0069 forbids, and a reader that counts `no-holdout` across versions would mix requirements
  and cases. Amending the rule of ADR-0069 for it was considered and discarded: the rule is what
  lets a reader trust that a code means one thing.
- **`no-holdout` by case where the key is and by requirement where it is not.** Two grains for one
  code in one version; the absence of the key is already the reason of the gate.
- **Only `not_checked`, without `holdout`.** `not_checked` lists what was not checked; the cases
  that do hold out an example, the examples kept visible and the digest of the batch would have no
  place, and the reader could not tell a case with a hidden part from one that the evidence forgot.
- **The ids of the held-out examples in `holdout`.** The contract names them in `held_out`; the
  evidence needs the case, and an id adds nothing that the reader of the evidence uses.
- **One entry of `best-effort-secrecy` with every limit in its reason.** A reader could not count
  the limits, nor a later version remove one when it is covered.
- **The barrier as entries of `not_checked`.** It is checked, by the gate, and its failures are
  findings; listing it as not checked would say the opposite.

## Consequences

- The reader of `evidence` keeps three schemas, one per version, and the closed list of the codes of
  `not_checked` differs by version: `case-without-holdout` is not a code of v0.1 or v0.2.
- `evidence` needs, from the run, the cases, the examples kept visible and the digest of the batch:
  the gate of `verify` has to hand them over, which `interfaces` carries into the run.
- An evidence of a run without the key says nothing of the hold-out but the reason of the gate. The
  cases without a hidden part could be told without the key, since the entries of `held_out` of the
  visible contract name the cases that hold out an example, and the number of visible examples of
  each other case gives its motive; they are not listed, because nothing of the hold-out was checked
  in that run, and the gate already says so once with its reason: listing them would report a
  coverage that the run does not have.
- The limits of the detection are written in three places: the requirements of `verify`, its
  README, and the evidence. A change of the detection changes all three.
- The table of the architecture in `03-data-and-evidence.md` has to name `case-without-holdout`
  and the field `holdout`, in a pull request of the architecture.
