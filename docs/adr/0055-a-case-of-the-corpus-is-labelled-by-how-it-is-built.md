# ADR-0055 · A case of the corpus is labelled by how it is built, and confirmed before it runs

**Status:** proposed

## Context

The harness is measured on a corpus with known verdicts
([ADR-0030](0030-the-harness-is-measured-on-a-corpus-with-known-verdicts.md)). The exit criterion
of milestone A3 is measured on the first ten cases of the corpus, labelled before they are run.
The same people who build the harness write the cases, so a case can be bent, without anyone
meaning to, towards what the harness already does. A label decided after seeing what the harness
said measures nothing.

## Decision

- **What a case is.** A project at a base commit, named by its repository and its full commit as in
  `tests/corpus/<project>/source.toml`; a contract of EARS requirements and examples
  ([ADR-0011](0011-contract-of-requirements-and-approved-examples.md)); a patch; and the expected
  verdict with its label from ADR-0030.
- **Where a case lives.** In `tests/corpus/<project>/cases/<case>/`, next to the pack of its
  project. CORPUS-001, which today allows only the pack, the Dockerfile and the source in the
  directory of a project, changes with it when the scope `corpus` opens in A3.
- **Where good patches come from.** From commits of the projects of the corpus that fixed code
  together with its test, whose test goes from red to green. The witnesses that the self-check of a
  pack finds ([ADR-0044](0044-the-packs-module-drives-the-self-check-in-an-order-of-its-own.md))
  are those commits. The base is the parent; the patch is the change of code that is not a test.
  The self-check stops at the second witness and does not record them, so it gives two for each
  project, six in all; with the patches derived from them that is enough for the ten cases of A3.
  Looking for witnesses past the second is needed when the corpus grows towards the thirty cases
  of [ADR-0030](0030-the-harness-is-measured-on-a-corpus-with-known-verdicts.md), in block B, and it
  is not built before.
- **Bad patches are derived from a good one**, one for each label that the exit criterion of A3
  names:
  - *fails a visible example*: a partial fix;
  - *edits tests*: the test that failed is changed or removed instead of the code;
  - *breaks existing tests*: the fix together with a regression elsewhere.

  The label follows from how the patch was built, not from what the harness says about it.
- **Who writes and who confirms.** The contract and the derived patches are drafted by an
  assistant session; the maintainer approves the contract and confirms the label.
- **Before a case runs for the first time**, it is merged into `main` with its label, and the
  maintainer has read its contract, its patch and its label and confirmed the verdict they expect.
  If the maintainer disagrees, the case is corrected or discarded before it runs. The minutes the
  maintainer spends on each case are recorded, as one of the metrics of ADR-0030.
- **A label never changes after the case ran.** A correction is a new case with its reason; the
  old one is kept and marked withdrawn.
- **A gate** checks that every case has a label and that the files of a case have not changed since
  the commit that added it. How the gate reads that from the history is a requirement of its scope.
- **Each case runs as many times as the policy says**
  ([ADR-0054](0054-the-policy-is-an-optional-file-of-values.md)); a case whose verdict varies is
  marked unstable, left out of the counts, and reported.

## Basis

Read:

- SWE-bench validates each task by the tests that go from failing to passing with the patch
  (FAIL_TO_PASS) and those that pass before and after (PASS_TO_PASS); a task needs at least one
  FAIL_TO_PASS, and validation is repeated, keeping only tasks with consistent results
  ([SWE-bench Goes Live](https://arxiv.org/pdf/2505.23419)).
- SWE-bench Verified had people screen each task with a written rubric and severity labels, and
  trained its annotators on fifty tasks labelled beforehand
  ([OpenAI](https://openai.com/index/introducing-swe-bench-verified/)).
- BugsInPy keeps a bug only if it is in source code, reproducible and isolated, and two authors
  checked isolation independently ([Widyasari et al.](https://www.arxiv.org/pdf/2401.15481)).
- Defects4J excludes tests that always fail and tests that fail intermittently
  ([Defects4J](https://github.com/rjust/defects4j)).

Measured: the self-check of the three packs found two witnesses in each on 2026-11-15, among 3, 3
and 6 candidates, so good patches exist in each project. Reasoning, without a test: that a label
fixed by construction and committed before the first run removes most of the bias of whoever builds
the harness. It does not remove all of it: the person who confirms the label is also the maintainer
of the harness.

## Alternatives considered

- **Patches written by real agents.** More realistic, and what the corpus grows with later; no
  agent runs under the harness until block C.
- **Labels decided after running.** They would fit the harness to its own output.
- **A second, independent person confirming every label.** Better; there is none yet. The
  published results say who labelled the cases.
- **A public benchmark.** Rejected by ADR-0030.

## Consequences

- The files of a case do not change once it is merged; the corpus only grows.
- A3 needs ten cases written, approved and confirmed before its first audit runs.
- The minutes of the maintainer per case are known from the first case.
- The published results state that the cases were labelled by the maintainer of the harness.
