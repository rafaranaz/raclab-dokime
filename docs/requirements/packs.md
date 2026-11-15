# Requirements of the `packs` scope

The pack of a verified project: the data that tells the harness how to build its environment and
how to run its tests. This first increment has what does not depend on a container engine: the
format of a pack and its check, and the rules of the self-check as decisions over results that
something else obtains. Each requirement follows an EARS template and has at least one test that
declares it in its `SDD-EARS:` marker.

The decisions behind these requirements are in
[ADR-0028](../adr/0028-language-support-is-a-declarative-pack-with-levels.md) and
[ADR-0041](../adr/0041-the-environment-of-a-verified-project-is-a-dockerfile.md).

## The check of a pack

- **PACKS-001** When a pack is checked, the checker shall report every finding of the strict reader.
- **PACKS-002** If the strict reader gives no value, then the checker shall report the findings of the reader and no other.
- **PACKS-003** The checker shall report every finding of a pack in one result, in the order of their lines.
- **PACKS-004** When a pack has no finding, the checker shall return the pack.
- **PACKS-005** If a pack has a finding, then the checker shall return no pack.

## Shape

- **PACKS-010** If the pack is not a mapping, then the checker shall report a finding with the code `wrong-type` and run no other check.
- **PACKS-011** If a mapping of a pack does not fit the table of fields, then the checker shall report for it the findings of the shape check of `core`.
- **PACKS-012** If the list of the test command or the list of the test paths has no item, then the checker shall report a finding with the code `empty-list`, with its line.
- **PACKS-013** If the path of the Dockerfile is absolute or goes above the directory of the pack, then the checker shall report a finding with the code `path-outside-pack`, with its line.
- **PACKS-014** If the path of the report is absolute or goes above the output directory, then the checker shall report a finding with the code `path-outside-output`, with its line.
- **PACKS-015** If a pattern of the test paths is absolute or goes above the project, then the checker shall report a finding with the code `path-outside-project`, with its line.

## Which files are tests

- **PACKS-020** When a path of the project matches a pattern of the test paths, the pack shall count that path as a test.
- **PACKS-021** When a path of the project matches no pattern of the test paths, the pack shall count that path as code that is not a test.

## The rules of the self-check

A candidate is a commit that may prove the pack. Its tests are run on its parent and on the commit
itself, which gives two reports: for each test, whether it passed, failed, gave an error or was
skipped.

- **PACKS-030** When a commit changes a path that is a test and a path that is not, the rule shall count the commit as a candidate.
- **PACKS-031** When a commit changes only tests or only code that is not a test, the rule shall not count the commit as a candidate.
- **PACKS-032** When a test passes on the commit and fails or gives an error on the parent, the rule shall count the commit as a witness.
- **PACKS-033** When a test passes on the commit and is missing from the report of the parent, and that report has a test that fails or gives an error, the rule shall count the commit as a witness.
- **PACKS-034** If the report of the parent has no test that fails or gives an error, then the rule shall not count the commit as a witness.
- **PACKS-035** When at least two of the first ten candidates are witnesses, the self-check shall give no finding.
- **PACKS-036** If fewer than two of the first ten candidates are witnesses, then the self-check shall report a finding with the code `too-few-witnesses` that says how many candidates and how many witnesses there were.

## The order of the history ([ADR-0044](../adr/0044-the-packs-module-drives-the-self-check-in-an-order-of-its-own.md))

The port of the project repository gives the history from a commit with no order; `packs` orders
it, so that every adapter gives the same candidates.

- **PACKS-040** When the history from a commit is ordered, the order shall place no commit before a commit that descends from it.
- **PACKS-041** When more than one commit can come next, the order shall place first the one with the later commit date.
- **PACKS-042** When commits that can come next have the same commit date, the order shall place first the one that became able to come next earlier, a commit becoming able when every commit that descends from it is placed, and the parents of a commit in the order the commit names them.
- **PACKS-043** When the history is ordered, the order shall leave out every commit that does not have exactly one parent.

## Running the tests of a pack on a directory

The operation that the self-check runs on each side of a candidate, and that `verify` reuses in
milestone A3. The pack and its Dockerfile are read once, from the working copy, and used the same
for every directory: old commits do not have the pack.

- **PACKS-050** When the tests of a pack are run on a directory, the test run shall build the image from the Dockerfile of the pack read from the working copy, with the directory as the context of the build, and ignore any `.dokime/` that the directory holds.
- **PACKS-051** When the tests of a pack are run on a directory, the test run shall run the test command of the pack in the image it built, with the directory as the project and an empty output directory of its own.
- **PACKS-052** When the command ends by itself, whatever its exit code, the test run shall give the report read at the path of the report of the pack.
- **PACKS-053** The test run shall give the digest of the image it built and the base of that image.
- **PACKS-054** The test run shall pass the default limits of a build, of a run and of the reading of a report.
- **PACKS-055** If the build, the run or the reading of the report is refused, then the test run shall give the finding of the refusal, with the verdict `ERROR`.
- **PACKS-056** If the container of the run is killed at the time limit, at the memory limit or for another reason, then the test run shall give a finding with the code `run-killed` and the verdict `ERROR`, naming the cause.

## The loop of the self-check ([ADR-0041](../adr/0041-the-environment-of-a-verified-project-is-a-dockerfile.md), [ADR-0044](../adr/0044-the-packs-module-drives-the-self-check-in-an-order-of-its-own.md))

`packs` drives the self-check over the ports that `interfaces` gives it. A finding with the
verdict `ERROR` ends it, because nothing found later changes that verdict
([ADR-0015](../adr/0015-a-gate-returns-one-of-four-verdicts.md)).

Known limit: the self-check has no limit of time of its own. In the worst case it takes ten
candidates, by two sides, by the 30 minutes of a build and the 15 of a run. The budget of a whole
run belongs to the flow ([ADR-0018](../adr/0018-the-flow-is-a-state-machine-in-a-yaml-file.md)),
in block C.

- **PACKS-060** When a pack is self-checked from a commit, the self-check shall look at the commits in the order of PACKS-040 to PACKS-043 and take as candidates those of PACKS-030.
- **PACKS-061** When a candidate is looked at, the self-check shall run the tests on the tree of the parent with the test paths taken from the commit.
- **PACKS-062** When a candidate is looked at, the self-check shall run the tests on the tree of the commit.
- **PACKS-063** When the second witness is found, the self-check shall look at no further candidate.
- **PACKS-064** When ten candidates have been looked at, the self-check shall look at no further candidate.
- **PACKS-065** If a test run gives a finding with the verdict `ERROR`, then the self-check shall end with that finding and look at no further candidate.
- **PACKS-066** If a port refuses an operation, then the self-check shall end with the finding of the refusal and look at no further candidate.
- **PACKS-067** When the history ends before ten candidates, the self-check shall decide with the candidates it looked at.

## What the self-check records

- **PACKS-070** When a candidate has been looked at, the result shall record the commit, the digest of each of its two trees, the digest and the base of each of its two images, and whether it is a witness.
- **PACKS-071** When a candidate is a witness, the result shall record the names of the tests that pass on the commit and failed, gave an error or were missing on the parent.
- **PACKS-072** The result shall record once the path and the version of each program that the caller says runs a port.

## The directories of each side

- **PACKS-080** When a side of a candidate has run, the self-check shall remove the directory of its tree and its output directory.
- **PACKS-081** If the harness receives SIGINT or SIGTERM while a side runs, then the self-check shall remove the directories of that side and let the interruption go on.

## Table of fields

A name is a text of letters, digits and hyphens that starts with a letter. A relative path does not
start with `/` and has no `..` part.

| Mapping | Field | Mandatory | Holds |
|---|---|---|---|
| Pack | `format` | Yes | The number 1 |
| Pack | `name` | Yes | A name |
| Pack | `environment` | Yes | A mapping |
| Pack | `tests` | Yes | A mapping |
| Environment | `dockerfile` | Yes | A relative path, from the directory of the pack |
| Tests | `command` | Yes | A list of texts, not empty: the command and its arguments |
| Tests | `report` | Yes | A relative path, from the output directory: the report in JUnit XML |
| Tests | `paths` | Yes | A list of patterns, not empty, where `*` stays inside a part of the path and `**` crosses parts |
