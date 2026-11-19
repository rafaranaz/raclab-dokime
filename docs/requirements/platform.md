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

## The commit of the harness ([ADR-0068](../adr/0068-the-harness-is-named-by-its-version-and-its-commit.md))

The evidence names the code of the harness by its version and its commit. The commit names the
code only when the checkout that runs it has no change, so a checkout with changes has no commit to
give.

- **PLATFORM-080** When it is asked the commit of the checkout that holds a directory, the platform shall give the commit of its `HEAD`.
- **PLATFORM-081** If the directory is not in a checkout of git, has no commit yet, or git cannot be found, then the platform shall give no commit.
- **PLATFORM-082** If the checkout has a change to a file that git follows, or a file that it does not follow and does not ignore, then the platform shall give no commit, since the commit would not name the code that runs.
- **PLATFORM-083** When it reads the commit of a checkout, the platform shall run no program that the configuration of git at any level, the hooks of the checkout or its attributes name, such as a filter that cleans a file to compare it.
- **PLATFORM-084** If the checkout follows no file under the directory, then the platform shall give no commit, since the directory is not part of the code of that checkout, as one inside an ignored environment of another project is not.

## The sealed store ([ADR-0072](../adr/0072-the-sealed-store-is-encrypted-with-age-for-a-list-of-recipients.md), [ADR-0073](../adr/0073-the-key-of-the-hold-out-lives-outside-ci-until-b4.md))

The adapter of the port `SealedStore` of `core`, with pyrage. It encrypts with age for the X25519
recipients given, which the caller reads from the base, and opens with one identity, an age file
encrypted with a passphrase. The content is decrypted only in memory.

- **PLATFORM-090** When a content is sealed for a list of recipients, the sealed store shall encrypt it with age so that the identity of any one of them opens it.
- **PLATFORM-091** If the list of recipients given to seal is empty or holds a text that is not an X25519 recipient of age, then the sealed store shall refuse to seal, with the code `bad-recipient`.
- **PLATFORM-092** When sealed bytes are opened, the sealed store shall decrypt them with its identity and give the content, without writing a file.
- **PLATFORM-093** If the identity of the sealed store is not a recipient of the sealed bytes, then the sealed store shall refuse to open them, with the code `not-a-recipient`.
- **PLATFORM-094** If the sealed bytes are not a file of age, then the sealed store shall refuse to open them, with the code `unreadable-batch`.
- **PLATFORM-095** The sealed store shall write sealed bytes that the binary `age` opens with the file of an identity that the platform created and its passphrase.
- **PLATFORM-096** When a content is sealed without an identity, the platform shall encrypt it for the recipients as the sealed store does, since sealing needs only the public keys of the recipients.

### The identity

- **PLATFORM-100** When an identity is created at a path with a passphrase, the platform shall write a new X25519 identity of age, encrypted with the passphrase in the format of age, and give its recipient.
- **PLATFORM-101** When the platform creates the file of an identity, the platform shall create it with the permissions 0600, and the directories it lacks with 0700.
- **PLATFORM-102** If a file exists at the path of an identity to create, then the platform shall refuse to create it, with the code `identity-exists`, and leave the file as it was.
- **PLATFORM-103** If the passphrase of an identity to create is empty, then the platform shall refuse to create it, with the code `empty-passphrase`.
- **PLATFORM-104** When an identity is loaded with its passphrase, the platform shall decrypt it in memory and give the sealed store that opens with it.
- **PLATFORM-105** If the passphrase does not open the file of an identity, then the platform shall refuse to load it, with the code `wrong-passphrase`.
- **PLATFORM-106** If the file of an identity can be read or written by its group or by others, then the platform shall load it with a finding `open-identity` of the verdict `ASK` that names its permissions.
- **PLATFORM-107** If there is no file at the path of an identity to load, then the platform shall refuse to load it, with the code `no-identity`.
- **PLATFORM-108** The default path of the identity shall be `dokime/identity.age` under `$XDG_DATA_HOME` when it is an absolute path, or under `$HOME/.local/share` otherwise, since the specification of XDG holds a relative path in those variables invalid.
- **PLATFORM-109** If the file of an identity opens with its passphrase but does not hold exactly one secret key of age, then the platform shall refuse to load it, with the code `bad-identity`.
- **PLATFORM-113** If neither `XDG_DATA_HOME` nor `HOME` is an absolute path, then the platform shall refuse to give the default path of the identity, with the code `no-home`, instead of a path relative to the working directory.

### The passphrase

The passphrase comes only from a descriptor that the caller names or from the terminal of the
process, never from a variable of the environment, an argument, a file read by its path or the
ledger.

- **PLATFORM-110** When a descriptor of the passphrase is given, the platform shall read the passphrase from it up to its first newline, without the newline.
- **PLATFORM-111** When no descriptor is given, the platform shall read the passphrase from the terminal of the process, `/dev/tty`, with its echo turned off and turned on again after.
- **PLATFORM-112** If no descriptor is given and the process has no terminal, then the platform shall refuse to read a passphrase, with the code `no-passphrase-source`, without reading from another source.
- **PLATFORM-114** If the passphrase read is not valid UTF-8, then the platform shall refuse it, with the code `unreadable-passphrase`.

## The randomness of the system

The seed of a split, the salts of the held-out examples and the canary come from the randomness of
the system, never from a value that a person chooses (ADR-0014).

- **PLATFORM-120** When it is asked for a number of random bytes, the platform shall give that many bytes from the randomness of the system.
- **PLATFORM-121** When it is asked for a seed, the platform shall give a natural integer of 53 random bits from the randomness of the system, the largest that the canonical form of ADR-0062 holds, since the seed is written in the sealed batch.
- **PLATFORM-122** If it is asked for a number of random bytes below 1, then the platform shall refuse with an error that names the number.

## The versions of a file in the history ([ADR-0014](../adr/0014-hidden-checks-are-held-out-approved-examples.md))

To find a held-out example that was once in clear, the audit reads every version of the contract of
a story in the history that its commit reaches. The whole history is walked, without the simplification
that git applies by default, which follows only one parent of a merge that leaves the file as it
was and so misses a version in clear on a branch that took it back before the merge.

These are limits of the detection, not guarantees: it does not see a version under an earlier path
when the history renamed the file, commits that only other refs reach, nor copies of an example in
other files.

- **PLATFORM-130** When it is asked the versions of a path from a commit, the platform shall give, newest first, each commit of the whole history reachable from it, the branches merged into it included, that changes the path and leaves it as a file, with the bytes of the path in that commit.
- **PLATFORM-131** When it reads the versions of a path, the platform shall run git with the environment of the adapter, with the hooks and the monitor of the file system turned off, the attributes read from the empty tree and the detection of renames turned off.
- **PLATFORM-132** If the directory is not a checkout of git, git cannot be found, or the commit is not a commit of it, then the platform shall refuse to read the versions, with the code `unknown-commit`.
- **PLATFORM-133** When the versions of a path from a commit are asked, the project repository adapter shall give, in the same order, each version that PLATFORM-130 gives, as a version of the port of the history of a file with its commit and its bytes.
