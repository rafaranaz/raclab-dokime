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
