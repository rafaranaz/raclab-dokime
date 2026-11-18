# platform

Adapters of the outside world that do not run code of others. It imports only `core`, and only
`interfaces` imports it. This increment has the adapter of the project repository that runs the
`git` command; its requirements are in [platform.md](../../../docs/requirements/platform.md).

## The git adapter

```python
from dokime.platform.git import GitRepository

with GitRepository(project) as repository:  # refuses git older than 2.41, SHA-256, shallow
    repository.git_path, repository.git_version  # the git that every command runs
    history = repository.history(start)
    change = repository.change(commit)  # the paths against its one parent
    tree = repository.compose_with_paths(change.parent, commit, is_test)
    repository.extract(tree, directory)  # an empty directory, filled byte for byte
```

The adapter reads three facts in the project: that it is a repository, the format of its objects
and whether it is a shallow clone. Everything else runs in a bare repository of its own, in a
temporary directory removed on `close()`, which reads the objects of the project as alternates.
The configuration and the attributes of the project and of the person do not reach it, and the
`.git` of the project is not written. A tree with a submodule is refused, and a composition with a
patch is refused until milestone A3.

## The composition with a patch

`compose_with_patch(base, patch)` applies the patch with `git apply --cached` to an index of the
adapter from the tree of the base, so no working tree and no git directory of the project is
touched. A patch that does not apply is refused with `patch-does-not-apply`, quoting git. Before
applying, the paths that git reads from the patch are checked, and one with a part `.git` in any
case of letters is refused with `patch-touches-git`.
The patch is applied with `core.protectNTFS` and `core.protectHFS` on, so that the names those
file systems take as `.git`, such as `.git.`, `git~1` or `.g` with an ignorable character of HFS
and `it`, are refused by git whatever its defaults.

## The composition over a tree

The adapter implements the port of the audited repository of `core`. `compose_tree_with_paths(tree,
source, take)` replaces, in a tree such as the base with the patch applied, the region that the
rule takes with the files of a commit (ADR-0058). It replaces and does not overlay: a file of the
tree under that region that the commit does not have, such as a `conftest.py` that the patch added,
is not in the result.

## The ledger store of a file and the system clock

`LedgerFile(path)` implements the port of the ledger store of `core` over one file of the state
directory of the harness: one event per line, each ended by a newline, written in append mode until
every byte of the line is written, and flushed to the storage device before `append` returns, with
its directory when the file is new. It refuses a line with a newline or a carriage return, and
appending after a last line that was cut. A file that does not exist has no lines and is created by
the first append. `SystemClock` implements the port of the clock with the time of the system in UTC.

```python
from dokime.core.ledger import Ledger
from dokime.platform.clock import SystemClock
from dokime.platform.ledger_file import LedgerFile

ledger = Ledger(LedgerFile(state / "ledger.jsonl"), SystemClock())
ledger.record("run.started", {})
```

## The commit of the harness

`checkout_commit(directory)` gives the commit of `HEAD` of the checkout of git that holds the
directory, which `interfaces` asks for the directory of the harness, so that the evidence names it
by its version and its commit (ADR-0068). It gives none when the directory is not in a checkout,
the checkout follows no file under it (a harness installed in an ignored environment of another
project), the checkout has no commit, git is not found, or the checkout has a change to a file git
follows or a file it neither follows nor ignores: the commit would not name the code that runs. git
runs with the environment of the adapter, with `core.fsmonitor` and the hooks turned off, and with
`GIT_ATTR_SOURCE` on the empty tree, so that no program that the configuration, the hooks or the
attributes name runs, not even a filter that cleans a file to compare it (PLATFORM-083).
