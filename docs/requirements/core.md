# Requirements of the `core` scope

Domain types that every module shares: the verdicts of a gate and the findings that explain them,
the strict reader of the files of the harness and the shape check, the ports of the project
repository and of the verification runtime, the canonical form that digests are taken over, the
policy, the ledger with the ports of its store and of the clock, the layout of a project, and the
port that observes the examples. Each requirement follows an EARS template and has at least one test
that declares it in its `SDD-EARS:` marker.

## Verdicts ([ADR-0015](../adr/0015-a-gate-returns-one-of-four-verdicts.md))

- **CORE-001** The verdict type shall have exactly the values `PASS`, `FAIL`, `ASK` and `ERROR`.
- **CORE-002** When any verdict of a round is `ERROR`, the aggregation shall return `ERROR`.
- **CORE-003** When no verdict of a round is `ERROR` and any is `FAIL`, the aggregation shall return `FAIL`.
- **CORE-004** When no verdict of a round is `ERROR` or `FAIL` and any is `ASK`, the aggregation shall return `ASK`.
- **CORE-005** When every verdict of a round is `PASS`, the aggregation shall return `PASS`.
- **CORE-006** If a round has no verdicts, then the aggregation shall raise an error that says the round is empty.
- **CORE-007** The aggregation shall return the same verdict for any order of the same verdicts.

## Findings

A finding is one problem found by a check. Its verdict is `FAIL`, `ASK` or `ERROR`.

- **CORE-010** The finding shall carry a code, a message, a verdict and a list of lines, which may be empty.
- **CORE-011** If a finding is given the verdict `PASS`, then the finding shall be rejected with an error naming the verdict.
- **CORE-012** If a finding has an empty code or an empty message, then the finding shall be rejected with an error naming the empty field.
- **CORE-013** When a list of findings is summarised, the summary shall be the aggregation of their verdicts.
- **CORE-014** When a list of findings is empty, the summary shall be `PASS`.
- **CORE-015** If a finding code is not made of words of lowercase letters and digits joined by hyphens, starting with a letter, then the finding shall be rejected with an error naming the code.
- **CORE-016** If a finding has a line smaller than 1, then the finding shall be rejected with an error naming the line.

## Strict reading ([ADR-0037](../adr/0037-a-contract-is-read-by-strict-rules-of-its-own.md))

The reader receives the text of a contract or of a flow file. It does not open files. The library
only parses; the rules below decide what the text means. Every finding of the reader has one of
the codes named here.

- **CORE-020** When a text is read, the reader shall return the value the text holds together with every finding of the text.
- **CORE-021** The reader shall give the verdict `FAIL` to every finding it reports.
- **CORE-022** If a text is not YAML, then the reader shall return no value and a single finding with the code `not-yaml` and the line of the error.
- **CORE-023** If a text does not hold exactly one document, then the reader shall return no value and a finding with the code `not-one-document`.
- **CORE-024** If a text has an anchor or an alias, then the reader shall return no value and a finding with the code `anchor-or-alias` for each of them, with its line.
- **CORE-025** If a node has an explicit tag, then the reader shall report a finding with the code `tag` and the line of the node.
- **CORE-026** If a mapping has the key `<<` without quotes, then the reader shall report a finding with the code `merge-key` and the line of the key.
- **CORE-027** If a key is a sequence or a mapping, then the reader shall report a finding with the code `key-not-text` and the line of the key.
- **CORE-028** The reader shall read every key as a text, as it is written.
- **CORE-029** If a key appears more than once in a mapping, then the reader shall report one finding with the code `duplicate-key` that names the key and lists every line where it appears.
- **CORE-030** When a value without quotes is `true` or `false`, the reader shall read it as a boolean.
- **CORE-031** When a value without quotes is `null`, the reader shall read it as null.
- **CORE-032** When a value without quotes is a number in the form JSON writes it, the reader shall read it as a number.
- **CORE-033** If a value without quotes has one of the forms of the table of ambiguous values, then the reader shall report a finding with the code `ambiguous-value` and the line of the value.
- **CORE-034** If a number without quotes has two or more decimals and the last one is zero, then the reader shall report a finding with the code `ambiguous-value` and the line of the value.
- **CORE-035** When a value without quotes has none of the forms above, the reader shall read it as a text.
- **CORE-036** When a value is in quotes, the reader shall read it as a text.
- **CORE-037** If a scalar is a folded block or continues on another line without being a literal block, then the reader shall report a finding with the code `text-on-several-lines` and the line where the scalar starts.
- **CORE-038** If the value of a literal block does not end in exactly one newline, then the reader shall report a finding with the code `block-ending` and the line where the block starts.
- **CORE-039** If a line of a literal block ends in a space or a tab, then the reader shall report a finding with the code `trailing-whitespace` and that line.

- **CORE-040** When a text is read, the reader shall give the line where every key of a mapping and every item of a sequence starts, addressed by its path from the root.
- **CORE-041** If a key appears more than once in a mapping, then the reader shall give for its path the line of the occurrence whose value it keeps.

- **CORE-042** When a text is read, the reader shall give the paths of the values that are written as literal blocks.

### Table of ambiguous values

A value without quotes in one of these forms is read with different types by different YAML
readers, so the reader rejects it and asks for quotes.

| Form | Examples |
|---|---|
| Words that some readers read as booleans or null, in any case | `yes`, `no`, `on`, `off`, `y`, `n`, `True`, `FALSE`, `Null`, `~` |
| An empty value | `key:` |
| A number with leading zeros | `010`, `-007` |
| Hexadecimal, octal and binary forms | `0x10`, `0o10`, `0b10` |
| Digits with underscores | `1_000` |
| A number with a leading `+` or a bare dot | `+1`, `.5`, `1.` |
| Infinities and not-a-number | `.inf`, `-.inf`, `.nan` |
| Dates and times | `2026-11-10`, `2026-11-10T10:00:00Z`, `12:30` |

## The shape of what was read

A check of a file that was read (a contract, a pack, a flow) compares each of its mappings with a
table of fields: which fields the mapping may have, which are mandatory and what each holds.

- **CORE-050** If a mapping has a field that its table does not list, then the shape check shall report a finding with the code `unknown-field` that names the field, with its line.
- **CORE-051** If a mapping lacks a field that its table marks as mandatory, then the shape check shall report a finding with the code `missing-field` that names the field, with the line of the mapping.
- **CORE-052** If the value of a field is not what its table states, then the shape check shall report a finding with the code `wrong-type` that names the field, with its line.
- **CORE-053** If a field with a closed list of values has a value that is not in the list with the same type, then the shape check shall report a finding with the code `unknown-value` that lists the values allowed, with its line.
- **CORE-054** When a finding is about a part that has no line of its own, the shape check shall give the line of the nearest part that contains it.

## The port of the project repository ([ADR-0042](../adr/0042-a-port-of-the-project-repository-composes-the-trees-that-are-built.md), [ADR-0044](../adr/0044-the-packs-module-drives-the-self-check-in-an-order-of-its-own.md))

`core` defines the port and the values it exchanges; it runs no `git`. What an adapter does with a
real repository (how it composes and extracts a tree, when it refuses and with which code) is
required in the scope of the adapters, for every adapter of the project repository, where it can
be tested. The order in which the self-check takes the commits of a history belongs to `packs`.

### Names and paths

- **CORE-060** The name of a commit and the name of a tree shall accept a text of 40 lowercase hexadecimal characters.
- **CORE-061** If the name of a commit or of a tree is not 40 lowercase hexadecimal characters, then the name shall be rejected with an error that quotes the text.
- **CORE-062** The name of a commit shall not be equal to the name of a tree with the same text.
- **CORE-063** The path of the repository shall accept a relative path whose parts are separated by `/`.
- **CORE-064** If a path of the repository is empty, starts or ends with `/`, has an empty part, has a part `.` or `..`, or has a NUL character, then the path shall be rejected with an error that quotes the path.
- **CORE-065** When a path of the repository is made from the bytes that a repository stores, the path shall decode them as UTF-8.
- **CORE-066** If the bytes of a path are not valid UTF-8, then the path shall be rejected with an error that quotes the bytes.

### What the port gives and takes

- **CORE-067** The port shall offer five operations: give the history from a commit, give the change of a commit, compose a tree from a commit with paths of another commit, compose a tree from a commit with a patch, and extract a tree to a directory.
- **CORE-068** The history from a commit shall carry every commit reachable from it, each with its commit date in whole seconds and its parents in the order the commit names them.
- **CORE-069** The change of a commit shall carry the name of the commit, the name of its one parent and the paths it changed.
- **CORE-070** The composition with paths of another commit shall receive the paths to take as a rule that says, for each path of the repository, whether it is taken.
- **CORE-071** The port shall return the name of the composed tree from each composition.

### The composition over a tree ([ADR-0058](../adr/0058-existing-tests-runs-the-tests-of-the-base-on-the-code-of-the-patch.md))

`existing-tests` runs the tests of the base on the code of the patch: the base with the patch
applied, a tree, with the paths of the tests taken from the base commit. The port that audits a
change extends the port of the project repository with that composition, so that the modules that
only self-check a pack and their doubles are not changed.

- **CORE-096** The port of the audited repository shall offer the operations of the port of the project repository and one more: compose a tree with paths of a commit.
- **CORE-097** The composition of a tree with paths of a commit shall receive the tree, the commit and the paths to take as the rule of CORE-070.
- **CORE-098** The composition of a tree with paths of a commit shall return the name of the composed tree.
- **CORE-099** The composed tree shall hold, under the paths that the rule takes, exactly the files of the commit, and elsewhere exactly the files of the tree.

### Refusals

A refusal is how an adapter says that it cannot do an operation. It is not an error of the
harness: the module that called the port adds its finding to its result, and the round ends in
`ERROR`.

- **CORE-072** When an adapter refuses an operation, the port shall raise a refusal that carries a finding with the verdict `ERROR`.
- **CORE-073** If a refusal is given a code or a message that a finding does not accept, then the refusal shall be rejected with the error of the finding.

## The outcome of a test run ([ADR-0045](../adr/0045-a-test-report-is-read-by-a-bounded-reader-that-refuses-any-dtd.md))

The adapter of the verification runtime reads the report of a run and gives these values to the
module that called it. They live in `core` because an adapter imports only `core`.

- **CORE-074** The outcome of a test shall be one of passed, failed, error and skipped.
- **CORE-075** The report of a run shall give, for the name of each test, its outcome.
- **CORE-076** The limits of reading a report shall carry the largest size of the report in bytes, the memory of the reader in bytes and the processor time of the reader in seconds.
- **CORE-077** The limits of reading a report shall default to 32 MiB for the report, 512 MiB for the memory of the reader and 10 seconds of processor time.
- **CORE-078** If a limit of reading a report is not a whole number greater than zero, then the limits shall be rejected with an error that names the limit.

## The port of the verification runtime ([ADR-0041](../adr/0041-the-environment-of-a-verified-project-is-a-dockerfile.md), [ADR-0043](../adr/0043-tests-run-only-on-an-engine-that-enforces-the-limits.md), [ADR-0045](../adr/0045-a-test-report-is-read-by-a-bounded-reader-that-refuses-any-dtd.md))

`core` defines the port and the values it exchanges; it runs no engine. What an adapter guarantees
while it runs (no network, the limits, a read-only root, how it tells a kill apart) and how it
finds the base image of a Dockerfile are requirements of the adapters. The port gives how a run
ended and does not decide a verdict: the module that called it does. Known limit: a project that
needs more than the default limits of a build or of a run cannot ask for them in this version.

### Digests

- **CORE-079** The digest of an image or of a manifest shall accept the text `sha256:` followed by 64 lowercase hexadecimal characters.
- **CORE-080** If the digest of an image or of a manifest is not `sha256:` followed by 64 lowercase hexadecimal characters, then the digest shall be rejected with an error that quotes the text.

### What the port gives and takes

- **CORE-081** The port shall offer three operations: build an image from a Dockerfile and a directory, run a command in an image, and read the report that a run wrote.
- **CORE-082** The build shall receive the Dockerfile, the directory it builds from and the limits of the build.
- **CORE-083** The build shall return the digest of the image it built and the base image of the final stage of the Dockerfile, or no base image when that stage starts from `scratch`.
- **CORE-084** The base image shall carry only the digest of the manifest of the platform that was built.
- **CORE-085** The run shall receive the digest of the image, the command as a list of arguments, the directory of the project, the output directory and the limits of the run.
- **CORE-086** The result of a run shall say how it ended: it exited by itself, it was killed when it reached the time limit, it was killed when it reached the memory limit, or it was killed for another reason.
- **CORE-087** The result of a run shall carry the exit code of the command when the run exited by itself, and no exit code otherwise.
- **CORE-088** The reading of a report shall receive the output directory, the path of the report inside it and the limits of reading, and give the report of the run.
- **CORE-089** When an adapter of the verification runtime refuses an operation, the port shall raise the refusal of CORE-072.

### The limits of a build and of a run

- **CORE-090** The limits of a build shall carry the time on the clock in seconds.
- **CORE-091** The limits of a build shall default to 1800 seconds.
- **CORE-092** If the time of a build is not a whole number greater than zero, then the limits of the build shall be rejected with an error that names the limit.
- **CORE-093** The limits of a run shall carry the memory in bytes, the number of processors, the number of processes and the time on the clock in seconds.
- **CORE-094** The limits of a run shall default to 2 GiB of memory, 2 processors, 512 processes and 900 seconds.
- **CORE-095** If the memory, the processes or the time of a run is not a whole number greater than zero, or the processors are not a finite number greater than zero, then the limits of the run shall be rejected with an error that names the limit.

## The canonical form ([ADR-0062](../adr/0062-a-digest-is-taken-over-a-restricted-canonical-json.md))

The canonical form is the JSON text of RFC 8785, restricted to the values of I-JSON (RFC 7493)
without decimals: texts, whole numbers, booleans, null, lists and mappings with text keys. The
place of a part is its path from the root, the keys and the positions that lead to it.

- **CORE-100** The canonical form of a value shall be its JSON text with no space between its parts.
- **CORE-101** The canonical form shall write the keys of every mapping in the order of their UTF-16 code units.
- **CORE-102** The canonical form shall write every character as itself except the quotation mark, the reverse solidus and the control characters below U+0020, which it escapes as RFC 8785 says.
- **CORE-103** If a value holds a number that is not a whole number, then the canonical form shall be refused with an error that names the place of the number.
- **CORE-104** If a value holds a whole number below −(2^53 − 1) or above 2^53 − 1, then the canonical form shall be refused with an error that names the place of the number.
- **CORE-105** If a text or a key holds a lone surrogate of UTF-16, then the canonical form shall be refused with an error that names its place.
- **CORE-106** If a value holds anything but a text, a whole number, a boolean, null, a list or a mapping whose keys are texts, then the canonical form shall be refused with an error that names its place.
- **CORE-107** The digest of a value shall be `sha256:` followed by the hexadecimal SHA-256 of its canonical form in UTF-8.
- **CORE-108** If a value holds lists or mappings nested more than 128 levels deep, then the canonical form shall be refused with an error that names the place where the limit is passed.

## The policy ([ADR-0054](../adr/0054-the-policy-is-an-optional-file-of-values.md))

The reader of the policy receives the text of `.dokime/policy.yaml`; it does not open the file.

| Mapping | Field | Mandatory | Holds | Default |
|---|---|---|---|---|
| Policy | `format` | Yes | The number 1 | — |
| Policy | `baseline` | No | A mapping | Its fields by default |
| Policy | `verification` | No | A mapping | Its fields by default |
| Policy | `relations` | No | A mapping | Its fields by default |
| Baseline | `runs` | No | A whole number of at least 2 | 2 |
| Verification | `runs` | No | A whole number of at least 2 | 2 |
| Relations | `permutations` | No | A whole number of at least 1 | 10 |

- **CORE-110** The reader of the policy shall read its text by the strict rules of CORE-020 to CORE-042, and check it against the table of fields of the policy with the shape check of CORE-050 to CORE-054.
- **CORE-111** If `runs` is a whole number below 2, then the reader of the policy shall report a finding with the code `wrong-type` that names the field, with its line.
- **CORE-190** If `permutations` is a whole number below 1, then the reader of the policy shall report a finding with the code `wrong-type` that names the field, with its line.
- **CORE-112** If the text of the policy has any finding, then the reader of the policy shall give no policy.
- **CORE-113** When a field of the policy that is not mandatory is absent, the reader of the policy shall give it its default.
- **CORE-114** When there is no policy file, the effective policy shall be the defaults of the table.
- **CORE-115** The effective policy shall say whether it came from the policy file or from the defaults.
- **CORE-116** The normalised form of the policy shall hold its format and every field of the table with its value, the defaults included.
- **CORE-117** The digest of the policy shall be the digest of its normalised form.

## The ledger ([ADR-0023](../adr/0023-evidence-is-an-attestation-bound-to-the-tree.md), [ADR-0062](../adr/0062-a-digest-is-taken-over-a-restricted-canonical-json.md))

The ledger of a run is a sequence of events, each one line of text. An event holds `seq`, `at`,
`type`, `prev` and `hash`, which are the fields of the ledger, and the fields of its type. `core`
writes it through the port of the ledger store and stamps it with the port of the clock; it opens
no file.

| Type | Records |
|---|---|
| `run.started`, `run.finished` | The digests the run starts from; the final state |
| `state.entered` | The state of the flow |
| `gate.started`, `gate.finished` | The gate, its status, its verdict and the digests of its inputs |
| `human.asked`, `human.answered` | The question; the answer, who gave it, how that was established, whether delegated |
| `model.called` | The registered prompt, the model and the digest of the output |
| `agent.started`, `agent.finished` | The agent profile, the model and the exit status |
| `baseline.unstable` | The tests excluded as unstable |
| `budget.exhausted` | The loop and the state that asks |
| `evidence.built` | The digest of the evidence |

### Writing

- **CORE-120** When an event is recorded, the ledger shall give it the sequence number after that of the last event, or 1 when there is none.
- **CORE-121** When the first event is recorded, the ledger shall give it a `prev` of null.
- **CORE-122** When an event after the first is recorded, the ledger shall give it as `prev` the `hash` of the event before it.
- **CORE-123** The `hash` of an event shall be the digest of the event without its field `hash`.
- **CORE-124** When an event is recorded, the ledger shall stamp it with the time the clock gives, written in UTC as `YYYY-MM-DDTHH:MM:SSZ`.
- **CORE-125** If the clock gives a time without a time zone, then the ledger shall refuse the event with an error and write nothing.
- **CORE-126** When an event is recorded, the ledger shall append through the port of the ledger store one line that is the canonical form of the event with its `hash`.
- **CORE-127** If the type of an event is not one of the table of types, then the ledger shall refuse the event with an error that names the type and write nothing.
- **CORE-128** If the fields of an event use the name of a field of the ledger, then the ledger shall refuse the event with an error that names the field and write nothing.
- **CORE-129** If the fields of an event have no canonical form, then the ledger shall refuse the event with the error of the canonical form and write nothing.
- **CORE-130** When the ledger is opened on a store that already holds events, the ledger shall continue the sequence and the chain from the last of them.
- **CORE-131** If the ledger is opened on a store whose events do not verify, then the ledger shall refuse to open with an error that gives the findings of the verification.

### Verifying

Each finding of the verification has the verdict `FAIL` and the number of its line.

- **CORE-135** When a ledger is verified whose lines were written by CORE-120 to CORE-126, the verification shall give no finding.
- **CORE-136** If a line is not a JSON object with the five fields of the ledger, of the types they hold, and a type of the table, then the verification shall report a finding with the code `not-an-event`.
- **CORE-137** If a line is not exactly the canonical form of the event it holds, then the verification shall report a finding with the code `not-canonical`.
- **CORE-138** If the `hash` of an event is not the digest of the event without it, then the verification shall report a finding with the code `wrong-hash`.
- **CORE-139** If the `prev` of an event is not the `hash` of the event before it, or is not null for the first, then the verification shall report a finding with the code `broken-chain`.
- **CORE-140** If the `seq` of an event is not the one after that of the event before it, or is not 1 for the first, then the verification shall report a finding with the code `wrong-sequence`.

### The head

The head of a ledger is what the evidence keeps of it, so that a ledger whose last events were
removed, or that was written again from the start, does not pass as the one the evidence describes.

- **CORE-141** The head of a ledger shall be the `hash` of its last event and the number of its events.
- **CORE-142** The head of a ledger without events shall have no hash and 0 events.
- **CORE-143** If the head of a ledger is asked for and its lines do not verify, then the head shall be refused with an error that gives the findings of the verification.
- **CORE-144** If a ledger is verified against an expected head and its head differs from it, then the verification shall report a finding with the code `wrong-head` that gives both heads.

### The ports of the ledger store and of the clock

- **CORE-145** The port of the ledger store shall offer two operations: append a line, and give the lines in the order they were appended.
- **CORE-146** The port of the clock shall offer one operation, which gives the current time with its time zone.

## The layout of a project ([ADR-0027](../adr/0027-memory-has-one-layout-and-three-scopes.md), [ADR-0054](../adr/0054-the-policy-is-an-optional-file-of-values.md))

The paths are relative to the root of the project. `core` gives them; it opens nothing. A story is a
name: a text of letters, digits and hyphens that starts with a letter, as the `story` of a contract.

- **CORE-150** The policy of a project shall be at `.dokime/policy.yaml`.
- **CORE-151** The directory of a change shall be `.dokime/changes/<story>/`, with the story of the change.
- **CORE-152** The contract of a change shall be the file `contract.yaml` in the directory of the change.
- **CORE-153** If a story is not a name, then the directory of the change shall be refused with an error that names the story.
- **CORE-172** The recipients of the sealed batches of a project shall be at `.dokime/recipients.txt`.
- **CORE-173** The sealed batch of a change shall be the file `sealed.age` in the directory of the change.

## The port that observes the examples ([ADR-0012](../adr/0012-examples-are-observations-at-a-boundary.md), [ADR-0063](../adr/0063-a-program-of-sandbox-observes-the-examples-inside-the-zone.md))

The zone of verification receives only the inputs of the examples and gives back what it saw; the
harness compares outside it. The port is apart from that of the verification runtime, which the
self-check uses.

| Boundary | What a step observes |
|---|---|
| `function` | The value returned, of any type that JSON holds, decimals included; or the exception raised, with the name of its class, its full name (module and qualified name), the full names of the classes of its MRO and its message; or the name of the type of a value returned that JSON cannot hold |
| `cli` | The exit code, the standard output, the standard error and the files the command wrote, by name, as texts |

- **CORE-160** The port that observes shall offer one operation: observe the examples of a list of requests in an image, with the directory of the project and the limits of observation.
- **CORE-161** The request of an example shall carry the identifier of its example, its boundary, its target and the inputs of its steps, and nothing of what is expected.
- **CORE-162** The observation of an example shall carry the identifier of the example and an observation for each step that ran, in the order of the steps.
- **CORE-163** The observation of a step at the boundary `function` shall be one of the three of the table.
- **CORE-164** The observation of a step at the boundary `cli` shall carry the four parts of the table.
- **CORE-165** When an example ends, the observation of the example shall say how it ended: it completed every step, it reached its limit of time, it reached its limit of output, or its process crashed.
- **CORE-166** The limits of observation shall carry the time of one example in seconds and the size of the observations in bytes, with the limits of a run for the whole.
- **CORE-167** The limits of observation shall default to 60 seconds for one example and 32 MiB of observations.
- **CORE-168** If the time of one example or the size of the observations is not a whole number greater than zero, then the limits of observation shall be rejected with an error that names the limit.
- **CORE-169** When an adapter of the port that observes refuses an operation, the port shall raise the refusal of CORE-072.
- **CORE-170** When the process of an example crashed, the observation of the example shall carry the signal that ended it, or its exit code, when they are known.
- **CORE-171** If an observation that did not crash carries a signal or an exit code, then the observation shall be rejected with an error that names the field.

## The sealed store ([ADR-0072](../adr/0072-the-sealed-store-is-encrypted-with-age-for-a-list-of-recipients.md), [ADR-0073](../adr/0073-the-key-of-the-hold-out-lives-outside-ci-until-b4.md))

The held-out examples of a contract are encrypted with age for the recipients of the project. The
file of recipients follows the format of age, one recipient per line, with empty lines and lines
that start with `#` ignored, and holds only X25519 recipients, the type of the identity that
ADR-0073 chose: `age1` and 58 characters of Bech32. `core` reads the text of the file, which the
caller takes from the base, and defines the port; it encrypts nothing.

- **CORE-180** When the text of a file of recipients is read, the reader shall give, in order, each line that is not empty and does not start with `#`, without the spaces around it.
- **CORE-181** If a line of a file of recipients is not an X25519 recipient of age, then the reader shall report a finding with the code `bad-recipient`, the verdict `ERROR` and the number of the line, without the text of the line.
- **CORE-182** If a file of recipients gives no recipient, then the reader shall report a finding with the code `no-recipient` and the verdict `ERROR`.
- **CORE-183** If a recipient appears more than once in a file of recipients, then the reader shall report a finding with the code `repeated-recipient`, the verdict `ERROR` and the numbers of its lines.
- **CORE-184** The port of the sealed store shall offer two operations: seal a content for a list of recipients and give the sealed bytes, and open sealed bytes and give their content.
- **CORE-185** When the sealed store cannot seal or open, the port shall raise a refusal that carries a finding with the verdict `ERROR`.

## The history of a file ([ADR-0014](../adr/0014-hidden-checks-are-held-out-approved-examples.md))

The hold-out holds out only examples that nobody has seen, so the command that seals and the gate
that checks the sealed batch read every version of the contract of a story that the history of a
commit holds. The port gives those versions; what counts as published is decided by whoever reads
them. Its limits are those of the history it reads: a version under an earlier path, after a
rename, is not given, and neither is one in a commit that the start does not reach.

- **CORE-186** The port of the history of a file shall offer one operation: give the versions of a path in the commits reachable from a commit.
- **CORE-187** The operation that gives the versions of a path shall receive the commit to start from and the path in the repository.
- **CORE-188** The version of a file that the port gives shall carry the commit that changed the path and the bytes of the file in that commit.
- **CORE-189** The port of the history of a file shall give the versions newest first, one for each commit reachable from the start that changes the path, without following a rename and without a commit where the path is absent.
