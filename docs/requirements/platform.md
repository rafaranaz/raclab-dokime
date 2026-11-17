# Requirements of the `platform` scope

The adapters of the outside world that do not run code of others: the project repository, the
ledger store and the clock, and later the signer, the other stores, the forge and randomness. The
adapter of the project repository runs the `git` command. Each requirement follows an EARS
template and has at least one test that declares it in its `SDD-EARS:` marker.

## The git adapter of the project repository ([ADR-0042](../adr/0042-a-port-of-the-project-repository-composes-the-trees-that-are-built.md), [ADR-0044](../adr/0044-the-packs-module-drives-the-self-check-in-an-order-of-its-own.md))

The adapter implements the port of `core`. It is opened on a project. It reads three facts in the
project: that it is a repository, the format of its objects and whether it is a shallow clone. For
everything else it keeps a git repository of its own in a temporary directory, which reads the
objects of the project as alternates, holds the objects the adapter writes and shares no
reference with the project. It runs every other command of git there, so that neither the
configuration nor the attributes of the project, nor those of the person, change what it composes
or extracts. The temporary directory lasts one opening and is removed when the adapter is closed;
keeping it from one run to the next would be a requirement of its own. A refusal is raised as the
refusal of the port, with the code given here.

Known limits: a file kept in Git LFS is extracted as its pointer; on a file system that does not
tell upper from lower case, a tree with two paths that differ only in case is not extracted
faithfully.

### Opening

- **PLATFORM-001** If the git command is not found as an executable program, then the git adapter shall refuse with the code `git-not-found`.
- **PLATFORM-002** If the version of git is older than 2.41, or the adapter cannot read it, then the git adapter shall refuse with the code `git-too-old`, quoting the version git gave.
- **PLATFORM-003** If the project is not a git repository, then the git adapter shall refuse with the code `not-a-repository`.
- **PLATFORM-004** If the project names its objects with SHA-256, then the git adapter shall refuse with the code `sha256-repository`.
- **PLATFORM-005** If the project is a shallow clone, then the git adapter shall refuse with the code `shallow-clone`.
- **PLATFORM-006** When the git adapter opens, the git adapter shall resolve the git command to an absolute path once and run that path for every command of git.
- **PLATFORM-007** The git adapter shall give the absolute path and the version of the git it runs.

### What the adapter reads and writes

- **PLATFORM-010** The git adapter shall leave every file under the git directory of the project unchanged.
- **PLATFORM-011** The git adapter shall write the objects it creates in a temporary directory of its own.
- **PLATFORM-012** The git adapter shall run git with no variable of the environment whose name starts with `GIT_` other than those it sets itself.
- **PLATFORM-013** The git adapter shall run git without the global and the system configuration of git.
- **PLATFORM-014** The git adapter shall ignore the replace objects of the project.
- **PLATFORM-015** If git ends with an error that no other requirement names, then the git adapter shall refuse with the code `git-failed`, quoting what git wrote on its error output.
- **PLATFORM-016** When the git adapter is closed, the git adapter shall remove its temporary directory.
- **PLATFORM-017** If the opening of the git adapter is refused, then the git adapter shall leave no temporary directory.
- **PLATFORM-047** The git adapter shall run no program that the configuration of git at any level, the hooks of the project or the attributes of the trees it reads name.

### History and change

- **PLATFORM-020** When the history from a commit is asked, the project repository adapter shall give every commit reachable from it, once each.
- **PLATFORM-021** When the history from a commit is asked, the project repository adapter shall give the committer date of each commit.
- **PLATFORM-022** When the history from a commit is asked, the project repository adapter shall give the parents of each commit in the order the commit names them.
- **PLATFORM-023** If a name given as a commit is not a commit of the project, then the project repository adapter shall refuse with the code `unknown-commit`, naming it.
- **PLATFORM-024** When the change of a commit is asked, the project repository adapter shall give every path whose file differs between the commit and its parent, the deleted and the added ones included.
- **PLATFORM-025** When the change of a commit that renames a file is asked, the project repository adapter shall give both the old and the new path.
- **PLATFORM-026** If the commit whose change is asked does not have exactly one parent, then the project repository adapter shall refuse with the code `not-one-parent`, naming the commit.
- **PLATFORM-027** If a path that the adapter reads is not valid UTF-8, then the project repository adapter shall refuse with the code `path-not-utf8`, quoting its bytes.

### Composition

- **PLATFORM-030** When a tree is composed from a base with the paths of a source, the project repository adapter shall give a tree that holds, under the paths the rule takes, exactly the files of the source with their modes.
- **PLATFORM-031** When a tree is composed from a base with the paths of a source, the project repository adapter shall keep every file of the base whose path the rule does not take.
- **PLATFORM-032** When a tree is composed from a base with a patch, the project repository adapter shall give the tree of the base with the patch applied, each file it touches with the bytes and the mode the patch gives it.
- **PLATFORM-033** When a tree is composed from a base with a patch, the project repository adapter shall keep every file of the base that the patch does not touch.
- **PLATFORM-034** If the patch does not apply to the base, then the project repository adapter shall refuse with the code `patch-does-not-apply`, quoting what git wrote.
- **PLATFORM-035** If a path that the patch names has a part that is `.git` in any case of letters, then the project repository adapter shall refuse with the code `patch-touches-git`, naming the path, before it applies anything.
- **PLATFORM-036** The project repository adapter shall apply a patch with the protections of git for NTFS and for HFS turned on, whatever the defaults of the git it runs.
- **PLATFORM-037** When a tree is composed with the paths of a commit, the project repository adapter shall give a tree that holds, under the paths the rule takes, exactly the files of the commit with their modes, and no file of the tree.
- **PLATFORM-038** When a tree is composed with the paths of a commit, the project repository adapter shall keep every file of the tree whose path the rule does not take.
- **PLATFORM-039** If a name given as the tree to compose is not a tree that the adapter can read, then the project repository adapter shall refuse with the code `unknown-tree`, naming it.

### Extraction

- **PLATFORM-040** When a tree is extracted, the project repository adapter shall write each file of the tree with the bytes of its blob, whatever the attributes and the configuration of the project and of the person.
- **PLATFORM-041** When a tree is extracted, the project repository adapter shall write each executable file of the tree as executable.
- **PLATFORM-042** When a tree is extracted, the project repository adapter shall write each symbolic link of the tree as a symbolic link with the target its blob holds.
- **PLATFORM-043** When a tree is extracted, the project repository adapter shall write in the directory nothing that is not in the tree.
- **PLATFORM-044** If the tree to extract holds a submodule, then the project repository adapter shall refuse with the code `submodule-in-tree`, naming its path, before writing anything.
- **PLATFORM-045** If a name given as a tree is not a tree that the adapter can read, then the project repository adapter shall refuse with the code `unknown-tree`, naming it.
- **PLATFORM-046** If the directory to extract into is not an empty directory, then the project repository adapter shall reject it with an error that names the directory.

## The ledger store of a file ([ADR-0023](../adr/0023-evidence-is-an-attestation-bound-to-the-tree.md))

The adapter implements the port of the ledger store of `core` over one file, whose path the caller
gives: the state directory of the harness, outside the working tree of the project. A line is one
event of the ledger, which its canonical form keeps on one line.

- **PLATFORM-060** When a line is appended, the file ledger store shall add the line and a newline at the end of its file.
- **PLATFORM-061** When its lines are asked for, the file ledger store shall give the lines of its file in the order they were appended, without their newlines.
- **PLATFORM-062** While its file does not exist, the file ledger store shall give no lines.
- **PLATFORM-063** When a line is appended and its file does not exist, the file ledger store shall create the file.
- **PLATFORM-064** If a line holds a newline or a carriage return, then the file ledger store shall refuse it with an error and write nothing.
- **PLATFORM-065** If its file is not empty and does not end with a newline, then the file ledger store shall refuse to append, with an error that says its last line is cut.
- **PLATFORM-066** If its file is not valid UTF-8, then the file ledger store shall refuse to give its lines, with an error that names the file.
- **PLATFORM-067** If the system writes fewer bytes of a line than it was given, then the file ledger store shall write the rest until the line is complete, or refuse with an error when the system writes none.
- **PLATFORM-068** When the file ledger store creates its file, the file ledger store shall flush the directory that holds it to the storage device.

## The system clock

- **PLATFORM-070** The system clock shall give the current time of the system, in UTC.
