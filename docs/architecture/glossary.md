# Glossary

*Leer en [español](glossary.es.md).*

The terms the invariants and the decisions rely on. A term has one meaning in every document; if
a decision needs another meaning, it needs another term.

## The harness and what it verifies

| Term | Meaning |
|---|---|
| Harness | This program. It runs on the machine of whoever uses it or in a job of a pipeline, outside every container, and it starts the containers it needs |
| Verified project | The repository whose change is checked. Its code and its tests run inside a container. The harness is not part of it |
| Pack | The data that tells the harness how to build the environment of a verified project and how to run its tests. It says nothing about how the harness itself is built |
| Environment | The container image where the code of a verified project runs, built as its pack says |
| Prepare | The phase that builds the environment of a verified project. It may download its dependencies |
| Verify | The phase that runs the code of a verified project in its environment, without network |
| Self-check of a pack | The proof that a pack really runs the tests: on a past commit of the project that fixed a defect and added a test, that test fails before the fix and passes after it |
| Pipeline of the project | The continuous integration of a verified project. It is a source for writing its pack. It is not the pipeline where the harness is tested |
| Memory | What the harness keeps about a verified project between runs: its pack and policy, the contract of each change, the state of the work. A store of its own, on local disk or in its own git repository, never inside the repository of the verified project |
| Corpus | The verified projects and their changes, each with a known verdict, that are used to measure the harness |

## Contract and examples

| Term | Meaning |
|---|---|
| Contract | The requirements of a change and its approved examples, with a digest. A person approves it |
| Example | An input and what is expected to be observed, at a declared boundary |
| Case | The label that groups the examples of one situation of a requirement |
| Approved example | An example a person approved. Before approval it is a proposal |
| Split | The moment, when the contract is approved, at which the harness holds out part of the approved examples at random |
| Visible example | An approved example the agent receives |
| Held-out example | An approved example the split set apart. The agent never receives it |
| Held-out content | The input or the expected value of a held-out example, **in clear**. The encrypted form is not held-out content |
| Sealed batch | The held-out examples of a contract, encrypted, with their seed and their canary |
| Sealed store | Where sealed batches are kept: an encrypted file in the repository |
| Sealed run | The execution of the held-out examples. It happens only when the visible ones pass |

## Places

| Term | Meaning |
|---|---|
| Work session | Everything the agent can read while it works: the working tree, the task files and its own installation |
| State directory of the harness | Where the harness keeps the ledger, the key when it is local, and its working files. It is not part of the work session when a barrier is in place |
| Barrier when specifying | What separates the place where a contract is specified from the agent: another machine, the wrapper, another system user, or none. The evidence records it |

## Checks and verdicts

| Term | Meaning |
|---|---|
| Check | One comparison between what was observed and what was expected |
| Origin | Who stands behind the expected result of a check: `human`, `derived`, `model` or `existing` |
| Gate | A step of the flow that returns a verdict |
| Work state | A state of the flow that runs one or more gates and closes with their aggregated verdict |
| Question state | A state of the flow in which a person chooses one of a closed list of answers |
| Budget | How many times a transition of the flow may repeat before a person is asked. It ends nothing by itself. The amount is in the policy |
| Optional gate | A gate the policy allows to skip. Every other gate is mandatory |
| Verdict | `PASS`, `FAIL`, `ASK` or `ERROR`. A gate returns one; the verdict of a change is their aggregation |
| Finding | One problem found by a check: a code from a closed list, a message, the lines where it is, and the verdict it gives (`FAIL`, `ASK` or `ERROR`) |
| Directive | A mapping in a contract with a key that starts with `$`. It is an instruction to the harness, not data |
| Not applicable | A gate that has nothing to act on in this change, by a condition read from the contract or from the level of the pack |
| Not reached | A gate the flow did not get to, because an earlier gate stopped it |
| Final state | A state of the flow with no gate and no transition. It either delivers or it does not |
| Identity | Who took a human decision, together with how that was established: signed, declared, or through a client and unverified |
| Replay | Recomputing the verdict of a run from its ledger and stored artifacts, without asking anyone |
| Delivery | Producing the commit of a change and attaching its evidence. Only a state of the flow that delivers can do it. Evidence exists for every finished run, delivered or not |
| Delegated answer | An answer to an interview question that a person left to a model. It is marked, and it never approves an example or a contract nor answers a gate |
