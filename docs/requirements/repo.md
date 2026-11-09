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

## Translations (`tools/check_translations.py`)

- **REPO-060** When a documentation file has no Spanish translation next to it, the translation check shall report the missing translation.
- **REPO-061** When the source hash recorded in a translation differs from the hash of its English source, the translation check shall report the translation as out of date with a message containing the current source hash.
- **REPO-062** If a Spanish translation has no English source next to it or no source header on its first line, then the translation check shall reject the translation.
