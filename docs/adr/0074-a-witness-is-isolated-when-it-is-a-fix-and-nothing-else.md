# ADR-0074 · A witness is isolated when it is a fix and nothing else

**Status:** proposed

## Context

[ADR-0057](0057-the-cases-of-the-corpus-come-from-witnesses-that-fit-a-boundary.md) keeps a
witness as a good patch only if it is *isolated*, "its change of code is the fix, not a refactor
nor a change of the tooling of the tests", and *expressible* at a boundary of the contract. It
does not say whether a new feature, a deprecation or a release is a fix.

The measurement that closed block A read the 41 witnesses of the corpus twice, without either
reading seeing the other. They labelled alike 36 of 41 on expressible (κ 0.75) and only 33 on
isolated (κ 0.57), and the eight differences on isolated went the same way: the first reading took
isolated as "the change is a fix", the second as "the change is only the behaviour sought, with no
refactor nor tooling", which lets a feature in.

A set of real bugs such as Defects4J starts from commits that the bug tracker of the project already
links to a bug. The witnesses of the corpus carry no such label: a witness is a commit that touches
the tests and turns some of them green, whatever it is.

The strategic review at the close of block A recommended the definition of Defects4J; the maintainer
approved it and asked that this ADR say how a witness is decided to be a fix. The session that
reviews the work found the gap in the measurement; the decision is the maintainer's.

## Decision

This amends ADR-0057 in its filter *isolated*; the rest of it stands.

**The rule.** A witness is isolated when its change outside the tests is the fix of a behaviour and
nothing else: not a feature, a refactor, a deprecation, the removal of something supported, a
release or a change of the tooling.

**How a witness is decided to be a fix, by reading, in the corpus.** Four conditions, each read in
the commit and in its base; a witness is isolated when it meets all four, and its label names the
first it fails:

1. **The interface exists at the base.** The tests it turns green use only names, parameters,
   options and formats of files that the base already has. A test that fails at the base because
   one of them is missing means the witness adds a feature.
2. **The base is wrong.** At the base, what those tests check is wrong in one of three ways:
   - it contradicts what the project already said: its documentation, its docstrings or types, an
     issue that the commit references, or another behaviour of the same interface;
   - it is an error the project does not handle, an unexpected exception or a hang, on a valid
     input;
   - it breaks an external specification that the project declares it follows, such as SemVer 2.0
     for python-semver or CommonMark for mdformat.

   If none holds and the base documented the old behaviour as intended, or as unspecified, the
   witness changes a behaviour; it does not fix one.
3. **Nothing is taken away.** The change removes no supported behaviour, adds no deprecation and is
   not only a change of the version or of the packaging.
4. **Nothing else comes with it.** The diff outside the tests holds only the fix; a fix that comes
   with a feature, a refactor or tooling is tangled, and not isolated.

The message of the commit, or a label "fix" in its pull request, supports the reading but does not
decide it.

**The measurement gives two shares**, as the close of block A did: the witnesses that fit, isolated
and expressible, which is the share of real fixes that ADR-0057 asks for; and the witnesses that are
expressible whatever they are, since the hypothesis of A0 speaks of requirements and a feature is a
requirement too.

## Basis

Verified in [Defects4J](https://homes.cs.washington.edu/~rjust/publ/defects4j_issta_2014.pdf) (Just,
Jalali and Ernst, ISSTA 2014) and in its [README](https://github.com/rjust/defects4j):

- Among the requirements of each bug, in section 2: "The bug fix (i.e., the diff between Vbug and Vfix) does not include unrelated changes such as
  features or refactorings."
- Its candidates come from the link between a commit and the bug tracker: "the commit log references
  a bug id of the bug tracking system or 2) the bug tracking system references a commit id of the
  version control system."
- That label is not enough: "we encountered several types of fixes not related to the source code,
  or features, which were classified as a 'bug fix' by developers."
- Isolating is done by reading: "We manually reviewed the source code diffs of reproducible bugs to
  verify that they did not include irrelevant changes."; and its README says that each bug is
  "Minimized: the Defects4J maintainers manually pruned out irrelevant changes in the commit (e.g.,
  refactorings or feature additions)."

Measured at the close of block A (`tests/corpus/witnesses.toml`): the agreement of the two readings,
33, 36 and 38 of 41 for isolated, expressible and both (κ 0.57, 0.75 and 0.84).

Reasoning, without a test: that the four conditions make two readings agree on isolated more than
κ 0.57. The test, before block B widens the corpus: the eight witnesses where the two readings
differed on isolated are labelled again with these four conditions only, by two readers that do not
see each other. One is a new agent, which has not seen the earlier labels nor the debate on them,
as the first reading was made; the other is the session that reviews the work, whose note says that
it knew the debate. κ is computed again on the eight.

## Alternatives considered

- **The second reading, "only the behaviour sought".** Broader, and it lets a feature be a good
  patch, which is not what the share of real fixes of ADR-0057 counts and departs from the published
  reference.
- **The label of the project**: take as a fix the witness whose commit, or the issue it references,
  is labelled as a bug in its tracker. Many witnesses reference no issue, reading the tracker needs
  the network at each measurement, and Defects4J found features under that label; it supports the
  reading instead.
- **Minimize the patch by hand, as Defects4J does**, pruning from the commit the changes that are
  not the fix. The good patch of a case is the commit as it is, everything outside the tests
  (ADR-0057), and editing it would bring back the choice by hand that taking the cases from the
  witnesses removes.
- **Drop the filter.** The measurement would stop telling fixes from features, and a tangled patch
  would confuse what each gate of a case catches.

## Consequences

- The labels of a measurement name the first condition a witness fails, so that two readings can be
  compared condition by condition.
- The cases that block B adds to the corpus take their good patches from witnesses isolated by this
  definition.
- The labels of the close of block A stay as they were read; the test above relabels only the eight
  in dispute.
- Reading a witness takes longer: condition two asks for the documentation of the base, not only the
  diff.
