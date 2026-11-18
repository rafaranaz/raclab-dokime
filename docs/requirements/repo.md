# Requirements of the `repo` scope

Governance gates of the repository itself, run by CI (`tools/`). Each requirement follows an EARS
template and has at least one test that declares it in its `SDD-EARS:` marker.

## Commits (`tools/check_commits.py`)

- **REPO-001** When a commit header does not match `type(scope): description` with a type from the allowed list, the commit check shall reject the commit with a message naming the header.
- **REPO-002** When a commit scope is not a declared scope, the commit check shall reject the commit.
- **REPO-003** When a branch scope is given and a commit scope differs from it, the commit check shall reject the commit.
- **REPO-004** If a commit of type feat, fix, refactor or perf has no body besides trailers, then the commit check shall reject the commit.
- **REPO-005** If a commit header is longer than 72 characters, then the commit check shall reject the commit.
- **REPO-006** If a commit has more than one parent, then the commit check shall reject the commit.

## Branch scope (`tools/check_scope.py`)

- **REPO-010** When a branch name does not match `type/scope-description` with an allowed type and a declared scope, the scope check shall reject the branch.
- **REPO-011** When a changed file matches neither the paths of the branch scope nor the shared paths, the scope check shall reject the change with a message listing each such file.

## History in code (`tools/check_history.py`)

- **REPO-020** When a comment or docstring in a Python file contains a task identifier, a version tag, an ISO date or a history phrase, the history check shall report the file, the line and the matched text.
- **REPO-021** When a comment or docstring in a Python file references a Markdown file that does not exist in the repository, the history check shall report the reference.

## EARS syntax (`tools/check_ears.py`)

- **REPO-030** When a requirement statement does not match one of the EARS templates, the EARS check shall reject the requirement.
- **REPO-031** When a requirement statement contains a term from the vague-terms list, the EARS check shall reject the requirement with a message naming the term.
- **REPO-032** If a requirement statement contains more than one occurrence of `shall`, then the EARS check shall reject the requirement.
- **REPO-033** If a requirement identifier is duplicated or does not start with the prefix of its file, then the EARS check shall reject the file.

## Traceability (`tools/check_traceability.py`)

- **REPO-040** When a requirement is not declared by the marker of any test file, the traceability check shall report the requirement as uncovered.
- **REPO-041** When a test marker declares a requirement identifier that does not exist, the traceability check shall report the marker.
- **REPO-042** If a test file has no marker on its first non-empty line, then the traceability check shall reject the file.

## Links (`tools/check_links.py`)

- **REPO-050** When a relative link in a Markdown file points to a path that does not exist, the link check shall report the file and the link.

## Mermaid diagrams (`tools/check_mermaid.py`)

- **REPO-070** When the Mermaid renderer rejects a Markdown file that contains a Mermaid block, the Mermaid check shall report the file with the error message of the renderer.
- **REPO-071** If the Mermaid renderer cannot be run, then the Mermaid check shall fail with a message naming the renderer.
- **REPO-072** The Mermaid check shall pass Markdown files without Mermaid blocks to no renderer.

## Translations (`tools/check_translations.py`)

- **REPO-060** When a documentation file has no Spanish translation next to it, the translation check shall report the missing translation.
- **REPO-061** When the source hash recorded in a translation differs from the hash of its English source, the translation check shall report the translation as out of date with a message containing the current source hash.
- **REPO-062** If a Spanish translation has no English source next to it or no source header on its first line, then the translation check shall reject the translation.

## Decision records (`tools/check_adrs.py`)

- **REPO-090** When a decision record numbered 0008 or higher has no `Basis` section with text, the decision-record check shall report the record.
- **REPO-091** When a decision record has no row in the index of decision records, the decision-record check shall report the record.
- **REPO-092** When the status of a decision record differs from the status in its index row, the decision-record check shall report both statuses.

## Import contracts (`pyproject.toml`, section `tool.importlinter`)

- **REPO-100** When a module of the package imports a module that the dependency rules of the architecture forbid, the import check shall reject the package.
- **REPO-101** While a module of the architecture does not exist in the package, the import check shall accept the package.
- **REPO-102** The import check shall accept every dependency drawn in the module diagram of the architecture.
- **REPO-103** The import contracts shall name the same modules as the module diagram of the architecture.

## The installed command (`pyproject.toml`, section `project.scripts`)

- **REPO-110** The package shall install a command named `dokime` that runs the command line of the `interfaces` module.

## Pull request descriptions (`tools/clean_pr_body.py`)

- **REPO-080** When a pull request description contains an attribution line added by tooling, the description cleaner shall remove that line together with the separator line directly above it.
- **REPO-081** When a pull request description contains a line that is only a link to a Claude session, the description cleaner shall remove that line.
- **REPO-082** The description cleaner shall leave unchanged every line that is not an attribution line, its separator, a session link or a trailing blank line.

## The gates in one command (`tools/gates.py`)

- **REPO-120** When the gate runner runs, the gate runner shall run every command of the block "Gates locally" of `CLAUDE.md`, in its order, with `<branch>` replaced by the name of the current branch as one argument of the shell.
- **REPO-121** If a command of the block fails, a command inside a pipeline included, then the gate runner shall stop and end with the exit code of that command.
- **REPO-122** When every command of the block passes, the gate runner shall end with the exit code 0.
- **REPO-123** If `CLAUDE.md` has no block "Gates locally", then the gate runner shall end with a non-zero exit code and a message that names the missing block.

## The run of the corpus in CI (`tools/check_corpus.py`)

The job `corpus` of CI runs the self-checks of `tests/corpus` and then this check on their JUnit
report, so that the job cannot pass without self-checking every project
([ADR-0052](../adr/0052-the-corpus-runs-in-ci-in-a-job-of-its-own-with-the-network.md)).

- **REPO-130** When the report of the corpus is checked, the corpus check shall pass only if the report has exactly one self-check for each project of `tests/corpus` and every one of them passed.
- **REPO-131** If a self-check of a project is missing from the report, was skipped, failed or gave an error, then the corpus check shall fail with a line that names the project and what happened.
- **REPO-132** If a self-check failed with a message that starts with `network:`, then the corpus check shall say that the cause was the network.
- **REPO-133** When the report of the corpus is checked, the corpus check shall write the duration of each self-check that ran.
- **REPO-134** If the report of the corpus cannot be read, then the corpus check shall fail with a line that names the report.

## The pack of this repository (`.dokime/`, [ADR-0041](../adr/0041-the-environment-of-a-verified-project-is-a-dockerfile.md))

A4 audits the pull requests of this repository, so dokime has a pack of its own, written by the
same rules as those of the corpus.

- **REPO-140** The pack of this repository at `.dokime/pack.yaml` shall pass the check of packs with no finding.
- **REPO-141** The Dockerfile of this repository shall name its base image by its digest.
- **REPO-142** The Dockerfile of this repository shall install every package with the exact version that `uv.lock` gives it and without resolving dependencies.
- **REPO-143** The Dockerfile of this repository shall put `/dokime/project/src` on `PYTHONPATH`, since the image does not install the project.
- **REPO-144** The pack of this repository shall name as the configuration of its tests the section `tool.pytest.ini_options` of `pyproject.toml` and every `conftest.py`.
- **REPO-145** The Dockerfile of this repository shall install every dependency that `uv.lock` gives the packages it installs, except those whose marker names another system than Linux, since it resolves none of them.
- **REPO-146** The command of the tests of the pack of this repository shall go on past an error in the collection of a module of tests, since otherwise one module that does not import stops every test and the side looks red as a whole.
